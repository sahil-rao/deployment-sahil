from .dbsilo import DBSilo
from .elasticsearch import ElasticsearchCluster
from .instance import Instance, format_instances
from .mongo import MongoCluster
from .redis import RedisCluster
from .ssh import Bastion, NoopBastion
from .util import COMMA_SEPARATED_LIST_TYPE
import boto3
import click


class Cluster(object):
    def __init__(self, profile, env, region, zone, bastion=None):
        self.profile = profile
        self.env = env
        self.region = region
        self.zone = zone

        self._bastion_name = bastion

        session = boto3.Session(profile_name=profile)
        self._ec2 = session.resource('ec2', region_name=region)

    @property
    def bastion(self):
        if not hasattr(self, '_bastion'):
            if self._bastion_name is None:
                self._bastion = NoopBastion()
            else:
                self._bastion = Bastion(self._bastion_name)

        return self._bastion

    def instances(self, filters=()):
        for instance in self._ec2.instances.filter(Filters=filters):
            if instance.state['Name'] != 'terminated':
                yield Instance(instance)

    def instances_by_tags(self, tags):
        return self.instances(filters=[
            {
                'Name': 'tag:{}'.format(tag),
                'Values': values,
            }
            for tag, values in tags
        ])

    def instances_by_tag(self, tag, values):
        return self.instances(filters=[
            {
                'Name': 'tag:{}'.format(tag),
                'Values': values,
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running'],
            },
        ])

    def instances_by_name(self, names):
        return self.instances_by_tag('Name', names)

    def instances_by_services(self, services):
        return self.instances_by_tag('Service', services)

    def instances_by_types(self, types):
        return self.instances_by_tag('Type', types)

    def dbsilo(self, dbsilo_name):
        return DBSilo(
            self,
            dbsilo_name,
        )

    def mongo_cluster(self, service_name):
        return MongoCluster(
            self,
            service_name,
            self.instances_by_service(service_name),
        )

    def redis_cluster(self, service_name):
        return RedisCluster(
            self,
            service_name,
            self.instances_by_service(service_name),
        )

    def elasticsearch_cluster(self, service_name):
        return ElasticsearchCluster(
            self,
            service_name,
            list(self.instances_by_services([service_name])),
        )

    def __str__(self):
        return 'Cluster({}, {}, {})'.format(self.env, self.region, self.zone)


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
@click.pass_context
def list_instances(ctx,
                   type_name,
                   fields,
                   sort_field,
                   show_header):
    cluster = ctx.obj['cluster']
    instances = list(cluster.instances())

    print format_instances(
        instances,
        fields=fields,
        sort_field=sort_field,
        show_header=show_header,
    )


@cli.command('terms')
@click.pass_context
def show_terms(ctx):
    with ctx.obj['cluster'].dbsilo('dbsilo1').mongo_master() as mongo:
        for x in mongo['xplainIO'].users.find():
            print x
