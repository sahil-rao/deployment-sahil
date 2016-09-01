from __future__ import absolute_import

from .base import HealthCheck, HealthCheckList
# from .disk import DiskUsageCheck
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
        if hasattr(self, 'mconn') and self.mconn:
            self.mconn.close()

        return super(Mongo, self).close()

    def mongo_version(self):
        if self.mconn is None:
            return None

        return self.mconn.server_info()['version']

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

    def is_replica(self):
        return self.current_repl_status.get('state') == 2

    def is_arbiter(self):
        return self.current_repl_status.get('state') == 7

    def members(self):
        primaries = []
        secondaries = []
        arbiters = []
        others = []

        for member in self.repl_status.get('members', []):
            name = member['name']

            if member['state'] == 1:
                primaries.append(name)
            elif member['state'] == 2:
                secondaries.append(name)
            elif member['state'] == 7:
                arbiters.append(name)
            else:
                others.append(name)

        return (
            sorted(primaries),
            sorted(secondaries),
            sorted(arbiters),
            sorted(others),
        )

    def member_states(self):
        num_primaries = 0
        num_secondaries = 0
        num_arbiters = 0
        num_otherstate = 0

        for member in self.repl_status.get('members', []):
            if member['state'] == 1:
                num_primaries += 1
            elif member['state'] == 2:
                num_secondaries += 1
            elif member['state'] == 7:
                num_secondaries += 1
            else:
                num_otherstate += 1

        return num_primaries, num_secondaries, num_arbiters, num_otherstate

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


class MongoVersionCheck(MongoHealthCheck):
    description = "Mongo versions match"

    def check_mongo_host(self, host):
        version = host.mongo_version()

        self.host_msgs[host] = 'version: {}'.format(version)

        return version and \
            self.all_equal(host.mongo_version() for host in self.hosts)


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


class MongoClusterConfigurationCheck(MongoHealthCheck):
    def __init__(self, *args, **kwargs):
        super(MongoClusterConfigurationCheck, self).__init__(*args, **kwargs)

        self.description = \
            "Mongo instance's replica set view has one " \
            "primary and {} secondaries + arbiters".format(
                len(self.hosts) - 1)

    def execute(self, *args, **kwargs):
        result = super(MongoClusterConfigurationCheck, self).execute(
            *args,
            **kwargs)

        return \
            self.all_equal(host.members() for host in self.hosts) and \
            result

    def check_mongo_host(self, host):
        primaries, secondaries, arbiters, others = host.members()
        self.host_msgs[host] = 'P: {} S: {} A: {} O: {}'.format(
            ','.join(sorted(primaries)),
            ','.join(sorted(secondaries)),
            ','.join(sorted(arbiters)),
            ','.join(sorted(others)))

        if len(primaries) + len(secondaries) + len(arbiters) != \
                len(self.hosts):
            return False

        for h in self.hosts:
            if h == host:
                continue

            if (primaries, secondaries, arbiters, others) != h.members():
                return False

        return True


class MongoClusterConfigVersionsCheck(MongoHealthCheck):
    description = "Config version of all replica set members match"

    def execute(self, *args, **kwargs):
        result = super(MongoClusterConfigVersionsCheck, self).execute(
            *args,
            **kwargs)

        return \
            self.all_equal(host.config_versions() for host in self.hosts) and \
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
        # Arbiters don't have replica delays.
        if host.is_arbiter():
            self.host_msgs[host] = 'arbiter'
            return True

        try:
            current_optime = host.current_repl_status['optimeDate']
        except KeyError:
            self.host_msgs[host] = 'current missing optime'
            return False

        try:
            primary_optime = host.primary_repl_status['optimeDate']
        except KeyError:
            self.host_msgs[host] = 'primary missing optime'
            return False

        lag = (primary_optime - current_optime).total_seconds()

        self.host_msgs[host] = 'lag: {}'.format(lag)

        return abs(lag) < 10.0


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
        mongodb_servers = pool.map(
            functools.partial(_create_mongo, bastion, 27017),
            mongodb_hostnames)
    finally:
        pool.close()
        pool.join()

    for health_check in (
            MongoVersionCheck(mongodb_servers),
            MongoClusterAgreeOnMasterCheck(mongodb_servers),
            MongoClusterConfigurationCheck(mongodb_servers),
            MongoClusterConfigVersionsCheck(mongodb_servers),
            MongoClusterHeartbeatCheck(mongodb_servers),
            MongoReplicaDelayCheck(mongodb_servers),
            # DiskUsageCheck(bastion, mongodb_hostnames),
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

    values = [
        '{}-{}-mongo'.format(cluster, dbsilo),
        '{}-{}-mongo-*'.format(cluster, dbsilo),
    ]

    if cluster in ('alpha', 'app'):
        values.extend([
            'MongoDB {} {}'.format(
                alpha_names[cluster],
                alpha_names[dbsilo]),
            'MONGO_{}_{}'.format(
                app_names[cluster],
                app_names[dbsilo]),
            'MONGO_{}_{} - Arbiter'.format(
                app_names[cluster],
                app_names[dbsilo]),
        ])

    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(Filters=[
        {
            'Name': 'tag:Name',
            'Values': values,
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
