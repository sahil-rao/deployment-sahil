from __future__ import absolute_import

from .base import HealthCheck, HealthCheckList
# from .disk import DiskUsageCheck
from .tunnel import Tunnel
import boto3
import elasticsearch
import functools
import multiprocessing.pool
import sys
import termcolor


class Elasticsearch(Tunnel):
    def __init__(self, bastion, hostname, port):
        super(Elasticsearch, self).__init__(bastion, hostname, port)

        if self.tunnel:
            self.conn = elasticsearch.Elasticsearch(
                ['localhost:{}'.format(self.tunnel.local_bind_port)],
                use_ssl=False,
            )
        else:
            self.conn = None

    def version(self):
        if self.conn is None:
            return None

        return self.conn.info()['version']['number']

    def health(self):
        if self.conn is None:
            return None

        return self.conn.cluster.health()

    def nodes(self):
        if self.conn is None:
            return None

        nodes = self.conn.nodes.info()['nodes']

        return set(info['http_address'] for info in nodes.itervalues())


class ElasticsearchHealthCheck(HealthCheck):
    def close(self):
        for host in self.hosts:
            host.close()

    def check_host(self, host):
        if host.conn is None:
            self.host_msgs[host] = 'cannot connect to Elasticsearch'
            return False

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


def check_elasticsearch(bastion, fqdn, cluster, region, dbsilo):
    es_checklist = HealthCheckList("Elasticsearch Cluster Health Checklist")
    es_hostnames = _get_es_hostnames(cluster, region, dbsilo)

    if not es_hostnames:
        print >> sys.stderr, \
            termcolor.colored('WARNING:', 'yellow'), \
            'no elasticsearch servers found in', cluster, region, dbsilo
        return es_checklist

    pool = multiprocessing.pool.ThreadPool(5)

    try:
        es_servers = pool.map(
            functools.partial(_create_es, bastion, 9200),
            es_hostnames)
    finally:
        pool.close()
        pool.join()

    for check in (
            ElasticsearchVersionCheck(es_servers),
            ElasticsearchClusterHealthCheck(es_servers),
            ElasticsearchClusterNodesCheck(es_servers),
            ElasticsearchClusterOddCheck(es_servers),

            # DiskUsageCheck(bastion, hosts=es_hostnames),
            ):
        es_checklist.add_check(check)

    return es_checklist


def _get_es_hostnames(cluster, region, dbsilo):
    alpha_names = {
        'alpha': 'Alpha',
        'app': 'App',
        'dbsilo1': 'DBSilo1',
        'dbsilo2': 'DBSilo2',
        'dbsilo3': 'DBSilo3',
        'dbsilo4': 'DBSilo4',
    }

    app_names = {
        'alpha': 'ALPHA',
        'app': 'APP',
        'dbsilo1': 'DBSILO_1',
        'dbsilo2': 'DBSILO_2',
        'dbsilo3': 'DBSILO_3',
        'dbsilo4': 'DBSILO_4',
    }

    values = [
        '{}-{}-elasticsearch'.format(cluster, dbsilo),
        '{}-{}-elasticsearch-*'.format(cluster, dbsilo),
    ]

    if cluster in ('alpha', 'app'):
        values.extend([
            'Elasticsearch {} {}'.format(
                alpha_names[cluster],
                alpha_names[dbsilo]),
            'Elasticsearch_{}_{}'.format(
                app_names[cluster],
                app_names[dbsilo]),
        ])

    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(Filters=[
        {
            'Name': 'tag:Name',
            'Values': values,
        },
    ])

    hostnames = []
    for instance in instances:
        if instance.private_ip_address:
            hostnames.append(instance.private_ip_address)

    hostnames.sort()

    return hostnames


def _create_es(bastion, port, host):
    return Elasticsearch(bastion, host, port)
