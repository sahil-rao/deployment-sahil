#!/usr/bin/env python

from __future__ import absolute_import

from pprint import pprint
import boto3
import click
import functools
import health_check.base
import health_check.dbsilo
import json
import pymongo
import re
import redis
import sshtunnel
import sys
import termcolor
import urllib2


def find_route53_records(resource, dbsilo, cluster_name='alpha', suffix='xplain.io'):
    """Find all relevant resource URLs from Route 53"""

    AWS_METADATA_ENDPOINT = 'http://169.254.169.254/latest/meta-data/'

    resp = urllib2.urlopen(AWS_METADATA_ENDPOINT + 'placement/availability-zone/')
    aws_availability_zone = resp.read()
    aws_region = re.match('(us|sa|eu|ap)-(north|south|central)?(east|west)?-[0-9]+',
                          aws_availability_zone).group(0)

    conn = boto.route53.connect_to_region(aws_region)
    route53_zone = conn.get_zone("{0}.{1}".format(cluster_name, suffix))

    # Match records belonging to the service for particular dbsilo and cluster
    match_regex = "({0}\d+\.{1}\.{2}\.{3}.?)" \
                  .format(resource, dbsilo, cluster_name, suffix)
    resource_records = []
    for record in route53_zone.get_records():
        match = re.search(match_regex, record.name)
        if match:
            resource_records.append(match.group(0))

    return resource_records


def get_mongodb_servers(dbsilo):
    return find_route53_records('mongo', dbsilo)



#    return find_route53_records('redis', dbsilo)

def get_elasticsearch_servers(dbsilo):
    return find_route53_records('elasticsearch', dbsilo)

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
@click.argument('dbsilo')
def cli(bastion, cluster, region, dbsilo):
    try:
        bastion = {
            'navopt-alpha': 'alpha-root.xplain.io',
            'navopt-prod': '52.27.164.215',
        }[bastion]
    except KeyError:
        pass

    cluster_checklist = health_check.base.HealthCheckList("NavOpt Cluster Health Checklist")
    cluster_checklist.add_check(health_check.dbsilo.check_dbsilo(
        bastion,
        cluster,
        region,
        dbsilo))

#    backoffice_checklist = HealthCheckList("Backoffice Health Checklist")
#    backoffice_checklist.add_check(DiskUsageCheck(get_backoffice_servers()))
#    cluster_checklist.add_check(backoffice_checklist)

    cluster_checklist.execute()
