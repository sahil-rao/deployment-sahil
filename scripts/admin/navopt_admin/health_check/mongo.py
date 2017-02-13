from __future__ import absolute_import

from .aws import AWSNameHealthCheck
from .base import HealthCheck, HealthCheckList
import datetime
import sys
import termcolor


class MongoHealthCheck(HealthCheck):
    def open(self):
        for host in self.hosts:
            host.open()

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

    def __init__(self, mongo_cluster, *args, **kwargs):
        super(MongoClusterAgreeOnMasterCheck, self).__init__(*args, **kwargs)

        self.mongo_cluster = mongo_cluster

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
        master_hostname = self.mongo_cluster.master_hostname()
        found_host = self.mongo_cluster.cluster.bastion.resolve_hostname(
            master_hostname)

        if not found_host:
            self.host_msgs[host] += ' failed to resolve: ' + master_hostname
            return False

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


def check_mongo(mongo_cluster):
    mongodb_checklist = HealthCheckList(
        "{} health checklist".format(mongo_cluster.service)
    )

    mongo_clients = list(mongo_cluster.clients())

    if not mongo_clients:
        print >> sys.stderr, \
            termcolor.colored('WARNING:', 'yellow'), \
            'no mongodb server found in', mongo_cluster.service

        return mongodb_checklist

    for health_check in (
            AWSNameHealthCheck(mongo_cluster.instances),

            MongoVersionCheck(mongo_clients),
            MongoClusterAgreeOnMasterCheck(mongo_cluster, mongo_clients),
            MongoClusterConfigurationCheck(mongo_clients),
            MongoClusterConfigVersionsCheck(mongo_clients),
            MongoClusterHeartbeatCheck(mongo_clients),
            MongoReplicaDelayCheck(mongo_clients),
            ):
        mongodb_checklist.add_check(health_check)

    return mongodb_checklist
