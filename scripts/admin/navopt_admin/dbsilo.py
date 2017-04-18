from __future__ import absolute_import

from .elasticsearch import ElasticsearchCluster
from .instance import format_instances
from .mongo import MongoCluster, OldMongoCluster
from .redis import RedisCluster, OldRedisCluster
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

    @property
    def mongo_service(self):
        return self.name + '-mongo'

    def mongo_instances(self):
        # FIXME: remove after we get rid of the old-style instances
        if self.cluster.env in ('alpha', 'prod-old'):
            alpha_names = {
                'alpha': 'Alpha',
                'app': 'App',
                'prod-old': 'App',
                'dbsilo1': 'DBSilo1',
                'dbsilo2': 'DBSilo2',
                'dbsilo3': 'DBSilo3',
                'dbsilo4': 'DBSilo4',
            }

            app_names = {
                'alpha': 'ALPHA',
                'app': 'APP',
                'prod-old': 'App',
                'dbsilo1': 'DBSILO1',
                'dbsilo2': 'DBSILO2',
                'dbsilo3': 'DBSILO3',
                'dbsilo4': 'DBSILO4',
            }

            # FIXME: remove after we get rid of the old instances
            env = self.cluster.env
            if env == 'prod-old':
                env = 'app'

            filters = [
                '{}-{}-mongo-*'.format(env, self.name),
                'MongoDB {} {}'.format(
                    alpha_names[env],
                    alpha_names[self.name]),
                'MONGO_{}_{}'.format(
                    app_names[self.cluster.env].upper(),
                    app_names[self.name].upper()),
                'MONGO_{}_{} - Arbiter'.format(
                    app_names[env].upper(),
                    app_names[self.name].upper()),
                'MONGO_{}_{} - Arbiter'.format(
                    app_names[env],
                    app_names[self.name]),
            ]

            return self.cluster.instances_by_name(filters)
        else:
            return self.cluster.instances_by_services([self.mongo_service])

    def mongo_cluster(self):
        # FIXME: remove after we get rid of the old-style instances
        if self.cluster.env in ('alpha', 'prod-old'):
            return OldMongoCluster(
                self.name,
                self.cluster,
                self.mongo_service,
                list(self.mongo_instances()))
        else:
            return MongoCluster(
                self.cluster,
                self.mongo_service,
                list(self.mongo_instances()))

    @property
    def redis_service(self):
        return self.name + '-redis'

    def redis_instances(self):
        if self.cluster.env == 'alpha':
            alpha_names = {
                'alpha': 'Alpha',
                'app': 'App',
                'prod-old': 'App',
                'prod': 'App',
                'dbsilo1': 'DBSilo1',
                'dbsilo2': 'DBSilo2',
                'dbsilo3': 'DBSilo3',
                'dbsilo4': 'DBSilo4',
            }

            app_names = {
                'alpha': 'ALPHA',
                'app': 'APP',
                'prod-old': 'APP',
                'prod': 'APP',
                'dbsilo1': 'DBSILO_1',
                'dbsilo2': 'DBSILO_2',
                'dbsilo3': 'DBSILO_3',
                'dbsilo4': 'DBSILO_4',
            }

            # FIXME: remove after we get rid of the old instances
            env = self.cluster.env
            if env in ('prod-old', 'prod'):
                env = 'app'

            filters = [
                '{}-{}-redis-*'.format(env, self.name),
                'Redis {} {}'.format(
                    alpha_names[self.cluster.env],
                    alpha_names[self.name]),
                'REDIS_{}_{}'.format(
                    app_names[self.cluster.env],
                    app_names[self.name]),
            ]

            return self.cluster.instances_by_name(filters)
        elif self.cluster.env in ('prod-old', 'prod'):
            if self.name == 'dbsilo1':
                filters = ['REDIS_APP_DBSILO_1']
            elif self.name == 'dbsilo2':
                filters = ['REDIS_APP_DBSILO_2']
            else:
                filters = ['app-dbsilo3-redis-*']

            return self.cluster.instances_by_name(filters)
        else:
            filters = [
                '{}-redis'.format(self.name),
            ]

            return self.cluster.instances_by_services([self.redis_service])

    def redis_cluster(self):
        # FIXME: remove after we get rid of the old-style instances
        if self.cluster.env in ('alpha', 'prod-old', 'prod'):
            return OldRedisCluster(
                self.name,
                self.cluster,
                self.redis_service,
                list(self.redis_instances()))
        else:
            return RedisCluster(
                self.cluster,
                self.redis_service,
                list(self.redis_instances()))

    @property
    def elasticsearch_service(self):
        return self.name + '-elasticsearch'

    def elasticsearch_instances(self):
        # FIXME: remove after we get rid of the old instances
        if self.cluster.env == 'alpha':
            alpha_names = {
                'alpha': 'Alpha',
                'app': 'App',
                'prod-old': 'App',
                'prod': 'App',
                'dbsilo1': 'DBSilo1',
                'dbsilo2': 'DBSilo2',
                'dbsilo3': 'DBSilo3',
                'dbsilo4': 'DBSilo4',
            }

            app_names = {
                'alpha': 'ALPHA',
                'app': 'APP',
                'prod-old': 'App',
                'prod': 'App',
                'dbsilo1': 'DBSILO_1',
                'dbsilo2': 'DBSILO_2',
                'dbsilo3': 'DBSILO_3',
                'dbsilo4': 'DBSILO_4',
            }

            env = self.cluster.env
            if env in ('prod-old', 'prod'):
                env = 'app'

            filters = [
                '{}-{}-elasticsearch-*'.format(env, self.name),
                'Elasticsearch {} {}'.format(
                    alpha_names[self.cluster.env],
                    alpha_names[self.name]),
                'ElasticSearch_{}_{}'.format(
                    app_names[self.cluster.env].upper(),
                    alpha_names[self.name].upper()),
                'Elasticsearch_{}_{}'.format(
                    app_names[self.cluster.env],
                    app_names[self.name]),
            ]

            return self.cluster.instances_by_name(filters)
        elif self.cluster.env == 'prod-old':
            if self.name == 'dbsilo1':
                filters = ['ElasticSearch_APP_DBSILO1']
            else:
                filters = ['app-{}-elasticsearch-*'.format(self.name)]

            return self.cluster.instances_by_name(filters)
        else:
            return self.cluster.instances_by_services(
                [self.elasticsearch_service])

    def elasticsearch_cluster(self):
        return ElasticsearchCluster(
            self.cluster,
            self.elasticsearch_service,
            list(self.elasticsearch_instances()))

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
    # Routing configuration is stored on dbsilo1
    master_dbsilo = ctx.obj['cluster'].dbsilo('dbsilo1')
    master_redis_cluster = master_dbsilo.redis_cluster()

    dbsilo = ctx.obj['cluster'].dbsilo(dbsilo_name)
    mongo_cluster = dbsilo.mongo_cluster()
    redis_cluster = dbsilo.redis_cluster()
    elasticsearch_cluster = dbsilo.elasticsearch_cluster()

    mongo_ips = sorted(mongo_cluster.instance_private_ips())
    redis_ips = sorted(redis_cluster.instance_private_ips())
    elasticsearch_ips = [elasticsearch_cluster.master_hostname()]

    proposed_dbsilo_info_data = {
        'mongo': ','.join(mongo_ips),
        'redis': ','.join(redis_ips),
        'elastic': ','.join(elasticsearch_ips),
        'capacitylimit': str(capacity),
        'name': dbsilo_name,
    }

    with master_redis_cluster.master() as redis_master:
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
