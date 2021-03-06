from __future__ import absolute_import

import click
import elasticsearch
import logging
import time
from .ssh import TunnelDown
from .util import prompt

LOG = logging.getLogger(__name__)
TEMPLATE_NAME = 'template_1'


class ConnectionClosed(Exception):
    pass


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

    def master_ip_address(self):
        master_hostname = self.master_hostname()
        return self.cluster.bastion.resolve_hostname(master_hostname)

    def master(self):
        master_address = self.master_ip_address()
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

        try:
            self._tunnel.open()
        except TunnelDown:
            LOG.exception('failed to open tunnel')
            self._conn = None
        else:
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
        if self._conn:
            return getattr(self._conn, key)
        else:
            raise ConnectionClosed

    def conn(self):
        if self._conn:
            return self._conn
        else:
            raise ConnectionClosed

    def version(self):
        return self.conn().info()['version']['number']

    def nodes(self):
        nodes = self.conn().nodes.info()['nodes']

        return set(info['http_address'] for info in nodes.itervalues())

    def master_address(self):
        for node in self.conn().cat.nodes(format='json'):
            if node['master'] == '*':
                return node['ip']

        return None

    def is_master(self):
        return self.master_address() == self.host

    def is_connected(self):
        return self._conn is not None

    def excluded_ips(self):
        excluded_ips = self.conn().cluster.get_settings() \
            .get('transient', {}) \
            .get('cluster', {}) \
            .get('routing', {}) \
            .get('allocation', {}) \
            .get('exclude', {}) \
            .get('_ip')

        if excluded_ips:
            excluded_ips = set(excluded_ips.split(','))
        else:
            excluded_ips = set()

        return excluded_ips

    def minimum_master_nodes(self):
        quorum = self.conn().cluster.get_settings() \
            .get('persistent', {}) \
            .get('discovery', {}) \
            .get('zen', {}) \
            .get('minimum_master_nodes', 1)
        return int(quorum)

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)


@click.group()
def cli():
    pass


@cli.command('change-default-shards')
@click.argument('dbsilo_name', required=True)
@click.argument('shards', type=int)
@click.pass_context
def change_shards(ctx, dbsilo_name, shards):
    if shards < 0:
        ctx.fail('cannot set shards under 0')

    dbsilo = ctx.obj['cluster'].dbsilo(dbsilo_name)

    with dbsilo.elasticsearch_cluster().master() as es_client:
        modified_template = False

        if es_client.indices.exists_template(TEMPLATE_NAME):
            index_template = es_client \
                .indices.get_template(TEMPLATE_NAME)[TEMPLATE_NAME]
            settings = index_template['settings']
            number_of_shards = settings['index'].get('number_of_shards', 0)
            number_of_shards = int(number_of_shards)

            print 'template {} has {} shards'.format(
                TEMPLATE_NAME,
                number_of_shards)

            modified_template = shards != number_of_shards

        else:
            modified_template = True
            index_template = None

        msg = 'are you sure you want to apply? [yes/no]: '
        if not prompt(msg, ctx.obj['yes']):
            ctx.fail('elasticsearch cluster unchanged')

        if modified_template:
            if index_template:
                index_template['settings']['number_of_shards'] = shards
            else:
                index_template = {
                    'template': '*',
                    'order': 0,
                    'settings': {
                        'number_of_shards': shards,
                    },
                }

            es_client.indices.put_template(TEMPLATE_NAME, index_template)

            print 'template modified'


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
@click.argument('service_name', required=True)
@click.argument('quorum', type=int)
@click.pass_context
def change_master_quorum(ctx, service_name, quorum):
    if quorum < 1:
        ctx.fail('cannot set quorum under 1')

    es_cluster = ctx.obj['cluster'].elasticsearch_cluster(service_name)

    with es_cluster.master() as es_client:
        current_quorum = es_client.cluster.get_settings() \
            .get('persistent', {}) \
            .get('discovery', {}) \
            .get('zen', {}) \
            .get('minimum_master_nodes', 1)

        if current_quorum is None:
            print 'no minimum master nodes set'
        else:
            current_quorum = int(current_quorum)
            print 'current quorum:', current_quorum

        if quorum == current_quorum:
            print 'no changes needed'
            return

        node_counts = es_client.cluster.stats()['nodes']['count']
        master_nodes = node_counts['master_only'] + node_counts['master_data']
        print 'master nodes:', master_nodes

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


@cli.command('decommission')
@click.option('--shutdown', is_flag=True, default=False)
@click.argument('service_name', required=True)
@click.argument('ips', nargs=-1)
@click.pass_context
def decommission(ctx, shutdown, service_name, ips):
    cluster = ctx.obj['cluster']
    ips = set(ip for ipset in ips for ip in ipset.split(','))

    if not ips:
        ctx.fail('cannot decommission an empty list')

    elasticsearch_cluster = cluster.elasticsearch_cluster(service_name)

    with elasticsearch_cluster.master() as es_client:
        quorum = es_client.cluster.get_settings() \
            .get('persistent', {}) \
            .get('discovery', {}) \
            .get('zen', {}) \
            .get('minimum_master_nodes', 1)
        quorum = int(quorum)

        excluded_ips = es_client.cluster.get_settings() \
            .get('transient', {}) \
            .get('cluster', {}) \
            .get('routing', {}) \
            .get('allocation', {}) \
            .get('exclude', {}) \
            .get('_ip')

        if excluded_ips:
            instance_ips = set(elasticsearch_cluster.instance_private_ips())
            excluded_ips = set(ip for ip in excluded_ips.split(',')
                               if ip in instance_ips)

            print 'excluded ips are', ' '.join(sorted(excluded_ips))
        else:
            excluded_ips = set()
            print 'no excluded ips'

        if ips == excluded_ips:
            print 'no changes needed'

        for ip in ips:
            if ip not in excluded_ips:
                print 'scheduling %s for decommissioning' % ip
                excluded_ips.add(ip)

        old_instance_count = len(elasticsearch_cluster.instances)
        new_instance_count = old_instance_count - len(excluded_ips)

        if new_instance_count < quorum:
            ctx.fail('cannot reduce instance count below quorum %s' % quorum)

        msg = 'are you sure you want to apply? [yes/no]: '
        if not prompt(msg, ctx.obj['yes']):
            ctx.fail('elasticsearch excluded ips unchanged')

        _update_excluded_ips(es_client, ips)

        print 'waiting for shards to migrate off hosts'
        _migrate_shards(es_client, ips)

        if shutdown:
            _stop_elasticsearch(cluster.bastion, ips)


@cli.command('recommission')
@click.option('--start', is_flag=True, default=False)
@click.argument('service_name', required=True)
@click.argument('ips', nargs=-1)
@click.pass_context
def recommission(ctx, start, service_name, ips):
    cluster = ctx.obj['cluster']
    elasticsearch_cluster = cluster.elasticsearch_cluster(service_name)
    ips = set(ips)

    with elasticsearch_cluster.master() as es_client:
        excluded_ips = es_client.excluded_ips()

        if excluded_ips:
            print 'excluded ips are', ' '.join(sorted(excluded_ips))
        else:
            excluded_ips = set()
            print 'no excluded ips'

        if ips == excluded_ips:
            print 'no changes needed'

        msg = 'are you sure you want to apply? [yes/no]: '
        if not prompt(msg, ctx.obj['yes']):
            ctx.fail('elasticsearch excluded ips unchanged')

        for ip in ips:
            if ip in excluded_ips:
                excluded_ips.remove(ip)

        _update_excluded_ips(es_client, excluded_ips)

        if start:
            _start_elasticsearch(cluster.bastion, ips)


def _update_excluded_ips(es_client, ips):
    es_client.cluster.put_settings({
        'transient': {
            'cluster.routing.allocation.exclude._ip':
                ','.join(sorted(ips)),
        }
    })
    print 'excluded ips changed'


def _migrate_shards(es_client, ips):
    while True:
        ip_shards = {}
        for shard in es_client.cat.shards(h='ip', format='json'):
            ip_shards.setdefault(shard['ip'], []).append(shard)

        migrating = False
        for ip in ips:
            shards = ip_shards.get(ip)
            if shards:
                migrating = True
                print 'ip %s has %s shards' % (ip, len(shards))

        if migrating:
            print 'sleeping'
            time.sleep(10)
        else:
            break


def _stop_elasticsearch(bastion, ips):
    for ip in ips:
        # Shut down our server
        bastion.check_call([
            'ssh',
            ip,
            '/usr/bin/sudo',
            '/usr/bin/service',
            'elasticsearch',
            'stop'])

        print 'server %s stopped' % ip


def _start_elasticsearch(bastion, ips):
    for ip in ips:
        # Shut down our server
        bastion.check_call([
            'ssh',
            ip,
            '/usr/bin/sudo',
            '/usr/bin/service',
            'elasticsearch',
            'start'])

        print 'server %s started' % ip


@cli.command('failover')
@click.argument('service_name', required=True)
@click.argument('ip')
@click.pass_context
def failover(ctx, service_name, ip):
    cluster = ctx.obj['cluster']
    es_cluster = cluster.elasticsearch_cluster(service_name)

    if ip not in es_cluster.instance_private_ips():
        ctx.fail('ip is not in this cluster')

    if ip != es_cluster.master_ip_address():
        ctx.fail('ip is not the master')

    with es_cluster.master() as es_client:
        if ip not in es_client.excluded_ips():
            ctx.fail('ip should be decommissioned first')

    msg = 'are you sure you want to apply? [yes/no]: '
    if not prompt(msg, ctx.obj['yes']):
        ctx.fail('elasticsearch excluded ips unchanged')

    # Restart the server to migrate the master
    cluster.bastion.check_call([
        'ssh',
        ip,
        '/usr/bin/sudo',
        '/usr/bin/service',
        'elasticsearch',
        'restart'])

    print 'server %s failed over' % ip
