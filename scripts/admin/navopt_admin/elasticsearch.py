from __future__ import absolute_import

import elasticsearch


class ElasticsearchCluster(object):
    def __init__(self, cluster, service, instances):
        self.cluster = cluster
        self.service = service
        self.instances = instances

    def instance_private_ips(self):
        for instance in self.instances:
            yield instance.private_ip_address

    def clients(self, port=9200):
        tunnels = []

        for ip in self.instance_private_ips():
            tunnel = self.cluster.bastion.tunnel(ip, port)
            tunnels.append((ip, tunnel))

        for ip, tunnel in tunnels:
            yield Elasticsearch(self.cluster.bastion, tunnel, ip, port)


class Elasticsearch(object):
    def __init__(self, bastion, tunnel, host, port):
        self.host = host
        self.port = port

        self._tunnel = tunnel
        self._tunnel.open()

        self._conn = elasticsearch.Elasticsearch(
            ['{}:{}'.format(self._tunnel.host, self._tunnel.port)],
            use_ssl=False)

    def close(self):
        self._tunnel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._tunnel.close()

    def __getattr__(self, key):
        return getattr(self._conn, key)

    def version(self):
        return self._conn.info()['version']['number']

    def nodes(self):
        nodes = self._conn.nodes.info()['nodes']

        return set(info['http_address'] for info in nodes.itervalues())

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)
