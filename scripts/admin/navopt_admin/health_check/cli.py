#!/usr/bin/env python

from __future__ import absolute_import

import click
from . import base
from . import dbsilo


# TODO: Make this function real
def get_backoffice_servers():
    return [
        "172.31.5.184",
        "172.31.13.245",
        "172.31.13.244",
        "172.31.13.243",
        "172.31.13.242",
        "172.31.7.45",
        "172.31.7.46",
        "172.31.7.48",
        "172.31.7.50"
    ]


@click.command('health-check')
@click.option('-s', '--services', default=None)
@click.argument('dbsilos', nargs=-1)
@click.pass_context
def health_check(ctx, services, dbsilos):
    cluster_checklist = base.HealthCheckList(
        "NavOpt Cluster Health Checklist")

    if not dbsilos:
        ctx.fail('no dbsilos specified')

    try:
        for dbsilo_name in dbsilos:
            cluster_checklist.add_check(dbsilo.check_dbsilo(
                ctx.obj['cluster'].dbsilo(dbsilo_name),
                services=services))

    #    backoffice_checklist = HealthCheckList("Backoffice Health Checklist")
    #    backoffice_checklist.add_check(DiskUsageCheck(get_backoffice_servers()))
    #    cluster_checklist.add_check(backoffice_checklist)

        cluster_checklist.execute()
    finally:
        cluster_checklist.close()
