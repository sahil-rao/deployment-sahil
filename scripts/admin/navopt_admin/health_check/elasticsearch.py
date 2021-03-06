from __future__ import absolute_import

from .aws import AWSNameHealthCheck
from .base import HealthCheck, HealthCheckList
from ..elasticsearch import ConnectionClosed
import sys
import termcolor
import collections


class ElasticsearchHealthCheck(HealthCheck):
    def open(self):
        for host in self.hosts:
            host.open()

    def close(self):
        for host in self.hosts:
            host.close()

    def check_host(self, host):
        if host.is_connected():
            try:
                return self.check_es_host(host)
            except ConnectionClosed:
                pass

        if host in self.host_msgs:
            self.host_msgs[host] += ' CANNOT CONNECT'
        else:
            self.host_msgs[host] = 'CANNOT CONNECT'

        return False

    def check_es_host(self, host):
        raise NotImplementedError


class ElasticsearchVersionCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch versions match"

    def check_es_host(self, host):
        version = host.version()

        self.host_msgs[host] = 'version: {}'.format(version)

        if not version:
            return False

        for h in self.hosts:
            if not h.is_connected() or h.version() != version:
                return False

        return True


class ElasticsearchClusterHealthCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch cluster health is green"

    def check_es_host(self, host):
        health = host.cluster.health()

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

        return status and self.all_equal(
            host.cluster.health() for host in self.hosts)


class ElasticsearchClusterNodesCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch cluster nodes can see each other"

    def check_es_host(self, host):
        self.host_msgs[host] = ','.join(sorted(host.nodes()))

        expected_hosts = set('{}:{}'.format(h.host, h.port) for h in self.hosts)

        return expected_hosts == host.nodes() and \
            self.all_equal(h.nodes() for h in self.hosts)


class ElasticsearchClusterIndexCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch indexes are healthy"

    def check_es_host(self, host):
        quorum = host.minimum_master_nodes()
        health = host.cluster.health(level='indices')
        indices = health['indices']
        self.host_msgs[host] = 'indices:{}'.format(len(indices))

        result = True

        number_of_shards = collections.defaultdict()
        relocating_shards = collections.defaultdict()
        initializing_shards = collections.defaultdict()
        unassigned_shards = collections.defaultdict()
        number_of_replicas = collections.defaultdict()

        for name, index in indices.iteritems():
            status = index['status']
            number_of_shards = index['number_of_shards']
            relocating_shards = index['relocating_shards']
            initializing_shards = index['initializing_shards']
            unassigned_shards = index['unassigned_shards']
            number_of_replicas = index['number_of_replicas']

            msgs = []

            if status != 'green':
                result = False
                self.host_msgs[host] += ' status:{}'.format(status)

            if relocating_shards != 0:
                result = False
                msgs.append('relocating:{}'.format(relocating_shards))

            if initializing_shards != 0:
                result = False
                msgs.append('initializing:{}'.format(initializing_shards))

            if unassigned_shards != 0:
                result = False
                msgs.append('unassigned:{}'.format(unassigned_shards))

            if number_of_replicas + 1 < quorum:
                result = False
                msgs.append('replicas:{}'.format(number_of_replicas))

            if msgs:
                self.host_msgs[host] += '\nindex:{} - shards:{} {}'.format(
                    name,
                    number_of_shards,
                    ' '.join(msgs),
                )

        return result


class ElasticsearchShardHealthCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch shards are on every instance version"

    def check_es_host(self, host):
        health = host.cluster.health()

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

        return status and self.all_equal(
            host.cluster.health() for host in self.hosts)


class ElasticsearchQuorumCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch quorum >= master nodes / 2 + 1"

    def check_es_host(self, host):
        quorum = host.minimum_master_nodes()

        node_counts = host.cluster.stats()['nodes']['count']
        master_nodes = node_counts['master_only'] + node_counts['master_data']
        min_masters = master_nodes / 2 + 1

        self.host_msgs[host] = 'quorum:{} masters:{} min-masters:{}'.format(
            quorum,
            master_nodes,
            min_masters)

        return quorum >= min_masters


class ElasticsearchAgreeOnMasterCheck(ElasticsearchHealthCheck):
    description = "Elasticsearch nodes agree on the same master"

    def __init__(self, es_cluster, *args, **kwargs):
        super(ElasticsearchAgreeOnMasterCheck, self).__init__(*args, **kwargs)

        self.es_cluster = es_cluster

    def check_es_host(self, host):
        if host.is_master():
            self.host_msgs[host] = '(master)'
            return self.check_master_hostname(host)

        master_address = host.master_address()
        self.host_msgs[host] = 'master: {}'.format(master_address)

        for h in self.hosts:
            if h.is_connected():
                if master_address != h.master_address():
                    return False
            else:
                return False

        return True

    def check_master_hostname(self, host):
        master_hostname = self.es_cluster.master_hostname()
        found_host = self.es_cluster.cluster.bastion.resolve_hostname(
            master_hostname)

        if not found_host:
            self.host_msgs[host] += ' failed to resolve: ' + master_hostname
            return False

        if host.host != found_host:
            self.host_msgs[host] += \
                ' master url resolves to {}'.format(found_host)
            return False
        else:
            return True


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
            ElasticsearchClusterIndexCheck(es_servers),
            ElasticsearchShardHealthCheck(es_servers),
            ElasticsearchQuorumCheck(es_servers),
            ElasticsearchAgreeOnMasterCheck(es_cluster, es_servers),
            ):
        es_checklist.add_check(check)

    return es_checklist
