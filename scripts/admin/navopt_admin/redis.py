from __future__ import absolute_import

import logging
import redis
from .ssh import TunnelDown

LOG = logging.getLogger(__name__)


class ConnectionClosed(Exception):
    pass


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
        port = 6379

        master_address = self.cluster.bastion.resolve_hostname(master_hostname)
        tunnel = self.cluster.bastion.tunnel(master_address, port)
        return Redis(self.cluster.bastion, tunnel, master_address, port)

    def instance_private_ips(self):
        for instance in self.instances:
            yield instance.private_ip_address

    def clients(self, port=6379):
        tunnels = []

        for ip in self.instance_private_ips():
            tunnel = self.cluster.bastion.tunnel(ip, port)
            tunnels.append((ip, tunnel))

        for ip, tunnel in tunnels:
            yield Redis(self.cluster.bastion, tunnel, ip, port)

    def sentinel_clients(self, port=26379):
        tunnels = []

        for ip in self.instance_private_ips():
            tunnel = self.cluster.bastion.tunnel(ip, port)
            tunnels.append((ip, tunnel))

        for ip, tunnel in tunnels:
            yield RedisSentinel(self.cluster.bastion, tunnel, ip, port)


# FIXME: Remove once we get rid of the old-style instances
class OldRedisCluster(RedisCluster):
    def __init__(self, dbsilo, *args, **kwargs):
        super(OldRedisCluster, self).__init__(*args, **kwargs)

        self.dbsilo = dbsilo

    def master_hostname(self):
        env = self.cluster.env
        if env == 'prod-old':
            env = 'app'

        return 'redismaster.{}.{}'.format(
            self.dbsilo,
            self.cluster.zone)


class Redis(object):
    def __init__(self, bastion, tunnel, host, port):
        self.host = host
        self.port = port

        self._tunnel = tunnel

        try:
            self._tunnel.open()
        except TunnelDown:
            LOG.exception('failed to open tunnel')
            self._conn = None
        else:
            self._conn = redis.StrictRedis(
                host=self._tunnel.host,
                port=self._tunnel.port,
            )

    def close(self):
        self._tunnel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getattr__(self, key):
        if self._conn:
            return getattr(self._conn, key)
        else:
            raise ConnectionClosed

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)


class RedisSentinel(Redis):
    def __init__(self, bastion, tunnel, host, port):
        super(RedisSentinel, self).__init__(bastion, tunnel, host, port)
