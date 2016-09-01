from __future__ import absolute_import

from .aws import AWSNameHealthCheck
from .base import HealthCheck, HealthCheckList
import sys
import termcolor


class ElasticsearchHealthCheck(HealthCheck):
    def close(self):
        for host in self.hosts:
            host.close()

    def check_host(self, host):
        return self.check_es_host(host)

    def check_es_host(self, host):
        raise NotImplementedError


class ElasticsearchVersionCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch versions match"

    def check_es_host(self, host):
        version = host.version()

        self.host_msgs[host] = 'version: {}'.format(version)

        return version and \
            self.all_equal(host.version() for host in self.hosts)


class ElasticsearchClusterHealthCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch cluster health is green"

    def check_es_host(self, host):
        health = host.health()

        self.host_msgs[host] = 'status:{} nodes:{}/{} cluster:{}'.format(
            health['status'],
            health['number_of_nodes'],
            health['number_of_data_nodes'],
            health['cluster_name'],
        )

        if health['status'] != 'green':
            return False

        if health['number_of_nodes'] != len(self.hosts):
            return False

        return health['status'] == 'green' and \
            self.all_equal(host.health() for host in self.hosts)


class ElasticsearchClusterOddCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch cluster node count is odd"

    def check_es_host(self, host):
        health = host.health()

        if health['number_of_nodes'] % 2 == 0:
            self.host_msgs[host] = 'not odd'
            return False

        return True


class ElasticsearchClusterNodesCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch cluster nodes can see each other"

    def check_es_host(self, host):
        self.host_msgs[host] = ','.join(sorted(host.nodes()))

        expected_hosts = set('{}:{}'.format(h.host, h.port) for h in self.hosts)

        return expected_hosts == host.nodes() and \
            self.all_equal(h.nodes() for h in self.hosts)


def check_elasticsearch(dbsilo):
    es_checklist = HealthCheckList("Elasticsearch Cluster Health Checklist")

    es_instances = list(dbsilo.elasticsearch_instances())
    es_servers = list(dbsilo.elasticsearch_clients())

    if not es_servers:
        print >> sys.stderr, \
            termcolor.colored('WARNING:', 'yellow'), \
            'no elasticsearch servers found in', dbsilo

        return es_checklist

    for check in (
            AWSNameHealthCheck(es_instances),

            ElasticsearchVersionCheck(es_servers),
            ElasticsearchClusterHealthCheck(es_servers),
            ElasticsearchClusterNodesCheck(es_servers),
            ElasticsearchClusterOddCheck(es_servers),
            ):
        es_checklist.add_check(check)

    return es_checklist
