#!/usr/bin/env python

from __future__ import absolute_import

from . import base
from . import elasticsearch
from . import mongo
from . import redis
from ..elasticsearch import ElasticsearchCluster
from ..mongo import MongoCluster
from ..redis import RedisCluster
import click
import operator


@click.command('health-check')
@click.argument('services', nargs=-1)
@click.pass_context
def health_check(ctx, services):
    cluster = ctx.obj['cluster']

    if services:
        instances = list(cluster.instances_by_services(services))
    else:
        instances = list(cluster.instances())

    instances.sort(key=operator.attrgetter('name'))

    services = {}
    for instance in instances:
        key = (instance.service, instance.service_type)
        services.setdefault(key, []).append(instance)

    cluster_checklist = base.HealthCheckList(
        "navopt cluster health checklist")

    try:
        for (service, service_type), instances in sorted(services.iteritems()):
            if service_type == 'elasticsearch':
                es_cluster = ElasticsearchCluster(cluster, service, instances)
                cluster_checklist.add_check(
                    elasticsearch.check_elasticsearch(es_cluster))

            elif service_type == 'mongo':
                mongo_cluster = MongoCluster(cluster, service, instances)
                cluster_checklist.add_check(mongo.check_mongo(mongo_cluster))

            elif service_type == 'redis':
                redis_cluster = RedisCluster(cluster, service, instances)
                cluster_checklist.add_check(redis.check_redis(redis_cluster))

        cluster_checklist.execute()
    finally:
        cluster_checklist.close()
