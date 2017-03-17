import boto3
import dd
import logging
import redis


TERMINATED_STATES = ('shutting-down', 'terminating', 'terminated')


def get_instances(region, service):
    """
    Find all the redis instances and split them up into a
    list of running and terminated hostnames
    """

    # Discover all the instances in the redis cluster
    ec2 = boto3.resource('ec2', region_name=region)
    instances = list(ec2.instances.filter(Filters=[
        {
            'Name': 'tag:Service',
            'Values': [service],
        },
    ]))

    if not instances:
        raise dd.Error(
            title='no instances',
            text='no instances found for tag `{}`'.format(service))

    running_instances = []

    for instance in instances:
        print 'found: {} ({})'.format(
            instance.private_ip_address,
            instance.state['Name']
        )

        if instance.state['Name'] not in TERMINATED_STATES:
            running_instances.append(instance)

    return running_instances


class RedisClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._client = redis.StrictRedis(host=host, port=port)

    def __getattr__(self, key):
        return getattr(self._client, key)

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)


def get_clients(service, instances, port):
    clients = []
    for instance in instances:
        host = instance.private_ip_address
        client = RedisClient(host=host, port=port)

        clients.append(client)

    if not clients:
        raise dd.Error(
            title='All {} databases offline'.format(service),
            instances=instances,
        )

    return clients


def get_all_masters(clients):
    masters = []
    for client in clients:
        try:
            info = client.info()
        except redis.exceptions.ConnectionError:
            logging.exception(
                'failed to connect to %s:%s, skipping',
                client.host,
                client.port)
        else:
            # Only consider masters really masters if they have any slaves.
            if info['role'] == 'master' and info['connected_slaves'] != 0:
                masters.append(client)

    return masters


def get_master(clients):
    # Find all the instances that think they are masters
    masters = get_all_masters(clients)

    if len(masters) == 0:
        return clients[0]
    elif len(masters) == 1:
        return masters[0]
    else:
        raise dd.Error(
            title='Multiple Redis Masters',
            text='\n'.join(
                ' * {}:{}'.format(master.host, master.port)
                for master in masters
            ),
        )
