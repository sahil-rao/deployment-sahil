from __future__ import absolute_import

from health_check.base import HealthCheck, HealthCheckList
from health_check.disk import DiskUsageCheck
import boto3
import functools
import multiprocessing.pool
import redis
import sshtunnel
import sys
import termcolor


class Redis(object):
    def __init__(self, bastion, host, port):
        self.bastion = bastion
        self.host = host
        self.port = port

        self.tunnel = sshtunnel.SSHTunnelForwarder(
            bastion,
            remote_bind_address=(host, port))

        self.tunnel.start()

        self.rconn = redis.StrictRedis(port=self.tunnel.local_bind_port)

    def close(self):
        self.tunnel.close()

    def __del__(self):
        self.close()

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)

    def __hash__(self):
        return hash(self.host)


class RedisHealthCheck(HealthCheck):
    def close(self):
        for host in self.hosts:
            host.close()


class RedisServerHealthCheck(RedisHealthCheck):
    def check_host(self, host):
        return True

        server_info = host.rconn.info()

        if server_info is None:
            self.host_msgs[host] = 'host or redis is offline'
            return False
        else:
            self.host_msgs[host] = ''

        return self.check_redis_host(host, server_info)

    def check_redis_host(self, host, server_info):
        raise NotImplementedError


class RedisNoBlockedClientsCheck(RedisServerHealthCheck):
    description = "No currently blocked clients"

    def check_redis_host(self, hostname, server_info):
        blocked_clients = server_info['blocked_clients']
        self.host_msgs[hostname] += \
            ' blocked_clients: {}'.format(blocked_clients)

        return blocked_clients == 0


class RedisRdbBackupCheck(RedisServerHealthCheck):
    description = "RDB backup successfully saved to disk"

    def check_redis_host(self, host, server_info):
        return server_info['rdb_last_bgsave_status'] == 'ok'


class RedisAofDisabledCheck(RedisServerHealthCheck):

    description = "AOF backups are disabled"

    def check_redis_host(self, host, server_info):
        return server_info['aof_enabled'] == 0


class RedisMemoryUsageCheck(RedisServerHealthCheck):

    description = "Redis memory usage is normal"

    def check_redis_host(self, host, server_info):
        """Redis memory usage is < 30 gb"""
        return server_info['used_memory'] < 30000000000


class RedisClusterConfigurationCheck(RedisServerHealthCheck):

    def __init__(self, *args, **kwargs):
        super(RedisClusterConfigurationCheck, self).__init__(*args, **kwargs)

        slaves = max(0, len(self.hosts) - 1)
        self.description = \
            "Redis cluster has one master and {} " \
            "connected slaves".format(slaves)

    def check_redis_host(self, host, server_info):
        role = server_info['role']
        self.host_msgs[host] = '({})'.format(role)

        if role == 'master':
            return self.check_master(host, server_info)
        else:
            return self.check_slave(host, server_info)

    def check_master(self, host, server_info):
        connected_slaves = server_info['connected_slaves']
        if connected_slaves == len(self.hosts) - 1:
            return True
        else:
            self.host_msgs[host] += ' {} out of {} connected slaves'.format(
                connected_slaves,
                len(self.hosts) - 1
            )
            return False

    def check_slave(self, host, server_info):
        master_link_status = server_info['master_link_status']
        if master_link_status == 'up':
            return True
        else:
            self.host_msgs[host] += \
                ' master link status is `{}`'.format(master_link_status)
            return False


class RedisSentinelHealthCheck(RedisServerHealthCheck):
    pass


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

    description = \
        "Redis sentinel is >= quorum, is odd, " \
        "and matches other sentinels"

    def check_sentinel_host(self, host, sentinel_info):
        quorum = sentinel_info['quorum']
        sentinels = sentinel_info['num-other-sentinels'] + 1

        self.host_msgs[host] += \
            'sentinels: {} quorum: {}'.format(sentinels, quorum)

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


class RedisClusterSyncCheck(RedisServerHealthCheck):

    description = "Redis cluster is not syncing"

    def check_redis_host(self, host, server_info):
        if server_info['role'] == 'master':
            return True
        if server_info['role'] == 'slave':
            return server_info['master_sync_in_progress'] == 0


def _create_redis(bastion, port, host):
    return Redis(bastion, host, port)


def check_redis(bastion, cluster, region, dbsilo):
    redis_checklist = HealthCheckList("Redis Cluster Health Checklist")
    redis_hostnames = _get_redis_hostnames(cluster, region, dbsilo)

    if not redis_hostnames:
        print >> sys.stderr, \
            termcolor.colored('WARNING:', 'yellow'), \
            'no redis servers found'
        return redis_checklist

    pool = multiprocessing.pool.ThreadPool(5)

    try:
        redis_servers = pool.map(
            functools.partial(_create_redis, bastion, 6379),
            redis_hostnames)

        redis_sentinels = pool.map(
            functools.partial(_create_redis, bastion, 26379),
            redis_hostnames)
    finally:
        pool.close()
        pool.join()

    for check in (
            RedisNoBlockedClientsCheck(redis_servers),
            RedisNoBlockedClientsCheck(redis_servers),
            RedisRdbBackupCheck(redis_servers),
            RedisAofDisabledCheck(redis_servers),
            RedisMemoryUsageCheck(redis_servers),
            RedisClusterConfigurationCheck(redis_servers),

            RedisClusterSyncCheck(redis_servers),

            RedisSentinelQuorumCheck(redis_sentinels),
            RedisSentinelMastersCheck(redis_sentinels),

            DiskUsageCheck(bastion, hosts=redis_hostnames),
            ):
        redis_checklist.add_check(check)

    return redis_checklist


def _get_redis_hostnames(cluster, region, dbsilo):
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
