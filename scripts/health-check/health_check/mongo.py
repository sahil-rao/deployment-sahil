from __future__ import absolute_import

from health_check.base import HealthCheck


class MongoClusterConfigurationCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.description = "Mongo instance's replica set view has one primary and two secondaries"

    def check_host(self, host):
        mconn = pymongo.MongoClient(host)
        repl_status = mconn.admin.command('replSetGetStatus')
        num_primaries = 0
        num_secondaries = 0
        num_otherstate = 0
        for member in repl_status['members']:
            if member['state'] == 1:
                num_primaries += 1
            elif member['state'] == 2:
                num_secondaries += 1
            else:
                num_otherstate += 1

        return num_primaries == 1 and num_secondaries == 2 and num_otherstate == 0


class MongoClusterConfigVersionsCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.description = "Config version of all replica set members match"

    def check_host(self, host):
        mconn = pymongo.MongoClient(host)
        repl_status = mconn.admin.command('replSetGetStatus')
        config_versions = []
        for member in repl_status['members']:
            config_versions.append(member['configVersion'])

        return len(set(config_versions)) <= 1


class MongoClusterHeartbeatCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.description = "Last heartbeat received is recent"

    def check_host(self, host):
        mconn = pymongo.MongoClient(host)
        repl_status = mconn.admin.command('replSetGetStatus')


def check_mongodb(dbsilo):
    mongodb_checklist = HealthCheckList("MongoDB Cluster Health Checklist")
    for klass in (MongoClusterConfigurationCheck, MongoClusterConfigVersionsCheck, DiskUsageCheck):
        mongodb_checklist.add_check(klass(get_mongodb_servers(dbsilo)))
    dbsilo_checklist.add_check(mongodb_checklist)
