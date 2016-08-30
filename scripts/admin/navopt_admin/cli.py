#!/usr/bin/env python

from __future__ import absolute_import

import click
import navopt_admin.cluster
import navopt_admin.dbsilo
import navopt_admin.health_check.cli
import navopt_admin.terms
import navopt_admin.user
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
    if env not in ['dev', 'stage']:
        ctx.fail('unknown environment `{}`'.format(env))

    if bastion is None:
        bastion = {
            'dev': 'navopt-dev',
            'stage': 'navopt-stage',
        }[env]

    if region is None:
        region = {
            'dev': 'us-west-2',
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

cli.add_command(
    click.CommandCollection('terms', sources=[navopt_admin.terms.cli])
)

cli.add_command(
    click.CommandCollection('user', sources=[navopt_admin.user.cli])
)


if __name__ == '__main__':
    sys.exit(cli())
