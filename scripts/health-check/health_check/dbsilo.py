import health_check.base
import health_check.mongo
import health_check.redis


def check_dbsilo(bastion, cluster, region, dbsilo):
    dbsilo_checklist = health_check.base.HealthCheckList(
            description=dbsilo.upper() + " Health Checklist")

#    dbsilo_checklist.add_check(
#        health_check.mongo.check_mongodb(
#            bastion,
#            cluster,
#            region,
#            dbsilo))

    dbsilo_checklist.add_check(
            health_check.redis.check_redis(
                bastion,
                cluster,
                region,
                dbsilo))

    return dbsilo_checklist
