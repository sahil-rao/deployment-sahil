from __future__ import absolute_import

import redis
import re


class RedisCluster(object):
    def __init__(self, cluster, service, instances):
        self.cluster = cluster
        self.service = service
        self.instances = instances

    def master_hostname(self):
        return '{}-master.{}'.format(
            self.service,
            self.cluster.zone)

    def master(self):
        master_hostname = self.master_hostname()
        return Redis(self.cluster.bastion, master_hostname)

    def instance_private_ips(self):
        for instance in self.instances:
            yield instance.private_ip_address

    def clients(self):
        for ip in self.instance_private_ips():
            yield Redis(self.cluster.bastion, ip)

    def sentinel_clients(self):
        for instance in self.instances:
            yield RedisSentinel(
                self.cluster.bastion,
                instance.private_ip_address)


# FIXME: Remove once we get rid of the old-style instances
class OldRedisCluster(RedisCluster):
    def __init__(self, dbsilo, *args, **kwargs):
        super(OldRedisCluster, self).__init__(*args, **kwargs)

        self.dbsilo = dbsilo

    def master_hostname(self):
        env = self.cluster.env
        if env == 'prod':
            env = 'app'

        return 'redismaster.{}.{}'.format(
            self.dbsilo,
            self.cluster.zone)


class Redis(object):
    def __init__(self, bastion, host, port=6379):
        self.host = host
        self.port = port

        self._tunnel = bastion.tunnel(host, port)

        self._conn = redis.StrictRedis(
            host=self._tunnel.local_host,
            port=self._tunnel.local_port,
        )

    def close(self):
        self._tunnel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getattr__(self, key):
        return getattr(self._conn, key)

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)


class RedisSentinel(Redis):
    def __init__(self, bastion, host, port=26379):
        super(RedisSentinel, self).__init__(bastion, host, port)
