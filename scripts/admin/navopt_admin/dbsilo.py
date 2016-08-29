from __future__ import absolute_import

from .elasticsearch import Elasticsearch
from .instance import format_instances
from .mongo import Mongo
from .redis import Redis, RedisSentinel
from .util import COMMA_SEPARATED_LIST_TYPE, prompt
from itertools import chain
import click
import pprint


class DBSilo(object):
    def __init__(self, cluster, name):
        self.cluster = cluster
        self.name = name

    def instances(self, Filters=()):
        return chain(
            self.mongo_instances(),
            self.redis_instances(),
            self.elasticsearch_instances())

    def mongo_instances(self):
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
            'dbsilo1': 'DBSILO1',
            'dbsilo2': 'DBSILO2',
            'dbsilo3': 'DBSILO3',
            'dbsilo4': 'DBSILO4',
        }

        filters = [
            '{}-mongo'.format(self.name),
            '{}-mongo-*'.format(self.name),
        ]

        if self.cluster.env in ('alpha', 'app'):
            filters.extend([
                'MongoDB {} {}'.format(
                    alpha_names[self.cluster.env],
                    alpha_names[self.name]),
                'MONGO_{}_{}'.format(
                    app_names[self.cluster.env],
                    app_names[self.name]),
                'MONGO_{}_{} - Arbiter'.format(
                    app_names[self.cluster.env],
                    app_names[self.name]),
            ])

        return self.cluster.instances_by_tags('DBSilo', filters)

    def mongo_instance_private_ips(self):
        return (instance.private_ip_address
                for instance in self.mongo_instances())

    def mongo_master_hostname(self):
        return 'mongomaster.{}.{}.{}'.format(
            self.name,
            self.cluster.env,
            self.cluster.zone)

    def mongo_master(self):
        master_hostname = self.mongo_master_hostname()
        return Mongo(self.cluster.bastion, master_hostname)

    def mongo_clients(self):
        for ip in self.mongo_instance_private_ips():
            yield Mongo(self.cluster.bastion, ip)

    def redis_instances(self):
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

        filters = [
            '{}-redis'.format(self.name),
        ]

        if self.cluster.env in ('alpha', 'app'):
            filters.extend([
                'Redis {} {}'.format(
                    alpha_names[self.cluster.env],
                    alpha_names[self.name]),
                'REDIS_{}_{}'.format(
                    app_names[self.cluster.env],
                    app_names[self.name]),
            ])

        return chain(
            self.cluster.instances_by_tags('DBSilo', filters),
            self.cluster.instances_by_tags('Service', filters),
        )

    def redis_instance_private_ips(self):
        return (instance.private_ip_address
                for instance in self.redis_instances())

    def redis_master_hostname(self):
        return '{}-redis-master.{}.{}'.format(
            self.name,
            self.cluster.env,
            self.cluster.zone)

    def redis_master(self):
        master_hostname = self.redis_master_hostname()
        return Redis(self.cluster.bastion, master_hostname)

    def redis_clients(self):
        for ip in self.redis_instance_private_ips():
            yield Redis(self.cluster.bastion, ip)

    def redis_sentinel_clients(self):
        for ip in self.redis_instance_private_ips():
            yield RedisSentinel(self.cluster.bastion, ip)

    def elasticsearch_instances(self):
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

        filters = [
            '{}-elasticsearch'.format(self.name),
        ]

        if self.cluster.env in ('alpha', 'app'):
            filters.extend([
                'Elasticsearch {} {}'.format(
                    alpha_names[self.cluster.env],
                    alpha_names[self.name]),
                'Elasticsearch_{}_{}'.format(
                    app_names[self.cluster.env],
                    app_names[self.name]),
            ])

        return self.cluster.instances_by_tags('DBSilo', filters)

    def elasticsearch_instance_private_ips(self):
        return (instance.private_ip_address
                for instance in self.elasticsearch_instances())

    def elasticsearch_clients(self):
        for ip in self.elasticsearch_instance_private_ips():
            yield Elasticsearch(self.cluster.bastion, ip)

    def __str__(self):
        return 'DBSilo({}, {})'.format(self.cluster, self.name)


@click.group()
def cli():
    pass


@cli.command('list-instances')
@click.option('-t', '--type', 'type_name')
@click.option('-f', '--fields', type=COMMA_SEPARATED_LIST_TYPE)
@click.option('-s', '--sort', 'sort_field')
@click.option('--nh', '--no-header', 'show_header',
              is_flag=True,
              flag_value=False,
              default=True,
              )
@click.argument('dbsilo_name', required=True)
@click.pass_context
def list_instances(ctx,
                   type_name,
                   fields,
                   sort_field,
                   show_header,
                   dbsilo_name):
    dbsilo = ctx.obj['cluster'].dbsilo(dbsilo_name)
    instances = list(dbsilo.instances())

    print format_instances(
        instances,
        fields=fields,
        sort_field=sort_field,
        show_header=show_header,
    )


@cli.command()
@click.argument('dbsilo_name', required=True)
@click.argument('capacity', type=int, default=1000)
@click.pass_context
def register(ctx, dbsilo_name, capacity):
    dbsilo = ctx.obj['cluster'].dbsilo(dbsilo_name)

    mongo_ips = sorted(dbsilo.mongo_instance_private_ips())
    redis_ips = sorted(dbsilo.redis_instance_private_ips())
    elasticsearch_ips = sorted(dbsilo.elasticsearch_instance_private_ips())

    proposed_dbsilo_info_data = {
        'mongo': ','.join(mongo_ips),
        'redis': ','.join(redis_ips),
        'elastic': ','.join(elasticsearch_ips),
        'capacitylimit': str(capacity),
        'name': dbsilo_name,
    }

    with dbsilo.redis_master() as redis_master:
        dbsilo_info_metakey = 'dbsilo:metakey:info'
        dbsilo_info_key = 'dbsilo:{}:info'.format(dbsilo_name)
        dbsilo_tenants_metakey = 'dbsilo:metakey:tenants'
        dbsilo_tenants_key = 'dbsilo:{}:tenants'.format(dbsilo_name)

        current_dbsilo_info_data = redis_master.hgetall(dbsilo_info_key)

        print 'current configuration:'
        pprint.pprint(current_dbsilo_info_data)
        print

        print 'proposed configuration:'
        pprint.pprint(proposed_dbsilo_info_data)
        print

        if current_dbsilo_info_data == proposed_dbsilo_info_data:
            print 'configuration unchanged'
            return

        msg = 'are you sure you want to apply? [yes/no]: '
        if not prompt(msg, ctx.obj['yes']):
            ctx.fail('dbsilo unchanged')

        redis_master.hmset(dbsilo_info_key, proposed_dbsilo_info_data)
        redis_master.sadd(dbsilo_info_metakey, dbsilo_info_key)
        redis_master.sadd(dbsilo_tenants_metakey, dbsilo_tenants_key)

        print 'dbsilo modified'
