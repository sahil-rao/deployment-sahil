from __future__ import absolute_import

import click
import logging
import redis
import time
from .ssh import TunnelDown
from .util import prompt

LOG = logging.getLogger(__name__)


class ConnectionClosed(Exception):
    pass


class UnknownRedisInstance(Exception):
    pass


class RedisCluster(object):
    def __init__(self, cluster, service, instances):
        self.cluster = cluster
        self.service = service
        self.instances = instances

    def master_hostname(self):
        return '{}-master.{}'.format(
            self.service,
            self.cluster.zone)

    def master_ip_address(self):
        return self.cluster.bastion.resolve_hostname(master_hostname)

    def master(self, port=6379):
        master_address = self.master_ip_address()

        tunnel = self.cluster.bastion.tunnel(master_address, port)
        return Redis(self.cluster.bastion, tunnel, master_address, port)

    def instance_private_ips(self):
        for instance in self.instances:
            yield instance.private_ip_address

    def clients(self, port=6379):
        tunnels = []

        for ip in self.instance_private_ips():
            tunnel = self.cluster.bastion.tunnel(ip, port)
            tunnels.append((ip, tunnel))

        for ip, tunnel in tunnels:
            yield Redis(self.cluster.bastion, tunnel, ip, port)

    def sentinel_master(self, port=26379):
        master_address = self.master_ip_address()

        tunnel = self.cluster.bastion.tunnel(master_address, port)
        return RedisSentinel(self.cluster.bastion, tunnel, master_address, port)

    def sentinel_clients(self, port=26379):
        tunnels = []

        for ip in self.instance_private_ips():
            tunnel = self.cluster.bastion.tunnel(ip, port)
            tunnels.append((ip, tunnel))

        for ip, tunnel in tunnels:
            yield RedisSentinel(self.cluster.bastion, tunnel, ip, port)

    def sentinel_client(self, ip, port=26379):
        for instance in self.instances:
            if instance.private_ip_address == ip:
                tunnel = self.cluster.bastion.tunnel(ip, port)
                return RedisSentinel(self.cluster.bastion, tunnel, ip, port)

        raise UnknownRedisInstance(ip)


# FIXME: Remove once we get rid of the old-style instances
class OldRedisCluster(RedisCluster):
    def __init__(self, dbsilo, *args, **kwargs):
        super(OldRedisCluster, self).__init__(*args, **kwargs)

        self.dbsilo = dbsilo

    def master_hostname(self):
        env = self.cluster.env
        if env == 'prod-old':
            env = 'app'

        return 'redismaster.{}.{}'.format(
            self.dbsilo,
            self.cluster.zone)


class Redis(object):
    def __init__(self, bastion, tunnel, host, port):
        self.host = host
        self.port = port

        self._tunnel = tunnel

        try:
            self._tunnel.open()
        except TunnelDown:
            LOG.error('failed to open tunnel to %s:%s', self.host, self.port)
            self._conn = None
        else:
            self._conn = redis.StrictRedis(
                host=self._tunnel.host,
                port=self._tunnel.port,
            )

    def close(self):
        self._tunnel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getattr__(self, key):
        if self._conn:
            return getattr(self._conn, key)
        else:
            raise ConnectionClosed

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)

    def is_connected(self):
        return self._conn is not None


class RedisSentinel(Redis):
    def __init__(self, bastion, tunnel, host, port):
        super(RedisSentinel, self).__init__(bastion, tunnel, host, port)


@click.group()
def cli():
    pass


@cli.command('change-master-quorum')
@click.argument('dbsilo_name', required=True)
@click.argument('quorum', type=int)
@click.pass_context
def change_master_quorum(ctx, dbsilo_name, quorum):
    if quorum < 1:
        ctx.fail('cannot set quorum under 1')

    dbsilo = ctx.obj['cluster'].dbsilo(dbsilo_name)

    redis_cluster = dbsilo.redis_cluster()
    master_hostname = redis_cluster.master_hostname()
    sentinel_clients = list(redis_cluster.sentinel_clients())

    needs_change = False
    for sentinel_client in sentinel_clients:
        if sentinel_client.is_connected():
            info = sentinel_client.sentinel_master(master_hostname)
            sentinel_quorum = info['quorum']
            sentinel_node_count = info['num-other-sentinels']

            print 'current quorum is', sentinel_quorum, 'on', sentinel_client

            if quorum < sentinel_node_count / 2 + 1:
                ctx.fail('quorum must be >= master nodes / 2 + 1')

            needs_change |= quorum != sentinel_quorum

    if not needs_change:
        print 'no changes needed'
        return

    msg = 'are you sure you want to apply? [yes/no]: '
    if not prompt(msg, ctx.obj['yes']):
        ctx.fail('cluster unchanged')

    for sentinel_client in sentinel_clients:
        sentinel_client.sentinel_set(master_hostname, 'quorum', quorum)

    print 'quorum changed'


@cli.command('decommission')
@click.option('--ignore-offline', default=False, is_flag=True)
@click.argument('dbsilo_name', required=True)
@click.argument('ips', nargs=-1)
@click.pass_context
def decommission(ctx, ignore_offline, dbsilo_name, ips):
    cluster = ctx.obj['cluster']
    dbsilo = cluster.dbsilo(dbsilo_name)
    ips = set(ips)

    redis_cluster = dbsilo.redis_cluster()
    old_instance_count = len(redis_cluster.instances)
    new_instance_count = old_instance_count - len(ips)
    quorum = (old_instance_count / 2) + 1

    print 'instance count:', old_instance_count
    print 'quorum:', quorum

    if new_instance_count < quorum:
        ctx.fail('cannot reduce instance count below quorum')

    # Make sure the IPs are in this redis cluster
    for ip in ips:
        found = False
        for instance in redis_cluster.instances:
            if ip == instance.private_ip_address:
                found = True
                break

        if not found:
            ctx.fail('ip is not in redis cluster')

    # First, create sentinel clients all but the node we're decommissioning.
    sentinel_clients = {}
    for ip in redis_cluster.instance_private_ips():
        try:
            sentinel_client = redis_cluster.sentinel_client(ip)
        except TunnelDown:
            if ignore_offline:
                LOG.error('ip %s is offline', ip)
                pass
            else:
                raise
        else:
            if sentinel_client.is_connected():
                sentinel_clients[ip] = sentinel_client
            else:
                LOG.error('ip %s is offline', ip)

    # Make sure sentinels all agree on who is the master
    if not _sentinels_agree_on_master(redis_cluster, sentinel_clients):
        ctx.fail('sentinels do not agree who is master')

    msg = 'are you sure you want to apply? [yes/no]: '
    if not prompt(msg, ctx.obj['yes']):
        ctx.fail('redis cluster unchanged')

    for ip in ips:
        _decommission_ip(
            ctx,
            ip,
            cluster.bastion,
            redis_cluster,
            sentinel_clients)


def _decommission_ip(ctx, ip, bastion, cluster, sentinel_clients):
    # We decommission according to this document:
    # https://redis.io/topics/sentinel#adding-or-removing-sentinels

    _decommission_sentinel(ctx, ip, bastion, cluster, sentinel_clients)
    _decommission_server(ctx, ip, bastion, cluster, sentinel_clients)


def _decommission_sentinel(ctx, ip, bastion, cluster, sentinel_clients):
    # Shut down our sentinel
    bastion.check_call([
        'ssh',
        ip,
        '/usr/bin/sudo',
        '/usr/bin/service',
        'redis-sentinel',
        'stop'])

    # Remove the decommissioned sentinel from our list
    del sentinel_clients[ip]

    _reset_sentinels(ctx, cluster, sentinel_clients)

    print 'sentinel %s decommissioned' % ip


def _decommission_server(ctx, ip, bastion, cluster, sentinel_clients):
    # Shut down our server
    bastion.check_call([
        'ssh',
        ip,
        '/usr/bin/sudo',
        '/usr/bin/service',
        'redis-server',
        'stop'])

    _reset_sentinels(ctx, cluster, sentinel_clients)

    print 'server %s decommissioned' % ip


def _reset_sentinels(ctx, cluster, sentinel_clients):
    # Next, reset each of the sentinels
    for client in sentinel_clients.itervalues():
        print 'resetting', client
        if client.execute_command('SENTINEL RESET *') != 1:
            ctx.fail('sentinel reset failed')

        print 'sleeping 30 seconds'
        time.sleep(30)

        for i in xrange(5):
            if _sentinels_agree_on_master(cluster, sentinel_clients):
                break
            else:
                print 'sentinels do not yet agree on master, sleeping'
                time.sleep(10)
        else:
            ctx.fail('sentinels do not agree on a master')


def _sentinels_agree_on_master(cluster, sentinel_clients):
    master_name = cluster.master_hostname()

    print 'make sure all sentinels agree on the master'
    master_ips = [(c.host, c.sentinel_master(master_name)['ip'])
                  for c in sentinel_clients.itervalues()]

    master_ip = master_ips[0][1]
    sentinels_agree = True
    for host, ip in master_ips:
        print '%s thinks %s is master' % (host, ip)
        if ip != master_ip:
            sentinels_agree = False

    return sentinels_agree
