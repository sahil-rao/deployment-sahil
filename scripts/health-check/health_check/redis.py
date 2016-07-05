from __future__ import absolute_import

from health_check.base import HealthCheck, HealthCheckList
from health_check.disk import DiskUsageCheck
from pprint import pprint
import boto3
import click
import functools
import health_check.base
import health_check.dbsilo
import json
import multiprocessing
import pymongo
import re
import redis
import sshtunnel
import sys
import termcolor
import urllib2


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


def check_redis(bastion, cluster, region, dbsilo):
    redis_checklist = HealthCheckList("Redis Cluster Health Checklist")
    redis_servers = _get_redis_servers(cluster, region, dbsilo)

    if not redis_servers:
        print >> sys.stderr, termcolor.colored('WARNING:', 'yellow'), 'no redis servers found'
        return redis_checklist

    # Grab the redis info from each server.
    pool = multiprocessing.Pool(5)
    redis_server_info = dict(pool.map(
        functools.partial(_get_redis_server_info, bastion),
        redis_servers))

    redis_sentinel_info = dict(pool.map(
        functools.partial(_get_redis_sentinel_info, bastion, cluster, dbsilo),
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
            DiskUsageCheck(bastion, hosts=redis_servers),
            ):
        redis_checklist.add_check(check)

    return redis_checklist


def _get_redis_servers(cluster, region, dbsilo):
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


def _get_redis_server_info(bastion, redis_server):
    server = sshtunnel.SSHTunnelForwarder(
            bastion,
            remote_bind_address=(redis_server, 6379))

    try:
        server.start()
        rconn = redis.StrictRedis(port=server.local_bind_port)
        info = rconn.info()
    except redis.ConnectionError:
        info = None
    except sshtunnel.HandlerSSHTunnelForwarderError:
        info = None
    finally:
        server.stop()

    return redis_server, info



def _get_redis_sentinel_info(bastion, cluster, dbsilo, redis_sentinel):
    sentinel = sshtunnel.SSHTunnelForwarder(
            bastion,
            remote_bind_address=(redis_sentinel, 26379))

    try:
        sentinel.start()
        rconn = redis.StrictRedis(port=sentinel.local_bind_port)
        sentinel_masters = rconn.sentinel_masters()
        info = sentinel_masters.get('redismaster.{}.{}.xplain.io'.format(dbsilo, cluster))
    except redis.ConnectionError:
        info = None
    except sshtunnel.HandlerSSHTunnelForwarderError:
        info = None
    finally:
        sentinel.stop()

    return redis_sentinel, info
