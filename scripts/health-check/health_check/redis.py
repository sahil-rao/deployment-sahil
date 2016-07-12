from __future__ import absolute_import

from .base import HealthCheck, HealthCheckList
from .disk import DiskUsageCheck
from .tunnel import Tunnel
import boto3
import functools
import hurry.filesize
import multiprocessing.pool
import redis
import sys
import termcolor


class Redis(Tunnel):
    def __init__(self, bastion, hostname, port, master):
        super(Redis, self).__init__(bastion, hostname, port)
        self.master = master

        if self.tunnel:
            self.rconn = redis.StrictRedis(port=self.tunnel.local_bind_port)
        else:
            self.rconn = None

    @property
    def info(self):
        if not hasattr(self, '_info'):
            self._info = self.rconn.info()

        return self._info

    @property
    def sentinel_masters(self):
        if not hasattr(self, '_sentinel_masters'):
            self._sentinel_masters = self.rconn.sentinel_masters()

        return self._sentinel_masters

    @property
    def sentinel_info(self):
        return self.sentinel_masters[self.master]

    @property
    def sentinels(self):
        if self.rconn is None:
            return set()

        sentinels = set()

        # Add the current host to the sentinel list.
        sentinels.add('{}:{}'.format(self.host, self.port))

        sentinels.update(sentinel['name']
            for sentinel in self.rconn.sentinel_sentinels(self.master))

        return sentinels


class RedisHealthCheck(HealthCheck):
    def close(self):
        for host in self.hosts:
            host.close()

    def check_host(self, host):
        if host.rconn is None:
            self.host_msgs[host] = 'cannot connect to Redis'
            return False

        return self.check_redis_host(host)

    def check_redis_host(self, host):
        raise NotImplementedError



class RedisNoBlockedClientsCheck(RedisHealthCheck):
    description = "No currently blocked clients"

    def check_redis_host(self, host):
        blocked_clients = host.info['blocked_clients']
        self.host_msgs[host] = \
            ' blocked_clients: {}'.format(blocked_clients)

        return blocked_clients == 0


class RedisRdbBackupCheck(RedisHealthCheck):
    description = "RDB backup successfully saved to disk"

    def check_redis_host(self, host):
        return host.info['rdb_last_bgsave_status'] == 'ok'


class RedisAofDisabledCheck(RedisHealthCheck):
    description = "AOF backups are disabled"

    def check_redis_host(self, host):
        return host.info['aof_enabled'] == 0


class RedisMemoryUsageCheck(RedisHealthCheck):
    description = "Redis memory usage < 30GB"

    def check_redis_host(self, host):
        """Redis memory usage is < 30 gb"""

        used_memory = host.info['used_memory']
        self.host_msgs[host] = hurry.filesize.size(used_memory)

        return used_memory < 30000000000


class RedisClusterConfigurationCheck(RedisHealthCheck):
    def __init__(self, *args, **kwargs):
        super(RedisClusterConfigurationCheck, self).__init__(*args, **kwargs)

        slaves = max(0, len(self.hosts) - 1)
        self.description = \
            "Redis cluster has one master and {} " \
            "connected slaves".format(slaves)

    def check_redis_host(self, host):
        role = host.info['role']
        self.host_msgs[host] = '({})'.format(role)

        if role == 'master':
            return self.check_master(host)
        else:
            return self.check_slave(host)

    def check_master(self, host):
        connected_slaves = host.info['connected_slaves']
        if connected_slaves == len(self.hosts) - 1:
            return True
        else:
            self.host_msgs[host] = ' {} out of {} connected slaves'.format(
                connected_slaves,
                len(self.hosts) - 1
            )
            return False

    def check_slave(self, host):
        master_link_status = host.info['master_link_status']
        if master_link_status == 'up':
            return True
        else:
            self.host_msgs[host] = \
                ' master link status is `{}`'.format(master_link_status)
            return False


class RedisClusterSyncCheck(RedisHealthCheck):

    description = "Redis cluster is not syncing"

    def check_redis_host(self, host):
        if host.info['role'] == 'master':
            return True
        if host.info['role'] == 'slave':
            return host.info['master_sync_in_progress'] == 0


class RedisSentinelMastersCheck(RedisHealthCheck):

    description = "Redis sentinels have the same master"

    def check_redis_host(self, host):
        ip = host.sentinel_info['ip']
        self.host_msgs[host] = 'master: {}'.format(ip)

        for h in self.hosts:
            if h == host:
                continue

            if h.sentinel_info.get('ip') != ip:
                return False

        return True


class RedisSameSentinelsCheck(RedisHealthCheck):

    description = "Redis machines have the same sentinels"

    def check_redis_host(self, host):
        sentinels = host.sentinels
        self.host_msgs[host] = 'sentinels: {}'.format(
            ','.join(sorted(sentinels)))

        initial = None
        for h in self.hosts:
            if h == host:
                continue

            if h.sentinels != sentinels:
                return False

        return True


class RedisSentinelQuorumCheck(RedisHealthCheck):

    description = \
        "Redis sentinel is >= quorum, is odd, " \
        "and matches other sentinels"

    def check_redis_host(self, host):
        quorum = host.sentinel_info['quorum']
        sentinels = host.sentinel_info['num-other-sentinels'] + 1

        self.host_msgs[host] = \
            'sentinels: {} quorum: {}'.format(sentinels, quorum)

        result = True

        if sentinels < quorum:
            self.host_msgs[host] += ' (under quorum)'
            result = False

        if sentinels % 2 == 0:
            self.host_msgs[host] += ' (even number of sentinels)'
            result = False

        for h in self.hosts:
            if h == host:
                continue

            if h.sentinel_info.get('quorum') != quorum:
                self.host_msgs[host] += ' (quorum count does not match)'
                result = False

            if h.sentinel_info['num-other-sentinels'] + 1 != sentinels:
                self.host_msgs[host] += ' (sentinel count does not match)'
                result = False

        return result


def check_redis(bastion, cluster, region, dbsilo):
    redis_checklist = HealthCheckList("Redis Cluster Health Checklist")
    redis_hostnames = _get_redis_hostnames(cluster, region, dbsilo)

    if not redis_hostnames:
        print >> sys.stderr, \
            termcolor.colored('WARNING:', 'yellow'), \
            'no redis servers found in', cluster, region, dbsilo
        return redis_checklist

    pool = multiprocessing.pool.ThreadPool(5)

    redis_master = 'redismaster.{}.{}.xplain.io'.format(dbsilo, cluster)

    try:
        redis_servers = pool.map(
            functools.partial(_create_redis, bastion, 6379, redis_master),
            redis_hostnames)

        redis_sentinels = pool.map(
            functools.partial(_create_redis, bastion, 26379, redis_master),
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

            RedisSameSentinelsCheck(redis_sentinels),
            RedisSentinelQuorumCheck(redis_sentinels),
            RedisSentinelMastersCheck(redis_sentinels),

            DiskUsageCheck(bastion, hosts=redis_hostnames),
            ):
        redis_checklist.add_check(check)

    return redis_checklist


def _get_redis_hostnames(cluster, region, dbsilo):
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
        'dbsilo1': 'DBSILO_1',
        'dbsilo2': 'DBSILO_2',
        'dbsilo3': 'DBSILO_3',
        'dbsilo4': 'DBSILO_4',
    }

    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Redis {} {}'.format(
                    alpha_names[cluster],
                    alpha_names[dbsilo]),
                'REDIS_{}_{}'.format(
                    app_names[cluster],
                    app_names[dbsilo]),
                '{}-{}-redis-green'.format(cluster, dbsilo),
                '{}-{}-redis-blue'.format(cluster, dbsilo),
                '{}-{}-redis-green-*'.format(cluster, dbsilo),
                '{}-{}-redis-blue-*'.format(cluster, dbsilo),
            ],
        },
    ])

    hostnames = []
    for instance in instances:
        if instance.private_ip_address:
            hostnames.append(instance.private_ip_address)

    hostnames.sort()

    return hostnames


def _create_redis(bastion, port, master, host):
    return Redis(bastion, host, port, master)
