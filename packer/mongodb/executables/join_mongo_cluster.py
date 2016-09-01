#!/usr/bin/python

import argparse
import boto3
import copy
import dd
import pprint
import pymongo
import sys


TERMINATED_STATES = ('shutting-down', 'terminating', 'terminated')


def report(title, text='', master=None, instances=(), **kwargs):
    print title

    lines = []

    for instance in instances:
        host = instance.private_ip_address

        line = ' * {} state:{}'.format(host, instance.state['Name'])

        if master and host == master.address[0]:
            line += ' (master)'

        lines.append(line)

    instances = '\n'.join(lines)

    if text:
        text = '{}\n{}'.format(text, instances)
    else:
        text = instances

    print text

    dd.create_event(
        title=title,
        text=text,
        **kwargs)


class Error(Exception):
    def __init__(self, title, text='', alert_type='error', **kwargs):
        super(Error, self).__init__()

        self.title = title
        self.text = text
        self.alert_type = alert_type
        self.kwargs = kwargs

    def __str__(self):
        return self.text

    def report(self):
        report(
            title='Failed joining MongoDB cluster: {}'.format(self.title),
            text=self.text,
            alert_type=self.alert_type,
            **self.kwargs)


def run_command(database, *args, **kwargs):
    resp = database.command(*args, **kwargs)

    if resp['ok'] != 1:
        raise Error(
            title='Failed to run replSetGetConfig',
            text=pprint.pformat(resp),
        )

    return resp


def get_instances(region, dbsilo):
    """
    Find all the dbsilo mongo instances and split them up into a
    list of running and terminated hostnames
    """

    dbsilo_tag = '{}-mongo'.format(dbsilo)

    # Discover all the instances in the mongo cluster
    ec2 = boto3.resource('ec2', region_name=region)
    instances = list(ec2.instances.filter(Filters=[
        {
            'Name': 'tag:DBSilo',
            'Values': [dbsilo_tag],
        },
    ]))

    if not instances:
        raise Error(
            title='no instances',
            text='no instances found for tag `{}`'.format(dbsilo_tag))

    running_instances = []

    for instance in instances:
        print 'found: {} ({})'.format(
            instance.private_ip_address,
            instance.state['Name']
        )

        if instance.state['Name'] not in TERMINATED_STATES:
            running_instances.append(instance)

    return running_instances


def get_clients(dbsilo, instances):
    clients = []
    for instance in instances:
        host = instance.private_ip_address

        try:
            client = pymongo.MongoClient(
                host=host,
                connectTimeoutMS=1000,
                serverSelectionTimeoutMS=1000,
                connect=True)

            # Make sure the server is up.
            client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError:
            print >> sys.stderr, 'failed to connect to', host
        else:
            clients.append(client)

    if not clients:
        raise Error(
            title='All {} databases offline'.format(dbsilo),
            instances=instances,
        )

    return clients


def get_masters(clients):
    return [
        client for client in clients
        if run_command(client.admin, 'isMaster')['ismaster']]


def initiate(master, dbsilo, instances):
    """
    Initiate the mongodb silo replicaset
    """

    # FIXME: This doesn't handle cases where the replicaset is already
    # initialized.

    print 'Initiating replicaset on {}:{}'.format(
        master.address[0],
        master.address[1])

    hosts = [instance.private_ip_address for instance in instances]

    config = {
        '_id': dbsilo,
        'members': [
            {'_id': i, 'host': '{}:27017'.format(host)}
            for i, host in enumerate(hosts)
        ],
    }

    run_command(master.admin, 'replSetInitiate', config)

    report(
        title='Created {} MongoDB replica set'.format(dbsilo),
        instances=instances,
    )


def repl_set_get_config(master):
    return run_command(master.admin, 'replSetGetConfig')['config']


def repl_set_reconfig(master, config):
    config['version'] += 1
    run_command(master.admin, 'replSetReconfig', config)


def add_new_hosts(config, running_instances):
    # Grab the current hostnames in the replicaset so we can determine what we
    # need to add and remove.
    current_hosts = set(member['host'] for member in config['members'])

    # If we have new hosts, their id needs to be greater than all the other ids.
    max_id = max(member['_id'] for member in config['members'])

    for instance in running_instances:
        host = '{}:27017'.format(instance.private_ip_address)

        if host not in current_hosts:
            print 'Adding new host:', host

            max_id += 1
            config['members'].append({'_id': max_id, 'host': host})


def remove_stopped_hosts(config, running_instances):
    # Remove any stopped hosts
    members = []

    running_hosts = set(
        '{}:27017'.format(instance.private_ip_address)
        for instance in running_instances)

    for member in config['members']:
        host = member['host']

        if host not in running_hosts:
            print 'Removing stopped host:', host
        else:
            members.append(member)

    config['members'] = members


def reconfigure(master, dbsilo, running_instances):
    config = repl_set_get_config(master)

    # Grab a copy of the original config to help track if anything has changed.
    original_config = copy.deepcopy(config)

    add_new_hosts(config, running_instances)
    remove_stopped_hosts(config, running_instances)

    if config != original_config:
        repl_set_reconfig(master, config)

        instances = running_instances

        report(
            title='Reconfigured {} MongoDB replica set'.format(dbsilo),
            instances=instances,
        )


def run(args):
    running_instances = get_instances(args.region, args.dbsilo)

    clients = get_clients(args.dbsilo, running_instances)

    # Find all the instances that think they are masters
    masters = get_masters(clients)

    if len(masters) == 0:
        master = clients[0]
        initiate(master, args.dbsilo, running_instances)
    elif len(masters) == 1:
        master = masters[0]
    else:
        raise Error(
            title='Multiple MongoDB Masters',
            text='\n'.join(
                ' * {}:{}'.format(*master.address)
                for master in masters
            ),
        )

    reconfigure(
        master,
        args.dbsilo,
        running_instances)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', required=True)
    parser.add_argument('--dbsilo', required=True)
    args = parser.parse_args()

    try:
        return run(args)
    except Error as err:
        err.report()
        return 1


if __name__ == '__main__':
    sys.exit(main())
