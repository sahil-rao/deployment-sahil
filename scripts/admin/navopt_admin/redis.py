from __future__ import absolute_import

from .ssh import Tunnel
import redis


class Redis(object):
    def __init__(self, bastion, hostname, port=6379):
        self._tunnel = bastion.tunnel(hostname, port)

        self._conn = redis.StrictRedis(
            host=self._tunnel.local_host,
            port=self._tunnel.local_port,
        )

    def close(self):
        self._tunnel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._tunnel.close()

    def __getattr__(self, key):
        return getattr(self._conn, key)

#    def info(self):
#        return
#        if not hasattr(self, '_info'):
#            self._info = self.rconn.info()
#
#        return self._info
#
#    @property
#    def sentinel_masters(self):
#        if not hasattr(self, '_sentinel_masters'):
#            self._sentinel_masters = self.rconn.sentinel_masters()
#
#        return self._sentinel_masters
#
#    @property
#    def sentinel_info(self):
#        return self.sentinel_masters[self._master_name]
#
#    @property
#    def sentinels(self):
#        if self.rconn is None:
#            return set()
#
#        sentinels = set()
#
#        # Add the current host to the sentinel list.
#        sentinels.add('{}:{}'.format(self.host, self.port))
#
#        sentinels.update(
#            sentinel['name']
#            for sentinel in self.rconn.sentinel_sentinels(self._master_name))
#
#        return sentinels
