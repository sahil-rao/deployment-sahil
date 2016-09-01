import health_check.base
import health_check.mongo
import health_check.redis


def check_dbsilo(bastion, fqdn, cluster, region, dbsilo, services=None):
    if services is None:
        services = ('mongo', 'redis')

    dbsilo_checklist = health_check.base.HealthCheckList(
            description=dbsilo.upper() + " Health Checklist")

    if 'mongo' in services:
        dbsilo_checklist.add_check(
            health_check.mongo.check_mongodb(
                bastion,
                cluster,
                region,
                dbsilo))

    if 'redis' in services:
        dbsilo_checklist.add_check(
                health_check.redis.check_redis(
                    bastion,
                    fqdn,
                    cluster,
                    region,
                    dbsilo))

    return dbsilo_checklist
