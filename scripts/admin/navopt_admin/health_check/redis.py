from __future__ import absolute_import

from .aws import AWSNameHealthCheck
from .base import HealthCheck, HealthCheckList
import hurry.filesize
import sys
import termcolor


class RedisHealthCheck(HealthCheck):
    def close(self):
        for host in self.hosts:
            host.close()

    def check_host(self, host):
        return self.check_redis_host(host)

    def check_redis_host(self, host):
        raise NotImplementedError


class RedisNoBlockedClientsCheck(RedisHealthCheck):
    description = "No currently blocked clients"

    def check_redis_host(self, host):
        blocked_clients = host.info()['blocked_clients']
        self.host_msgs[host] = \
            ' blocked_clients: {}'.format(blocked_clients)

        return blocked_clients == 0


class RedisRdbBackupCheck(RedisHealthCheck):
    description = "RDB backup successfully saved to disk"

    def check_redis_host(self, host):
        return host.info()['rdb_last_bgsave_status'] == 'ok'


class RedisAofDisabledCheck(RedisHealthCheck):
    description = "AOF backups are disabled"

    def check_redis_host(self, host):
        return host.info()['aof_enabled'] == 0


class RedisMemoryUsageCheck(RedisHealthCheck):
    description = "Redis memory usage < 30GB"

    def check_redis_host(self, host):
        """Redis memory usage is < 30 gb"""

        used_memory = host.info()['used_memory']
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
        role = host.info()['role']
        self.host_msgs[host] = '({})'.format(role)

        if role == 'master':
            return self.check_master(host)
        else:
            return self.check_slave(host)

    def check_master(self, host):
        connected_slaves = host.info()['connected_slaves']
        if connected_slaves == len(self.hosts) - 1:
            return True
        else:
            self.host_msgs[host] = ' {} out of {} connected slaves'.format(
                connected_slaves,
                len(self.hosts) - 1
            )
            return False

    def check_slave(self, host):
        master_link_status = host.info()['master_link_status']
        if master_link_status == 'up':
            return True
        else:
            self.host_msgs[host] = \
                ' master link status is `{}`'.format(master_link_status)
            return False


class RedisClusterSyncCheck(RedisHealthCheck):

    description = "Redis cluster is not syncing"

    def check_redis_host(self, host):
        if host.info()['role'] == 'master':
            return True
        if host.info()['role'] == 'slave':
            return host.info()['master_sync_in_progress'] == 0


class RedisSentinelHealthCheck(RedisHealthCheck):
    def __init__(self, master, *args, **kwargs):
        super(RedisHealthCheck, self).__init__(*args, **kwargs)

        self.master = master


class RedisSentinelMastersCheck(RedisSentinelHealthCheck):
    description = "Redis sentinels have the same master"

    def check_redis_host(self, host):
        ip = host.sentinel_masters()[self.master]['ip']
        self.host_msgs[host] = 'master: {}'.format(ip)

        for h in self.hosts:
            if h == host:
                continue

            if h.sentinel_masters()[self.master].get('ip') != ip:
                return False

        return True


class RedisSameSentinelsCheck(RedisSentinelHealthCheck):
    description = "Redis machines have the same sentinels"

    def check_redis_host(self, host):
        sentinels = self.sentinels(host)
        self.host_msgs[host] = 'sentinels: {}'.format(
            ','.join(sorted(sentinels)))

        for h in self.hosts:
            if h == host:
                continue

            if self.sentinels(h) != sentinels:
                return False

        return True

    def sentinels(self, redis):
        sentinels = set()

        # Add the current host to the sentinel list.
        sentinels.add('{}:{}'.format(redis.host, redis.port))

        sentinels.update(
            sentinel['name']
            for sentinel in redis.sentinel_sentinels(self.master))

        return sentinels


class RedisSentinelQuorumCheck(RedisSentinelHealthCheck):

    description = \
        "Redis sentinel is >= quorum, is odd, " \
        "and matches other sentinels"

    def check_redis_host(self, host):
        info = host.sentinel_masters()[self.master]
        quorum = info['quorum']
        sentinels = info['num-other-sentinels'] + 1

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

            h_info = h.sentinel_masters()[self.master]

            if h_info.get('quorum') != quorum:
                self.host_msgs[host] += ' (quorum count does not match)'
                result = False

            if h_info['num-other-sentinels'] + 1 != sentinels:
                self.host_msgs[host] += ' (sentinel count does not match)'
                result = False

        return result


def check_redis(redis_cluster):
    redis_servers = list(redis_cluster.clients())
    redis_sentinels = list(redis_cluster.sentinel_clients())

    redis_checklist = HealthCheckList(
        "{} health checklist".format(redis_cluster.service))

    if not redis_servers:
        print >> sys.stderr, \
            termcolor.colored('WARNING:', 'yellow'), \
            'no redis servers found in', redis_cluster.service
        return redis_checklist

    master_hostname = redis_cluster.master_hostname()

    for check in (
            AWSNameHealthCheck(redis_cluster.instances),

            RedisNoBlockedClientsCheck(redis_servers),
            RedisNoBlockedClientsCheck(redis_servers),
            RedisRdbBackupCheck(redis_servers),
            RedisAofDisabledCheck(redis_servers),
            RedisMemoryUsageCheck(redis_servers),
            RedisClusterConfigurationCheck(redis_servers),

            RedisClusterSyncCheck(redis_servers),

            RedisSameSentinelsCheck(master_hostname, redis_sentinels),
            RedisSentinelQuorumCheck(master_hostname, redis_sentinels),
            RedisSentinelMastersCheck(master_hostname, redis_sentinels),
            ):
        redis_checklist.add_check(check)

    return redis_checklist
