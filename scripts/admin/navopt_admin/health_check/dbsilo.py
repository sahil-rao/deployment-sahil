from __future__ import absolute_import

from . import base
from . import elasticsearch
from . import mongo
from . import redis


def check_dbsilo(dbsilo, services=None):
    if services is None:
        services = ('mongo', 'redis', 'elasticsearch')

    dbsilo_checklist = base.HealthCheckList(
            description=dbsilo.name.upper() + " Health Checklist")

    if 'mongo' in services:
        dbsilo_checklist.add_check(mongo.check_mongodb(dbsilo))

    if 'redis' in services:
        dbsilo_checklist.add_check(redis.check_redis(dbsilo))

    if 'elasticsearch' in services or 'es' in services:
        dbsilo_checklist.add_check(elasticsearch.check_elasticsearch(dbsilo))

    return dbsilo_checklist
