from .dbsilo import DBSilo
from .ssh import Bastion
from .instance import (
    Instance,
    format_instances,
)
from .util import COMMA_SEPARATED_LIST_TYPE
import boto3
import click


class Cluster(object):
    def __init__(self, env, region, zone, bastion=None):
        self.env = env
        self.region = region
        self.zone = zone

        self._bastion_name = bastion
        self._bastion = None

        self._ec2 = boto3.resource('ec2', region_name=region)

    @property
    def bastion(self):
        if self._bastion is None:
            if self._bastion_name is None:
                raise Exception('bastion is not configured')

            self._bastion = Bastion(self._bastion_name)

        return self._bastion

    def instances(self, Filters=()):
        return (
            Instance(instance)
            for instance in self._ec2.instances.filter(Filters=Filters)
        )

    def instances_by_tags(self, tag, values):
        return self.instances(Filters=[
            {
                'Name': 'tag:{}'.format(tag),
                'Values': values,
            }
        ])

    def dbsilo(self, dbsilo_name):
        return DBSilo(
            self,
            dbsilo_name,
        )


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
    cluster = Cluster(ctx.obj['region'])
    instances = list(cluster.instances())

    print format_instances(
        instances,
        fields=fields,
        sort_field=sort_field,
        show_header=show_header,
    )
