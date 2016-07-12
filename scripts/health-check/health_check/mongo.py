from __future__ import absolute_import

from .base import HealthCheck, HealthCheckList
from .disk import DiskUsageCheck
from .tunnel import Tunnel
import boto3
import datetime
import functools
import multiprocessing.pool
import pymongo
import sys
import termcolor


class Mongo(Tunnel):
    def __init__(self, bastion, host, port):
        super(Mongo, self).__init__(bastion, host, port)

        if self.tunnel:
            self.mconn = pymongo.MongoClient(
                port=self.tunnel.local_bind_port,
                socketTimeoutMS=10000,
                connectTimeoutMS=10000,
                serverSelectionTimeoutMS=10000,
            )
        else:
            self.mconn = None

    def close(self):
        if self.mconn:
            self.mconn.close()

        return super(Mongo, self).close()

    def server_status(self):
        if self.mconn is None:
            return {}

        if not hasattr(self, '_server_status'):
            try:
                self._server_status = self.mconn.admin.command('serverStatus')
            except pymongo.errors.PyMongoError:
                self._server_status = {}

        return self._server_status

    @property
    def repl_status(self):
        if self.mconn is None:
            return {}

        if not hasattr(self, '_repl_status'):
            try:
                self._repl_status = self.mconn.admin.command('replSetGetStatus')
            except pymongo.errors.PyMongoError:
                self._repl_status = {}

        return self._repl_status

    @property
    def primary_repl_status(self):
        for member in self.repl_status.get('members', []):
            if member['state'] == 1:
                return member

        return {}

    @property
    def current_repl_status(self):
        for member in self.repl_status.get('members', []):
            if member.get('self'):
                return member

        return {}

    def is_master(self):
        return self.current_repl_status.get('state') == 1

    def members(self):
        primaries = []
        secondaries = []
        others = []

        for member in self.repl_status.get('members', []):
            name = member['name']

            if member['state'] == 1:
                primaries.append(name)
            elif member['state'] == 2:
                secondaries.append(name)
            else:
                others.append(name)

        return sorted(primaries), sorted(secondaries), sorted(others)

    def member_states(self):
        num_primaries = 0
        num_secondaries = 0
        num_otherstate = 0

        for member in self.repl_status.get('members', []):
            if member['state'] == 1:
                num_primaries += 1
            elif member['state'] == 2:
                num_secondaries += 1
            else:
                num_otherstate += 1

        return num_primaries, num_secondaries, num_otherstate

    def config_versions(self):
        config_versions = set()
        for member in self.repl_status.get('members', []):
            try:
                config_versions.add(member['configVersion'])
            except KeyError:
                pass

        return config_versions


class MongoHealthCheck(HealthCheck):
    def close(self):
        for host in self.hosts:
            host.close()

    def check_host(self, host):
        if not host.mconn:
            self.host_msgs[host] = 'cannot connect to MongoDB'
            return False

        return self.check_mongo_host(host)

    def check_mongo_host(self, host):
        raise NotImplementedError

    def _all_equal(self, items):
        # Make sure everyone agrees on the count
        initial = None
        for item in items:
            if initial is None:
                initial = item
            elif initial != item:
                return False

        return True


class MongoClusterAgreeOnMasterCheck(MongoHealthCheck):
    description = "Mongo nodes agree on the same master"

    def check_mongo_host(self, host):
        if host.is_master():
            self.host_msgs[host] = '(current primary)'
            return True

        primary = host.primary_repl_status.get('name')
        if primary is None:
            self.host_msgs[host] = 'no primary?'
            return False

        self.host_msgs[host] = 'primary: {}'.format(primary)

        for h in self.hosts:
            if primary != h.primary_repl_status.get('name'):
                return False

        return True


class MongoSameReplicasCheck(MongoHealthCheck):

    description = "Mongo machines have the same replicas"

    def check_mongo_host(self, host):
        primaries, secondaries, others = host.members()
        self.host_msgs[host] = 'P: {} S: {} O: {}'.format(
            ','.join(sorted(primaries)),
            ','.join(sorted(secondaries)),
            ','.join(sorted(others)))

        initial = None
        for h in self.hosts:
            if h == host:
                continue

            if (primaries, secondaries, others) != h.members():
                return False

        return True


class MongoClusterConfigurationCheck(MongoHealthCheck):
    def __init__(self, *args, **kwargs):
        super(MongoClusterConfigurationCheck, self).__init__(*args, **kwargs)

        self.description = \
            "Mongo instance's replica set view has one " \
            "primary and {} secondaries and arbiters".format(
                len(self.hosts) - 1)

    def execute(self, *args, **kwargs):
        result = super(MongoClusterConfigurationCheck, self).execute(
            *args,
            **kwargs)

        return \
            self._all_equal(host.member_states() for host in self.hosts) and \
            result

    def check_mongo_host(self, host):
        num_primaries, num_secondaries, num_otherstate = host.member_states()

        self.host_msgs[host] = 'primaries: {} secondaries: {} other: {}'.format(
            num_primaries,
            num_secondaries,
            num_otherstate)

        return \
            num_primaries == 1 and \
            (num_secondaries + num_otherstate) == len(self.hosts) - 1


class MongoClusterConfigVersionsCheck(MongoHealthCheck):
    description = "Config version of all replica set members match"

    def execute(self, *args, **kwargs):
        result = super(MongoClusterConfigVersionsCheck, self).execute(
            *args,
            **kwargs)

        return \
            self._all_equal(host.config_versions() for host in self.hosts) and \
            result

    def check_mongo_host(self, host):
        config_versions = host.config_versions()

        self.host_msgs[host] = 'versions: {}'.format(sorted(config_versions))

        return len(config_versions) <= 1


class MongoClusterHeartbeatCheck(MongoHealthCheck):
    description = "Last heartbeat received is recent"

    def check_mongo_host(self, host):
        now = datetime.datetime.now()
        heartbeats = []
        for member in host.repl_status.get('members', []):
            # Ignore ourselves
            if member.get('self'):
                continue

            heartbeats.append((now - member['lastHeartbeat']).seconds)

        self.host_msgs[host] = 'heartbeats: {}'.format(heartbeats)

        return any(heartbeat < 65000 for heartbeat in heartbeats)

class MongoReplicaDelayCheck(MongoHealthCheck):
    description = "Check replicas are not behind master"

    def check_mongo_host(self, host):
        primary_repl_status = host.primary_repl_status
        repl_status = host.current_repl_status

        try:
            lag = primary_repl_status['optimeDate'] - repl_status['optimeDate']
        except KeyError:
            return False

        lag = max(0, lag.seconds)

        self.host_msgs[host] = 'lag: {}'.format(lag)

        return lag < 10000


def check_mongodb(bastion, cluster, region, dbsilo):
    mongodb_checklist = HealthCheckList("MongoDB Cluster Health Checklist")
    mongodb_hostnames = _get_mongodb_hostnames(cluster, region, dbsilo)

    if not mongodb_hostnames:
        print >> sys.stderr, \
            termcolor.colored('WARNING:', 'yellow'), \
            'no mongo servers found in', cluster, region, dbsilo
        return mongodb_checklist

    pool = multiprocessing.pool.ThreadPool(5)
    try:
        mongodb_servers = map(
            functools.partial(_create_mongo, bastion, 27017),
            mongodb_hostnames)
    finally:
        pool.close()
        pool.join()

    for health_check in (
            MongoClusterAgreeOnMasterCheck(mongodb_servers),
            MongoSameReplicasCheck(mongodb_servers),
            MongoClusterConfigurationCheck(mongodb_servers),
            MongoClusterConfigVersionsCheck(mongodb_servers),
            MongoClusterHeartbeatCheck(mongodb_servers),
            MongoReplicaDelayCheck(mongodb_servers),
            DiskUsageCheck(bastion, mongodb_hostnames),
            ):
        mongodb_checklist.add_check(health_check)

    return mongodb_checklist


def _get_mongodb_hostnames(cluster, region, dbsilo):
    alpha_names = {
        'alpha': 'Alpha',
        'app': 'App',
        'dbsilo1': 'DBSilo1',
        'dbsilo2': 'DBSilo2',
        'dbsilo3': 'DBSilo3',
        'dbsilo4': 'DBSilo4',
    }

    app_names = {
        'alpha': 'ALPHA',
        'app': 'APP',
        'dbsilo1': 'DBSILO1',
        'dbsilo2': 'DBSILO2',
        'dbsilo3': 'DBSILO3',
        'dbsilo4': 'DBSILO4',
    }

    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'MongoDB {} {}'.format(
                    alpha_names[cluster],
                    alpha_names[dbsilo]),
                'MONGO_{}_{}'.format(
                    app_names[cluster],
                    app_names[dbsilo]),
                'MONGO_{}_{} - Arbiter'.format(
                    app_names[cluster],
                    app_names[dbsilo]),
                '{}-{}-mongo-green'.format(cluster, dbsilo),
                '{}-{}-mongo-blue'.format(cluster, dbsilo),
                '{}-{}-mongo-green-*'.format(cluster, dbsilo),
                '{}-{}-mongo-blue-*'.format(cluster, dbsilo),
            ],
        },
    ])

    hostnames = []
    for instance in instances:
        if instance.private_ip_address:
            hostnames.append(instance.private_ip_address)

    hostnames.sort()

    return hostnames


def _create_mongo(bastion, port, host):
    return Mongo(bastion, host, port)
