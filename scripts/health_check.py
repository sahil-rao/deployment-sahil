#!/usr/bin/env python

import json
import sys
import re
import urllib2
import ConfigParser
from pprint import pprint
import paramiko
import boto.route53
import redis
import pymongo


def find_route53_records(resource, dbsilo_name, cluster_name='alpha', suffix='xplain.io'):
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
                  .format(resource, dbsilo_name, cluster_name, suffix)
    resource_records = []
    for record in route53_zone.get_records():
        match = re.search(match_regex, record.name)
        if match:
            resource_records.append(match.group(0))

    return resource_records

def get_mongodb_servers(dbsilo_name):
    return find_route53_records('mongo', dbsilo_name)

def get_redis_servers(dbsilo_name):
    return find_route53_records('redis', dbsilo_name)

def get_elasticsearch_servers(dbsilo_name):
    return find_route53_records('elasticsearch', dbsilo_name)

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


# Terminal codes for colors to make things pretty
class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


# Subclass this to make a new check
class HealthCheck(object):

    def __init__(self, hosts, description=""):
        self.hosts = hosts
        self.description = description

    def execute(self, tabs=1):
        """Return True if healthcheck passed on all hosts"""
        host_statuses = []
        for host in self.hosts:
            status = self.check_host(host)
            host_statuses.append(status)
        return all(host_statuses)

    def check_host(self, host):
        """Return True if healthcheck passed no host"""
        raise NotImplementedError



# Executes all healthchecks added to the checklist; Checklists may be composed
class HealthCheckList(object):

    def __init__(self, description):
        self.health_checks = []
        self.description = description

    def add_check(self, healthcheck):
        self.health_checks.append(healthcheck)

    def execute(self, tabs=1):
        print ""
        print "\t" * (tabs-1), color.BLUE, color.BOLD, "Executing checklist: ", self.description, color.END, color.END
        print "\t" * (tabs-1), " ", len(self.health_checks), "checks to execute in the checklist:"
        healthcheck_statuses = []
        for i, healthcheck in enumerate(self.health_checks):
            status = healthcheck.execute(tabs + 1)
            if isinstance(healthcheck, HealthCheck):
                if status is True:
                    print "\t" * tabs, str(i+1) + ")", color.BOLD, color.GREEN, "PASSED", color.END, ":", color.BOLD, healthcheck.description, color.END
                else:
                    print "\t" * tabs, str(i+1) + ")", color.BOLD, color.RED, "FAILED", color.END, ":", color.BOLD, healthcheck.description, color.END
                for host in healthcheck.hosts:
                    if healthcheck.check_host(host) == True:
                        print "\t" * (tabs+1), "PASSED\t" + host
                    else:
                        print "\t" * (tabs+1), "FAILED\t" + host

            healthcheck_statuses.append(status)

        status = all(healthcheck_statuses)
        if status is True:
            print "\t" * (tabs-1), color.GREEN, color.BOLD, "PASSED", color.END, color.END, "Checklist:", color.UNDERLINE + self.description + color.END
        else:
            print "\t" * (tabs-1), color.RED, color.BOLD, "FAILED", color.END, color.END, "Checklist:", color.UNDERLINE + self.description + color.END

        return status


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



class DiskUsageCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.description = "Disk usage on all drives is < 80%"

    def check_host(self, host):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username="ubuntu")
        stdin, stdout, stderr = client.exec_command("df -hP | awk 'NR>1{print $1,$5}' | sed -e's/%//g'")
        for line in stdout.readlines():
            drive, percent_full = line.strip().split()
            if int(percent_full) > 80:
                return False
        return True


class RedisHealthCheck(HealthCheck):

    def __init__(self, hosts):
        self.hosts = hosts
        self.redis_info = {}
        for host in self.hosts:
            rconn = redis.StrictRedis(host=host)
            self.redis_info[host] = rconn.info()

    def check_host(self, host):
        raise NotImplementedError

class RedisNoBlockedClientsCheck(RedisHealthCheck):

    def __init__(self, hosts):
        RedisHealthCheck.__init__(self, hosts)
        self.description = "No currently blocked clients"

    def check_host(self, host):
        return self.redis_info[host]['blocked_clients'] == 0

class RedisRdbBackupCheck(RedisHealthCheck):

    def __init__(self, hosts):
        RedisHealthCheck.__init__(self, hosts)
        self.description = "RDB backup successfully saved to disk"

    def check_host(self, host):
        return self.redis_info[host]['rdb_last_bgsave_status'] == 'ok'

class RedisAofDisabledCheck(RedisHealthCheck):

    def __init__(self, hosts):
        RedisHealthCheck.__init__(self, hosts)
        self.description = "AOF backups are disabled"

    def check_host(self, host):
        return self.redis_info[host]['aof_enabled'] == 0

class RedisMemoryUsageCheck(RedisHealthCheck):

    def __init__(self, hosts):
        RedisHealthCheck.__init__(self, hosts)
        self.description = "Redis memory usage is normal"

    def check_host(self, host):
        """Redis memory usage is < 30 gb"""
        return self.redis_info[host]['used_memory'] < 30000000000

class RedisClusterConfigurationCheck(RedisHealthCheck):

    def __init__(self, hosts):
        RedisHealthCheck.__init__(self, hosts)
        self.description = "Redis cluster has one master and two connected slaves"

    def check_host(self, host):
        if self.redis_info[host]['role'] == 'master':
            return self.redis_info[host]['connected_slaves'] == 2
        if self.redis_info[host]['role'] == 'slave':
            return self.redis_info[host]['master_link_status'] == 'up'



def main():

    cluster_checklist = HealthCheckList("NavOpt Cluster Health Checklist")

    for dbsilo_name in ("dbsilo1", "dbsilo2"):

        dbsilo_checklist = HealthCheckList(dbsilo_name.upper() + " Health Checklist")

        mongodb_checklist = HealthCheckList("MongoDB Cluster Health Checklist")
        for klass in (MongoClusterConfigurationCheck, MongoClusterConfigVersionsCheck, DiskUsageCheck):
            mongodb_checklist.add_check(klass(get_mongodb_servers(dbsilo_name)))
        dbsilo_checklist.add_check(mongodb_checklist)

        redis_checklist = HealthCheckList("Redis Cluster Health Checklist")
        for klass in (RedisNoBlockedClientsCheck, RedisRdbBackupCheck, RedisAofDisabledCheck, RedisMemoryUsageCheck, RedisClusterConfigurationCheck, DiskUsageCheck):
            redis_checklist.add_check(klass(get_redis_servers(dbsilo_name)))
        dbsilo_checklist.add_check(redis_checklist)

        cluster_checklist.add_check(dbsilo_checklist)

    backoffice_checklist = HealthCheckList("Backoffice Health Checklist")
    backoffice_checklist.add_check(DiskUsageCheck(get_backoffice_servers()))
    cluster_checklist.add_check(backoffice_checklist)

    cluster_checklist.execute()

if __name__ == "__main__":
    main()
