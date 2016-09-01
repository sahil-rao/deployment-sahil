from __future__ import absolute_import

from .redis import Redis
from .instance import format_instances
from .util import COMMA_SEPARATED_LIST_TYPE, prompt
from itertools import chain
import click
import pprint


class DBSilo(object):
    def __init__(self, cluster, dbsilo_name):
        self._cluster = cluster
        self._dbsilo_name = dbsilo_name

    def instances(self, Filters=()):
        return chain(
            self.mongo_instances(),
            self.redis_instances(),
            self.elasticsearch_instances())

    def mongo_instances(self):
        return self._cluster.instances_by_tags(
            'DBSilo',
            ['{}-mongo'.format(self._dbsilo_name)],
        )

    def mongo_instance_private_ips(self):
        return (instance.private_ip_address
                for instance in self.mongo_instances())

    def redis_instances(self):
        return self._cluster.instances_by_tags(
            'DBSilo',
            ['{}-redis'.format(self._dbsilo_name)],
        )

    def redis_instance_private_ips(self):
        return (instance.private_ip_address
                for instance in self.redis_instances())

    def elasticsearch_instances(self):
        return self._cluster.instances_by_tags(
            'DBSilo',
            ['{}-elasticsearch'.format(self._dbsilo_name)],
        )

    def elasticsearch_instance_private_ips(self):
        return (instance.private_ip_address
                for instance in self.elasticsearch_instances())

    def redis_master(self):
        if self._cluster.bastion is None:
            raise Exception('bastion is not configured')

        master_hostname = 'redismaster.{}.{}.{}'.format(
            self._dbsilo_name,
            self._cluster.env,
            self._cluster.zone)

        return Redis(self._cluster.bastion, master_hostname)


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
        if not prompt(msg, ctx.obj['YES']):
            ctx.fail('dbsilo unchanged')

        redis_master.hmset(dbsilo_info_key, proposed_dbsilo_info_data)
        redis_master.sadd(dbsilo_info_metakey, dbsilo_info_key)
        redis_master.sadd(dbsilo_tenants_metakey, dbsilo_tenants_key)

        print 'dbsilo modified'
