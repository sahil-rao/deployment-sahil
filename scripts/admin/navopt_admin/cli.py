#!/usr/bin/env python

from __future__ import absolute_import

import click
import navopt_admin.cluster
import navopt_admin.dbsilo
import navopt_admin.health_check.cli
import sys


@click.group()
@click.option('--env', 'env',
              help='what environment are we inspecting',
              required=True)
@click.option('--bastion', 'bastion')
@click.option('--region')
@click.option('--zone', default='xplain.io')
@click.option('-y/-n', '--yes/--no', 'assume_yes',
              help='respond yes to all questions',
              default=None)
@click.pass_context
def cli(ctx, env, bastion, region, zone, assume_yes):
    if env not in ['stage']:
        ctx.fail('unknown environment `{}`'.format(env))

    if bastion is None:
        bastion = {
            'stage': 'navopt-stage',
        }[env]

    if region is None:
        region = {
            'stage': 'us-west-2',
        }[env]

    cluster = navopt_admin.cluster.Cluster(
        env=env,
        region=region,
        zone=zone,
        bastion=bastion,
    )

    ctx.obj = {
        'cluster': cluster,
        'env': env,
        'bastion': bastion,
        'region': region,
        'zone': zone,
        'yes': assume_yes,
    }


cli.add_command(
    click.CommandCollection('cluster', sources=[navopt_admin.cluster.cli])
)

cli.add_command(
    click.CommandCollection('dbsilo', sources=[navopt_admin.dbsilo.cli])
)

cli.add_command(
    navopt_admin.health_check.cli.health_check
)


if __name__ == '__main__':
    sys.exit(cli())
