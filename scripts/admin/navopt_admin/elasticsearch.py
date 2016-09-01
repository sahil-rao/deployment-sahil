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

    def clients(self):
        for ip in self.instance_private_ips():
            yield Elasticsearch(self.cluster.bastion, ip)


class Elasticsearch(object):
    def __init__(self, bastion, host, port=9200):
        self.host = host
        self.port = port

        self._tunnel = bastion.tunnel(host, port)
        self._conn = elasticsearch.Elasticsearch(
            ['{}:{}'.format(
                self._tunnel.local_host,
                self._tunnel.local_port,
            )],
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

    def health(self):
        return self._conn.cluster.health()

    def nodes(self):
        nodes = self._conn.nodes.info()['nodes']

        return set(info['http_address'] for info in nodes.itervalues())

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)
