from __future__ import absolute_import

import redis


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
