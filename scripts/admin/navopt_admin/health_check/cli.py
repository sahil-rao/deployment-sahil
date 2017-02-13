#!/usr/bin/env python

from __future__ import absolute_import

from . import base
from . import elasticsearch
from . import mongo
from . import redis
from ..elasticsearch import ElasticsearchCluster
from ..mongo import MongoCluster, OldMongoCluster
from ..redis import RedisCluster, OldRedisCluster
import click
import operator
import re


@click.command('health-check')
@click.argument('services', nargs=-1)
@click.pass_context
def health_check(ctx, services):
    if ctx.obj['env'] in ['alpha', 'prod-old']:
        return _old_health_check(ctx, services)
    else:
        return _new_health_check(ctx, services)


def _old_health_check(ctx, services):
    cluster = ctx.obj['cluster']

    if cluster.env == 'alpha':
        dbsilos = ['dbsilo1', 'dbsilo2']
    else:
        dbsilos = ['dbsilo1', 'dbsilo2', 'dbsilo3']

    instances = {}

    if services:
        for service in services:
            m = re.match(r'^dbsilo\*-mongo', service)
            if m:
                for dbsilo_name in dbsilos:
                    dbsilo = cluster.dbsilo(dbsilo_name)
                    instances.setdefault(dbsilo_name, []).extend(
                        dbsilo.mongo_instances())

            m = re.match(r'^(dbsilo\d+)-mongo', service)
            if m:
                dbsilo_name = m.group(1)
                dbsilo = cluster.dbsilo(dbsilo_name)
                instances.setdefault(dbsilo_name, []).extend(
                    dbsilo.mongo_instances())

            m = re.match(r'^dbsilo\*-redis', service)
            if m:
                for dbsilo_name in dbsilos:
                    dbsilo = cluster.dbsilo(dbsilo_name)
                    instances.setdefault(dbsilo_name, []).extend(
                        dbsilo.redis_instances())

            m = re.match(r'^(dbsilo\d+)-redis', service)
            if m:
                dbsilo_name = m.group(1)
                dbsilo = cluster.dbsilo(dbsilo_name)
                instances.setdefault(dbsilo_name, []).extend(
                    dbsilo.redis_instances())

            m = re.match(r'^dbsilo\*-elasticsearch', service)
            if m:
                for dbsilo_name in dbsilos:
                    dbsilo = cluster.dbsilo(dbsilo_name)
                    instances.setdefault(dbsilo_name, []).extend(
                        dbsilo.elasticsearch_instances())

            m = re.match(r'^(dbsilo\d+)-elasticsearch', service)
            if m:
                dbsilo_name = m.group(1)
                dbsilo = cluster.dbsilo(dbsilo_name)
                instances.setdefault(dbsilo_name, []).extend(
                   dbsilo.elasticsearch_instances())
    else:
        for dbsilo in dbsilos:
            dbsilo = cluster.dbsilo(dbsilo)
            instances.setdefault(dbsilo, []).extend(
                dbsilo.mongo_instances())
            instances.setdefault(dbsilo, []).extend(
                dbsilo.redis_instances())
            instances.setdefault(dbsilo, []).extend(
                dbsilo.elasticsearch_instances())

    cluster_checklist = base.HealthCheckList(
        "navopt cluster health checklist")

    cluster_checklist.open()

    try:
        for dbsilo, instances in sorted(instances.iteritems()):
            instances.sort(key=operator.attrgetter('name'))

            services = {}
            for instance in instances:
                key = (instance.service, instance.service_type)
                services.setdefault(key, []).append(instance)

            for (service, service_type), instances in sorted(services.iteritems()):
                if service_type == 'elasticsearch':
                    es_cluster = ElasticsearchCluster(cluster, service, instances)
                    cluster_checklist.add_check(
                        elasticsearch.check_elasticsearch(es_cluster))

                elif service_type == 'mongo':
                    mongo_cluster = OldMongoCluster(dbsilo, cluster, service, instances)
                    cluster_checklist.add_check(mongo.check_mongo(mongo_cluster))

                elif service_type == 'redis':
                    redis_cluster = OldRedisCluster(dbsilo, cluster, service, instances)
                    cluster_checklist.add_check(redis.check_redis(redis_cluster))

        cluster_checklist.execute()
    finally:
        cluster_checklist.close()


def _new_health_check(ctx, services):
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
