#!/usr/bin/python

import argparse
import boto3
import dd
import pprint
import pymongo
import sys


def get_clients(hostnames):
    clients = []
    for hostname in hostnames:
        print 'connecting to', hostname

        try:
            client = pymongo.MongoClient(
                host=hostname,
                connectTimeoutMS=1000,
                serverSelectionTimeoutMS=1000,
                connect=True)

            # Make sure the server is up.
            client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError:
            print >> sys.stderr, 'failed to connect to', hostname
        else:
            clients.append(client)

    return clients


def initiate(master, dbsilo, hostnames):
    config = {
        '_id': dbsilo,
        'members': [
            {'_id': i, 'host': '{}:27017'.format(hostname)}
            for i, hostname in enumerate(hostnames)
        ],
    }
    resp = master.admin.command('replSetInitiate', config)

    if resp['ok'] != 1:
        print >> sys.stderr, 'Failed to run replSetInitiate'
        pprint.pprint(resp, sys.stderr)

        dd.create_event(
            title='Failed to create MongoDB replica set',
            text='Failed to create replica set on {}:{}\n{}'.format(
                master.address[0],
                master.address[1],
                pprint.pformat(resp),
            ),
            alert_type='error',
            hosts=[master.address[0]],
        )

        return 1

    print 'created replica set'

    dd.create_event(
        title='Created MongoDB replica set',
        text='Created MongoDB {} Repica Set on {}\n{}'.format(
            dbsilo,
            master.address[0],
            master.address[1],
            '\n'.join(' * {}'.format(host) for host in hostnames),
        ),
    )


def reconfigure(master, hostnames):
    # Otherwise, Add any missing nodes to the set.
    resp = master.admin.command('replSetGetConfig')
    if resp['ok'] != 1:
        print >> sys.stderr, 'Failed to run replSetGetConfig'
        pprint.pprint(resp, sys.stderr)
        return 1

    config = resp['config']
    members = config['members']

    rs_hosts = set(member['host'] for member in members)
    current_hosts = set('{}:27017'.format(hostname) for hostname in hostnames)

    add_hosts = []

    for host in current_hosts:
        if host not in rs_hosts:
            add_hosts.append(host)

    if add_hosts:
        print 'Adding new hosts:', ' '.join(add_hosts)

        max_id = max(member['_id'] for member in members)

        for host in add_hosts:
            max_id += 1
            config['members'].append({'_id': max_id, 'host': host})

        config['version'] += 1

        resp = master.admin.command('replSetReconfig', config)
        if resp['ok'] != 1:
            print >> sys.stderr, 'Failed to run replSetReconfig'
            pprint.pprint(resp, sys.stderr)

            dd.create_event(
                title='Failed to reconfigure MongoDB replica set',
                text='Failed to reconfigure replica set on {}:{}\n{}'.format(
                    master.address[0],
                    master.address[1],
                    pprint.pformat(resp),
                ),
                alert_type='error',
                hosts=[master.address[0]],
            )

            return 1

        dd.create_event(
            title='Reconfigured MongoDB replica set',
            text='Reconfigured replica set on {}:{}\n{}'.format(
                master.address[0],
                master.address[1],
                '\n'.join(' * {}'.format(host) for host in hostnames),
            ),
            hosts=[master.address[0]] + hostnames,
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', required=True)
    parser.add_argument('--dbsilo', required=True)
    args = parser.parse_args()

    dbsilo_tag = '{}-mongo'.format(args.dbsilo)

    # Discover all the instances in the mongo cluster
    ec2 = boto3.resource('ec2', region_name=args.region)
    instances = list(ec2.instances.filter(Filters=[
        {
            'Name': 'instance-state-name',
            'Values': ['running'],
        },
        {
            'Name': 'tag:DBSilo',
            'Values': [dbsilo_tag],
        },
    ]))

    hostnames = sorted(instance.private_ip_address for instance in instances)
    print 'found instances:', ' '.join(hostnames)

    if len(hostnames) == 0:
        print >> sys.stderr, 'error: no instances found for tag', dbsilo_tag
        return 1
        pass

    clients = get_clients(hostnames)

    # Find master
    masters = [
        client for client in clients
        if client['admin'].command('isMaster')['ismaster']]

    if len(masters) == 0:
        print 'No master found, electing', clients[0].address
        return initiate(clients[0], args.dbsilo, hostnames)

    elif len(masters) == 1:
        return reconfigure(masters[0], hostnames)

    else:
        print >> sys.stderr, \
            'error, multiple masters!', \
            ' '.join(str(master.address) for master in masters)

        dd.create_event(
            title='Multiple MongoDB Masters',
            text='Multiple MongoDB Masters:\n{}'.format(
                '\n'.join(
                    ' * {}:{}'.format(*master.address)
                    for master in masters
                ),
            ),
            alert_type='error',
            hosts=[master.address[0] for master in masters],
        )

        return 1


if __name__ == '__main__':
    sys.exit(main())
