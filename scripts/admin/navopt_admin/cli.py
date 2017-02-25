#!/usr/bin/env python

from __future__ import absolute_import

import click
import logging
import navopt_admin.cluster
import navopt_admin.dbsilo
import navopt_admin.elasticsearch
import navopt_admin.health_check.cli
import navopt_admin.terms
import navopt_admin.user
import sys


@click.group()
@click.option('--profile', 'profile',
              default=None)
@click.option('--env', 'env',
              help='what environment are we inspecting',
              required=True,
              type=click.Choice(['alpha', 'dev', 'stage', 'prod-old', 'prod']))
@click.option('--bastion', 'bastion')
@click.option('--region')
@click.option('--zone', default=None)
@click.option('-y/-n', '--yes/--no', 'assume_yes',
              help='respond yes to all questions',
              default=None)
@click.option('--log-level',
              default='warning',
              type=click.Choice([
                  'critical',
                  'error',
                  'warning',
                  'info',
                  'debug'
              ]))
@click.pass_context
def cli(ctx, profile, env, bastion, region, zone, assume_yes, log_level):
    logging.basicConfig()
    logging.getLogger('navopt_admin').setLevel({
        'critical': logging.CRITICAL,
        'error': logging.error,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
    }[log_level])

    if profile is None:
        profile = {
            'alpha': 'navopt_prod',
            'dev': 'navopt_dev',
            'stage': 'navopt_stage',
            'prod-old': 'navopt_prod',
            'prod': 'navopt_prod',
        }[env]

    if bastion is None:
        bastion = {
            'alpha': 'navopt-alpha',
            'dev': None,
            'stage': 'navopt-stage',
            'prod-old': 'navopt-prod',
            'prod': 'bastion.optimizer.cloudera.com',
        }[env]

    if region is None:
        region = {
            'alpha': 'us-west-1',
            'dev': 'us-west-2',
            'stage': 'us-west-2',
            'prod-old': 'us-west-2',
            'prod': 'us-west-2',
        }[env]

    if zone is None:
        zone = {
            'alpha': 'alpha.xplain.io',
            'dev': 'navopt-dev.cloudera.com',
            'stage': 'stage.xplain.io',
            'prod-old': 'app.xplain.io',
            'prod': 'optimizer.cloudera.com',
        }[env]

    cluster = navopt_admin.cluster.Cluster(
        profile=profile,
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
    click.CommandCollection(
        'elasticsearch',
        sources=[navopt_admin.elasticsearch.cli])
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
