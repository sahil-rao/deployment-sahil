from __future__ import absolute_import

import pymongo


class MongoCluster(object):
    def __init__(self, cluster, service, instances):
        self.cluster = cluster
        self.service = service
        self.instances = instances

    def master_hostname(self):
        return '{}-master.{}'.format(
            self.service,
            self.cluster.zone)

    def master(self):
        master_hostname = self.master_hostname()
        return Mongo(self.cluster.bastion, master_hostname)

    def instance_private_ips(self):
        for instance in self.instances:
            yield instance.private_ip_address

    def clients(self, port=27017):
        tunnels = []

        for ip in self.instance_private_ips():
            tunnel = self.cluster.bastion.tunnel(ip, port)
            tunnels.append((ip, tunnel))

        for ip, tunnel in tunnels:
            yield Mongo(self.cluster.bastion, tunnel, ip, port)


# FIXME: Remove once we get rid of the old-style instances
class OldMongoCluster(MongoCluster):
    def __init__(self, dbsilo, *args, **kwargs):
        super(OldMongoCluster, self).__init__(*args, **kwargs)

        self.dbsilo = dbsilo

    def master_hostname(self):
        return 'mongomaster.{}.{}'.format(
            self.dbsilo,
            self.cluster.zone)


class Mongo(object):
    def __init__(self, bastion, tunnel, host, port):
        self.host = host
        self.port = port

        self._tunnel = tunnel
        self._tunnel.open()

        self._conn = pymongo.MongoClient(
            host=self._tunnel.host,
            port=self._tunnel.port,
            socketTimeoutMS=10000,
            connectTimeoutMS=10000,
            serverSelectionTimeoutMS=10000,
        )

    def close(self):
        self._conn.close()
        self._tunnel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getattr__(self, key):
        return getattr(self._conn, key)

    def __getitem__(self, key):
        return self._conn[key]

    def mongo_version(self):
        if self._conn is None:
            return None

        return self._conn.server_info()['version']

    def server_status(self):
        if not hasattr(self, '_server_status'):
            try:
                self._server_status = self._conn.admin.command('serverStatus')
            except pymongo.errors.PyMongoError:
                self._server_status = {}

        return self._server_status

    @property
    def repl_status(self):
        if not hasattr(self, '_repl_status'):
            try:
                self._repl_status = self._conn.admin.command('replSetGetStatus')
            except pymongo.errors.PyMongoError:
                self._repl_status = {}

        return self._repl_status

    @property
    def primary_repl_status(self):
        for member in self.repl_status.get('members', []):
            if member['state'] == 1:
                return member

        return {}

    @property
    def current_repl_status(self):
        for member in self.repl_status.get('members', []):
            if member.get('self'):
                return member

        return {}

    def is_master(self):
        return self.current_repl_status.get('state') == 1

    def is_replica(self):
        return self.current_repl_status.get('state') == 2

    def is_arbiter(self):
        return self.current_repl_status.get('state') == 7

    def members(self):
        primaries = []
        secondaries = []
        arbiters = []
        others = []

        for member in self.repl_status.get('members', []):
            name = member['name']

            if member['state'] == 1:
                primaries.append(name)
            elif member['state'] == 2:
                secondaries.append(name)
            elif member['state'] == 7:
                arbiters.append(name)
            else:
                others.append(name)

        return (
            sorted(primaries),
            sorted(secondaries),
            sorted(arbiters),
            sorted(others),
        )

    def member_states(self):
        num_primaries = 0
        num_secondaries = 0
        num_arbiters = 0
        num_otherstate = 0

        for member in self.repl_status.get('members', []):
            if member['state'] == 1:
                num_primaries += 1
            elif member['state'] == 2:
                num_secondaries += 1
            elif member['state'] == 7:
                num_secondaries += 1
            else:
                num_otherstate += 1

        return num_primaries, num_secondaries, num_arbiters, num_otherstate

    def config_versions(self):
        config_versions = set()
        for member in self.repl_status.get('members', []):
            try:
                config_versions.add(member['configVersion'])
            except KeyError:
                pass

        return config_versions

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)
