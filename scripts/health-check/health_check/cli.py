#!/usr/bin/env python

from __future__ import absolute_import

import click
import health_check.base
import health_check.dbsilo
import health_check.ssh


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


@click.command()
@click.option('-b', '--bastion', default=None)
@click.argument('cluster')
@click.argument('region')
@click.argument('dbsilo', nargs=-1)
def cli(bastion, cluster, region, dbsilo):
    bastion = health_check.ssh.get_config(bastion)['hostname']

    cluster_checklist = health_check.base.HealthCheckList(
        "NavOpt Cluster Health Checklist")

    try:
        for silo in dbsilo:
            cluster_checklist.add_check(health_check.dbsilo.check_dbsilo(
                bastion,
                cluster,
                region,
                silo))

    #    backoffice_checklist = HealthCheckList("Backoffice Health Checklist")
    #    backoffice_checklist.add_check(DiskUsageCheck(get_backoffice_servers()))
    #    cluster_checklist.add_check(backoffice_checklist)

        cluster_checklist.execute()
    finally:
        cluster_checklist.close()
