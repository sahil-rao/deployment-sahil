#!/usr/bin/env python

import boto3
import click
import json
import functools
import multiprocessing
import pymongo
import re
import redis
import sshtunnel
import sys
import termcolor
import urllib2
from pprint import pprint


def find_route53_records(resource, dbsilo, cluster_name='alpha', suffix='xplain.io'):
    """Find all relevant resource URLs from Route 53"""

    AWS_METADATA_ENDPOINT = 'http://169.254.169.254/latest/meta-data/'

    resp = urllib2.urlopen(AWS_METADATA_ENDPOINT + 'placement/availability-zone/')
    aws_availability_zone = resp.read()
    aws_region = re.match('(us|sa|eu|ap)-(north|south|central)?(east|west)?-[0-9]+',
                          aws_availability_zone).group(0)

    conn = boto.route53.connect_to_region(aws_region)
    route53_zone = conn.get_zone("{0}.{1}".format(cluster_name, suffix))

    # Match records belonging to the service for particular dbsilo and cluster
    match_regex = "({0}\d+\.{1}\.{2}\.{3}.?)" \
                  .format(resource, dbsilo, cluster_name, suffix)
    resource_records = []
    for record in route53_zone.get_records():
        match = re.search(match_regex, record.name)
        if match:
            resource_records.append(match.group(0))

    return resource_records

def get_mongodb_servers(dbsilo):
    return find_route53_records('mongo', dbsilo)

def get_redis_servers(cluster, region, dbsilo):
    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                '{}-{}-redis-green-*'.format(cluster, dbsilo),
                '{}-{}-redis-blue-*'.format(cluster, dbsilo),
            ],
        },
    ])

    hostnames = []
    for instance in instances:
        if instance.private_ip_address:
            hostnames.append(instance.private_dns_name)

    return hostnames

#    return find_route53_records('redis', dbsilo)

def get_elasticsearch_servers(dbsilo):
    return find_route53_records('elasticsearch', dbsilo)

# TODO: Make this function real
def get_backoffice_servers():
    return [
        "172.31.5.184",
        "172.31.13.245",
        "172.31.13.244",
        "172.31.13.243",
        "172.31.13.242",
        "172.31.7.45",
        "172.31.7.46",
        "172.31.7.48",
        "172.31.7.50"
    ]


# Terminal codes for colors to make things pretty
class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


# Subclass this to make a new check
class HealthCheck(object):
    description = ""

    def __init__(self, hosts, description=None):
        self.hosts = hosts
        self.host_msgs = {}

        if description is not None:
            self.description = description

    def execute(self, tabs=1):
        """Return True if healthcheck passed on all hosts"""
        host_statuses = []
        for host in self.hosts:
            status = self.check_host(host)
            host_statuses.append(status)
        return all(host_statuses)

    def check_host(self, host):
        """Return True if healthcheck passed no host"""
        raise NotImplementedError


# Executes all healthchecks added to the checklist; Checklists may be composed
class HealthCheckList(object):

    def __init__(self, description):
        self.health_checks = []
        self.description = description

    def add_check(self, healthcheck):
        self.health_checks.append(healthcheck)

    def execute(self, tabs=1):
        print ""
        print "\t" * (tabs-1), color.BLUE, color.BOLD, "Executing checklist: ", self.description, color.END, color.END
        print "\t" * (tabs-1), " ", len(self.health_checks), "checks to execute in the checklist:"
        healthcheck_statuses = []
        for i, healthcheck in enumerate(self.health_checks):
            status = healthcheck.execute(tabs + 1)
            if isinstance(healthcheck, HealthCheck):
                if status is True:
                    print "\t" * tabs, str(i+1) + ")", color.BOLD, color.GREEN, "PASSED", color.END, ":", color.BOLD, healthcheck.description, color.END
                else:
                    print "\t" * tabs, str(i+1) + ")", color.BOLD, color.RED, "FAILED", color.END, ":", color.BOLD, healthcheck.description, color.END
                for host in healthcheck.hosts:
                    host_msg = healthcheck.host_msgs.get(host, '')
                    if host_msg:
                        host_msg = '\t- {}'.format(host_msg)

                    if healthcheck.check_host(host):
                        print "\t" * (tabs+1), "PASSED\t" + host, host_msg
                    else:
                        print "\t" * (tabs+1), "FAILED\t" + host, host_msg

            healthcheck_statuses.append(status)

        status = all(healthcheck_statuses)
        if status is True:
            print "\t" * (tabs-1), color.GREEN, color.BOLD, "PASSED", color.END, color.END, "Checklist:", color.UNDERLINE + self.description + color.END
        else:
            print "\t" * (tabs-1), color.RED, color.BOLD, "FAILED", color.END, color.END, "Checklist:", color.UNDERLINE + self.description + color.END

        return status


class MongoClusterConfigurationCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.description = "Mongo instance's replica set view has one primary and two secondaries"

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

        return num_primaries == 1 and num_secondaries == 2 and num_otherstate == 0

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



class DiskUsageCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.description = "Disk usage on all drives is < 80%"

    def check_host(self, host):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username="ubuntu")
        stdin, stdout, stderr = client.exec_command("df -hP | awk 'NR>1{print $1,$5}' | sed -e's/%//g'")
        for line in stdout.readlines():
            drive, percent_full = line.strip().split()
            if int(percent_full) > 80:
                return False
        return True


class RedisHealthCheck(HealthCheck):
    def __init__(self, redis_server_info, redis_sentinel_info):
        super(RedisHealthCheck, self).__init__(redis_server_info.keys())
        self.redis_server_info = redis_server_info
        self.redis_sentinel_info = redis_sentinel_info

    def check_host(self, host):
        redis_server_info = self.redis_server_info[host]
        if redis_server_info is None:
            self.host_msgs[host] = 'host or redis is offline'
            return False
        else:
            self.host_msgs[host] = ''

        return self.check_redis_host(host, redis_server_info)

    def check_redis_host(self, host, redis_server_info):
        raise NotImplementedError

class RedisNoBlockedClientsCheck(RedisHealthCheck):

    description = "No currently blocked clients"

    def check_redis_host(self, host, redis_server_info):
        return redis_server_info['blocked_clients'] == 0

class RedisRdbBackupCheck(RedisHealthCheck):
    description = "RDB backup successfully saved to disk"

    def check_redis_host(self, host, redis_server_info):
        return redis_server_info['rdb_last_bgsave_status'] == 'ok'

class RedisAofDisabledCheck(RedisHealthCheck):

    description = "AOF backups are disabled"

    def check_redis_host(self, host, redis_server_info):
        return redis_server_info['aof_enabled'] == 0

class RedisMemoryUsageCheck(RedisHealthCheck):

    description = "Redis memory usage is normal"

    def check_redis_host(self, host, redis_server_info):
        """Redis memory usage is < 30 gb"""
        return redis_server_info['used_memory'] < 30000000000

class RedisClusterConfigurationCheck(RedisHealthCheck):

    def __init__(self, *args, **kwargs):
        super(RedisClusterConfigurationCheck, self).__init__(*args, **kwargs)

        slaves = max(0, len(self.redis_server_info) - 1)
        self.description = "Redis cluster has one master and {} connected slaves".format(slaves)

    def check_redis_host(self, host, redis_server_info):
        role = redis_server_info['role']
        self.host_msgs[host] = '({})'.format(role)

        if role == 'master':
            return self.check_master(host, redis_server_info)
        else:
            return self.check_slave(host, redis_server_info)

    def check_master(self, host, redis_server_info):
        connected_slaves = redis_server_info['connected_slaves']
        if connected_slaves == len(self.hosts) - 1:
            return True
        else:
            self.host_msgs[host] += ' {} out of {} connected slaves'.format(
                connected_slaves,
                len(self.hosts) - 1
            )
            return False

    def check_slave(self, host, redis_server_info):
        master_link_status = redis_server_info['master_link_status']
        if master_link_status == 'up':
            return True
        else:
            self.host_msgs[host] += ' master link status is `{}`'.format(master_link_status)
            return False


class RedisSentinelHealthCheck(RedisHealthCheck):

    def check_redis_host(self, host, redis_server_info):
        sentinel_info = self.redis_sentinel_info[host]
        if sentinel_info is None:
            self.host_msgs[host] += 'sentinel is not up'
            return False

        return self.check_sentinel_host(host, sentinel_info)

    def check_sentinel_host(self, host, sentinel_info):
        raise NotImplementedError


class RedisSentinelMastersCheck(RedisSentinelHealthCheck):

    description = "Redis sentinels have the same master"

    def check_sentinel_host(self, host, sentinel_info):
        ip = self.redis_sentinel_info[host]['ip']
        self.host_msgs[host] += 'master: {}'.format(ip)

        for h, info in self.redis_sentinel_info.iteritems():
            if h == host or info is None:
                continue

            if info.get('ip') != ip:
                return False

        return True


class RedisSentinelQuorumCheck(RedisSentinelHealthCheck):

    description = "Redis sentinel is >= quorum, is odd, and matches other sentinels"

    def check_sentinel_host(self, host, sentinel_info):
        quorum = sentinel_info['quorum']
        sentinels = sentinel_info['num-other-sentinels'] + 1

        self.host_msgs[host] += 'sentinels: {} quorum: {}'.format(sentinels, quorum)

        result = True

        if sentinels < quorum:
            self.host_msgs[host] += ' (under quorum)'
            result = False

        if sentinels % 2 == 0:
            self.host_msgs[host] += ' (even number of sentinels)'
            result = False

        for h, info in self.redis_sentinel_info.iteritems():
            if h == host or info is None:
                continue

            if info.get('quorum') != quorum:
                self.host_msgs[host] += ' (quorum count does not match)'
                result = False

            if info['num-other-sentinels'] + 1 != sentinels:
                self.host_msgs[host] += ' (sentinel count does not match)'
                result = False

        return result


class RedisClusterSyncCheck(RedisHealthCheck):

    description = "Redis cluster is not syncing"

    def check_redis_host(self, host, redis_server_info):
        if redis_server_info['role'] == 'master':
            return True
        if redis_server_info['role'] == 'slave':
            return redis_server_info['master_sync_in_progress'] == 0


def check_mongodb(dbsilo):
    mongodb_checklist = HealthCheckList("MongoDB Cluster Health Checklist")
    for klass in (MongoClusterConfigurationCheck, MongoClusterConfigVersionsCheck, DiskUsageCheck):
        mongodb_checklist.add_check(klass(get_mongodb_servers(dbsilo)))
    dbsilo_checklist.add_check(mongodb_checklist)


def get_redis_server_info(bastion, redis_server):
    server = sshtunnel.SSHTunnelForwarder(
            bastion,
            remote_bind_address=(redis_server, 6379))

    try:
        server.start()
        rconn = redis.StrictRedis(port=server.local_bind_port)
        info = rconn.info()
    except redis.exceptions.ConnectionError:
        info = None
    except sshtunnel.HandlerSSHTunnelForwarderError:
        info = None
    finally:
        server.stop()

    return redis_server, info



def get_redis_sentinel_info(bastion, cluster, dbsilo, redis_sentinel):
    sentinel = sshtunnel.SSHTunnelForwarder(
            bastion,
            remote_bind_address=(redis_sentinel, 26379))

    try:
        sentinel.start()
        rconn = redis.StrictRedis(port=sentinel.local_bind_port)
        sentinel_masters = rconn.sentinel_masters()
        info = sentinel_masters.get('redismaster.{}.{}.xplain.io'.format(dbsilo, cluster))
    except redis.exceptions.ConnectionError:
        info = None
    except sshtunnel.HandlerSSHTunnelForwarderError:
        info = None
    finally:
        sentinel.stop()

    return redis_sentinel, info


def check_redis(bastion, cluster, region, dbsilo):
    redis_checklist = HealthCheckList("Redis Cluster Health Checklist")
    redis_servers = get_redis_servers(cluster, region, dbsilo)

    if not redis_servers:
        print >> sys.stderr, termcolor.colored('WARNING:', 'yellow'), 'no redis servers found'
        return redis_checklist

    # Grab the redis info from each server.
    pool = multiprocessing.Pool(5)
    redis_server_info = dict(pool.map(
        functools.partial(get_redis_server_info, bastion),
        redis_servers))

    redis_sentinel_info = dict(pool.map(
        functools.partial(get_redis_sentinel_info, bastion, cluster, dbsilo),
        redis_servers))

    for check in (
            RedisNoBlockedClientsCheck(redis_server_info, redis_sentinel_info),
            RedisRdbBackupCheck(redis_server_info, redis_sentinel_info),
            RedisAofDisabledCheck(redis_server_info, redis_sentinel_info),
            RedisMemoryUsageCheck(redis_server_info, redis_sentinel_info),
            RedisClusterConfigurationCheck(redis_server_info, redis_sentinel_info),
            RedisSentinelQuorumCheck(redis_server_info, redis_sentinel_info),
            RedisSentinelMastersCheck(redis_server_info, redis_sentinel_info),
            RedisClusterSyncCheck(redis_server_info, redis_sentinel_info),
            #DiskUsageCheck,
            ):
        redis_checklist.add_check(check)

    return redis_checklist


@click.command()
@click.option('-b', '--bastion', default=None)
@click.argument('cluster')
@click.argument('region')
@click.argument('dbsilo')
def cli(bastion, cluster, region, dbsilo):
    try:
        bastion = {
            'navopt-alpha': 'alpha-root.xplain.io',
            'navopt-prod': '52.27.164.215',
        }[bastion]
    except KeyError:
        pass

    cluster_checklist = HealthCheckList("NavOpt Cluster Health Checklist")

    dbsilo_checklist = HealthCheckList(dbsilo.upper() + " Health Checklist")
    #dbsilo_checklist.add_check(check_mongodb(dbsilo))
    dbsilo_checklist.add_check(check_redis(bastion, cluster, region, dbsilo))

    cluster_checklist.add_check(dbsilo_checklist)

#    backoffice_checklist = HealthCheckList("Backoffice Health Checklist")
#    backoffice_checklist.add_check(DiskUsageCheck(get_backoffice_servers()))
#    cluster_checklist.add_check(backoffice_checklist)

    cluster_checklist.execute()
