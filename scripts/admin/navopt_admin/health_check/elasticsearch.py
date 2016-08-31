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

        self.host_msgs[host] = 'status:{} cluster:{}'.format(
            health['status'],
            health['cluster_name'],
        )

        status = True

        if health['status'] != 'green':
            status = False

        if health['number_of_nodes'] != len(self.hosts) or \
                health['number_of_data_nodes'] != len(self.hosts):

            self.host_msgs[host] += ' nodes:{}/{}'.format(
                health['number_of_nodes'],
                len(self.hosts),
            )
            status = False

        if health['unassigned_shards'] != 0:
            self.host_msgs[host] += ' shards:{}/{}'.format(
                health['active_shards'],
                health['unassigned_shards'] + health['active_shards'],
            )
            status = False

        return status and self.all_equal(host.health() for host in self.hosts)


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


def check_elasticsearch(es_cluster):
    es_checklist = HealthCheckList(
        "{} cluster health checklist".format(es_cluster.service))

    es_servers = list(es_cluster.clients())

    if not es_servers:
        print >> sys.stderr, \
            termcolor.colored('WARNING:', 'yellow'), \
            'no elasticsearch servers found in', es_cluster.service

        return es_checklist

    for check in (
            AWSNameHealthCheck(es_cluster.instances),

            ElasticsearchVersionCheck(es_servers),
            ElasticsearchClusterHealthCheck(es_servers),
            ElasticsearchClusterNodesCheck(es_servers),
            ElasticsearchClusterOddCheck(es_servers),
            ):
        es_checklist.add_check(check)

    return es_checklist
