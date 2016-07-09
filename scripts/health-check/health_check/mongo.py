from __future__ import absolute_import

from .base import HealthCheck, HealthCheckList
from .disk import DiskUsageCheck
from .tunnel import Tunnel
import boto3
import functools
import multiprocessing.pool
import pymongo
import sys
import termcolor


class Mongo(Tunnel):
    def __init__(self, bastion, host, port):
        super(Mongo, self).__init__(bastion, host, port)

#        if self.tunnel.is_use_local_check_up:
        self.mconn = pymongo.MongoClient(
            port=self.tunnel.local_bind_port,
            socketTimeoutMS=10000,
            connectTimeoutMS=10000,
            serverSelectionTimeoutMS=10000,
        )

        try:
            self.mconn.admin.command('replSetGetStatus')
        except pymongo.errors.ServerSelectionTimeoutError:
            self.mconn = None


class MongoHealthCheck(HealthCheck):
    def close(self):
        for host in self.hosts:
            host.close()


class MongoClusterConfigurationCheck(MongoHealthCheck):
    def __init__(self, *args, **kwargs):
        super(MongoClusterConfigurationCheck, self).__init__(*args, **kwargs)

        self.description = \
            "Mongo instance's replica set view has one " \
            "primary and {} secondaries".format(len(self.hosts) - 1)

    def check_host(self, host):
        if not host.mconn:
            self.host_msgs[host] = 'tunnel is down'
            return False

        repl_status = host.mconn.admin.command('replSetGetStatus')

        num_primaries = 0
        num_secondaries = 0
        num_otherstate = 0

        for member in repl_status['members']:
            if member['state'] == 1:
                num_primaries += 1
            elif member['state'] == 2:
                num_secondaries += 1
            else:
                num_otherstate += 1

        self.host_msgs[host] = 'primaries: {} secondaries: {} other: {}'.format(
            num_primaries,
            num_secondaries,
            num_otherstate)

        return \
            num_primaries == 1 and \
            num_secondaries == len(self.hosts) - 1 and \
            num_otherstate == 0


class MongoClusterConfigVersionsCheck(HealthCheck):
    description = "Config version of all replica set members match"

    def check_host(self, host):
        if not host.mconn:
            self.host_msgs[host] = 'tunnel is down'
            return False

        repl_status = host.mconn.admin.command('replSetGetStatus')
        config_versions = set()
        for member in repl_status['members']:
            config_versions.add(member['configVersion'])

        self.host_msgs[host] = 'versions: {}'.format(sorted(config_versions))

        return len(config_versions) <= 1


class MongoClusterHeartbeatCheck(HealthCheck):
    description = "Last heartbeat received is recent"

    def check_host(self, host):
        if not host.mconn:
            self.host_msgs[host] = 'tunnel is down'
            return False

        repl_status = host.mconn.admin.command('replSetGetStatus')
        print repl_status

        return False


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
            MongoClusterConfigurationCheck(mongodb_servers),
            MongoClusterConfigVersionsCheck(mongodb_servers),
            DiskUsageCheck(bastion, mongodb_hostnames),
            ):
        mongodb_checklist.add_check(health_check)

    return mongodb_checklist


def _get_mongodb_hostnames(cluster, region, dbsilo):
    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
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
            hostnames.append(instance.private_dns_name)

    return hostnames


def _create_mongo(bastion, port, host):
    return Mongo(bastion, host, port)
