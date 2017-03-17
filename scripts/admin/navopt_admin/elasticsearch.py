from __future__ import absolute_import

import click
import elasticsearch
from .util import prompt

TEMPLATE_NAME = 'template_1'


class ElasticsearchCluster(object):
    def __init__(self, cluster, service, instances):
        self.cluster = cluster
        self.service = service
        self.instances = instances
        self._port = 9200

    def instance_private_ips(self):
        for instance in self.instances:
            yield instance.private_ip_address

    def master_hostname(self):
        return '{}-master.{}'.format(
            self.service,
            self.cluster.zone)

    def master(self):
        master_hostname = self.master_hostname()
        master_address = self.cluster.bastion.resolve_hostname(master_hostname)
        tunnel = self.cluster.bastion.tunnel(master_address, self._port)
        return Elasticsearch(
            self.cluster.bastion,
            tunnel,
            master_address,
            self._port)

    def clients(self):
        tunnels = []

        for ip in self.instance_private_ips():
            tunnel = self.cluster.bastion.tunnel(ip, self._port)
            tunnels.append((ip, tunnel))

        for ip, tunnel in tunnels:
            yield Elasticsearch(self.cluster.bastion, tunnel, ip, self._port)


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

    def master_address(self):
        for node in self._conn.cat.nodes(format='json'):
            if node['master'] == '*':
                return node['ip']

        return None

    def is_master(self):
        return self.master_address() == self.host

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)


@click.group()
def cli():
    pass


@cli.command('change-replicas')
@click.argument('dbsilo_name', required=True)
@click.argument('replicas', type=int)
@click.pass_context
def change_replicas(ctx, dbsilo_name, replicas):
    if replicas < 0:
        ctx.fail('cannot set replicas under 0')

    dbsilo = ctx.obj['cluster'].dbsilo(dbsilo_name)

    with dbsilo.elasticsearch_cluster().master() as es_client:
        modified_template = False

        if es_client.indices.exists_template(TEMPLATE_NAME):
            index_template = es_client \
                .indices.get_template(TEMPLATE_NAME)[TEMPLATE_NAME]
            settings = index_template['settings']
            number_of_replicas = int(settings['index']['number_of_replicas'])

            print 'template {} has {} replicas'.format(
                TEMPLATE_NAME,
                number_of_replicas)

            modified_template = replicas != number_of_replicas

        else:
            modified_template = True
            index_template = None

        indices_to_change = []

        for index in es_client.indices.get('*'):
            settings = es_client.indices.get_settings(index)[index]['settings']
            number_of_replicas = int(settings['index']['number_of_replicas'])

            if replicas != number_of_replicas:
                print '{} has {} replicas'.format(index, number_of_replicas)
                indices_to_change.append(index)

        if not modified_template and not indices_to_change:
            print 'no changes needed'
            return

        msg = 'are you sure you want to apply? [yes/no]: '
        if not prompt(msg, ctx.obj['yes']):
            ctx.fail('elasticsearch cluster unchanged')

        if modified_template:
            if index_template:
                index_template['settings']['number_of_replicas'] = replicas
            else:
                index_template = {
                    'template': '*',
                    'order': 0,
                    'settings': {
                        'number_of_replicas': replicas,
                    },
                }

            es_client.indices.put_template(TEMPLATE_NAME, index_template)

            print 'template modified'

        if indices_to_change:
            es_client.indices.put_settings({
                'index': {
                    'number_of_replicas': replicas,
                },
            })

            print 'indices modified'


@cli.command('change-master-quorum')
@click.argument('dbsilo_name', required=True)
@click.argument('quorum', type=int)
@click.pass_context
def change_master_quorum(ctx, dbsilo_name, quorum):
    if quorum < 1:
        ctx.fail('cannot set quorum under 1')

    dbsilo = ctx.obj['cluster'].dbsilo(dbsilo_name)

    with dbsilo.elasticsearch_cluster().master() as es_client:
        current_quorum = es_client.cluster.get_settings() \
            .get('persistent', {}) \
            .get('discovery', {}) \
            .get('zen', {}) \
            .get('minimum_master_nodes', 1)

        if current_quorum is None:
            print 'no minimum master nodes set'
        else:
            current_quorum = int(current_quorum)
            print 'minimum master nodes is ', current_quorum

        if quorum == current_quorum:
            print 'no changes needed'
            return

        node_counts = es_client.cluster.stats()['nodes']['count']
        master_nodes = node_counts['master_only'] + node_counts['master_data']
        print 'master nodes is', master_nodes

        if quorum < master_nodes / 2 + 1:
            ctx.fail('quorum must be >= master nodes / 2 + 1')

        msg = 'are you sure you want to apply? [yes/no]: '
        if not prompt(msg, ctx.obj['yes']):
            ctx.fail('elasticsearch cluster unchanged')

        es_client.cluster.put_settings({
            'persistent': {
                'discovery.zen.minimum_master_nodes': quorum
            }
        })

        print 'minimum master nodes changed'
