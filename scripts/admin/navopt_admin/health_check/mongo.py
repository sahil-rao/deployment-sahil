from __future__ import absolute_import

from .aws import AWSNameHealthCheck
from .base import HealthCheck, HealthCheckList
import boto3
import datetime
import pipes
import re
import sys
import termcolor


class MongoHealthCheck(HealthCheck):
    def close(self):
        for host in self.hosts:
            host.close()

    def check_host(self, host):
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

    def __init__(self, dbsilo, *args, **kwargs):
        super(MongoClusterAgreeOnMasterCheck, self).__init__(*args, **kwargs)

        self.dbsilo = dbsilo

    def check_mongo_host(self, host):
        if host.is_master():
            self.host_msgs[host] = '(current primary)'
            return self.check_master_hostname(host)

        primary = host.primary_repl_status.get('name')
        if primary is None:
            self.host_msgs[host] = 'no primary?'
            return False

        self.host_msgs[host] = 'primary: {}'.format(primary)

        for h in self.hosts:
            if primary != h.primary_repl_status.get('name'):
                return False

        return True

    def check_master_hostname(self, host):
        master_hostname = self.dbsilo.mongo_master_hostname()
        command = 'host {}'.format(pipes.quote(master_hostname))
        stdout = self.dbsilo.cluster.bastion.check_output(command).strip()

        m = re.match('.* has address (.*)$', stdout)
        if not m:
            self.host_msgs[host] += ' failed to parse: ' + stdout
            return False

        found_host = m.group(1)
        if host.host != found_host:
            self.host_msgs[host] += ' master is on {}'.format(found_host)
            return False
        else:
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
        now = datetime.datetime.utcnow()
        heartbeats = []
        for member in host.repl_status.get('members', []):
            # Ignore ourselves
            if member.get('self'):
                continue

            heartbeats.append(
                abs((now - member['lastHeartbeat']).total_seconds())
            )

        self.host_msgs[host] = 'heartbeats: {}'.format(heartbeats)

        return any(heartbeat < 10.0 for heartbeat in heartbeats)


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


def check_mongodb(dbsilo):
    mongodb_checklist = HealthCheckList("MongoDB Cluster Health Checklist")

    mongodb_instances = list(dbsilo.mongo_instances())
    mongodb_servers = list(dbsilo.mongo_clients())

    if not mongodb_servers:
        print >> sys.stderr, \
            termcolor.colored('WARNING:', 'yellow'), \
            'no mongodb servers found in', dbsilo
        return mongodb_checklist

    for health_check in (
            AWSNameHealthCheck(mongodb_instances),

            MongoVersionCheck(mongodb_servers),
            MongoClusterAgreeOnMasterCheck(dbsilo, mongodb_servers),
            MongoClusterConfigurationCheck(mongodb_servers),
            MongoClusterConfigVersionsCheck(mongodb_servers),
            MongoClusterHeartbeatCheck(mongodb_servers),
            MongoReplicaDelayCheck(mongodb_servers),
            ):
        mongodb_checklist.add_check(health_check)

    return mongodb_checklist


def _get_mongodb_instances(cluster, region, dbsilo):
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
    instances = list(ec2.instances.filter(Filters=[
        {
            'Name': 'tag:Name',
            'Values': values,
        }
    ]))

    # Filter out terminated instances.
    instances = [
        instance for instance in instances
        if instance.state['Name'] != 'terminated']

    return sorted(instances, key=lambda instance: instance.private_ip_address)
