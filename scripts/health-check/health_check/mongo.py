from __future__ import absolute_import

from health_check.base import HealthCheck, HealthCheckList
from health_check.disk import DiskUsageCheck
import boto3
import pymongo


class MongoClusterConfigurationCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.description = \
            "Mongo instance's replica set view has one " \
            "primary and two secondaries"

    def check_host(self, host):
        mconn = pymongo.MongoClient(host)
        repl_status = mconn.admin.command('replSetGetStatus')
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

        return num_primaries == 1 and \
            num_secondaries == 2 and \
            num_otherstate == 0


class MongoClusterConfigVersionsCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.description = "Config version of all replica set members match"

    def check_host(self, host):
        mconn = pymongo.MongoClient(host)
        repl_status = mconn.admin.command('replSetGetStatus')
        config_versions = []
        for member in repl_status['members']:
            config_versions.append(member['configVersion'])

        return len(set(config_versions)) <= 1


class MongoClusterHeartbeatCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.description = "Last heartbeat received is recent"

    def check_host(self, host):
        mconn = pymongo.MongoClient(host)
        repl_status = mconn.admin.command('replSetGetStatus')
        print repl_status

        return False


def check_mongodb(bastion, cluster, region, dbsilo):
    mongodb_checklist = HealthCheckList("MongoDB Cluster Health Checklist")

    mongo_servers = _get_mongodb_servers(cluster, region, dbsilo)

    for health_check in (
            MongoClusterConfigurationCheck(mongo_servers),
            MongoClusterConfigVersionsCheck(mongo_servers),
            DiskUsageCheck(bastion, mongo_servers),
            ):
        mongodb_checklist.add_check(health_check)

    return mongodb_checklist


def _get_mongodb_servers(cluster, region, dbsilo):
    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
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
