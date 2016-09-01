#!/usr/bin/python

from pymongo import MongoClient
import argparse
import boto3
import calendar
import datetime
import dd
import sys


AUTOREMOVAL_DELAY_SECONDS = 10800   # 3 hours
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
    def __init__(self, title, text, alert_type='error', **kwargs):
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


def reconfigure_replicaset(client, member_id_to_remove):
    """
    Generate new config with reassigned member ids; apply new configuration
    """

    resp = client['admin'].command('replSetGetConfig')
    if resp['ok'] != 1:
        return

    config = resp['config']
    for member in config['members']:
        if member['_id'] == member_id_to_remove:
            config['members'].remove(member)
            break

    config['version'] += 1

    client['admin'].command('replSetReconfig', config)


def get_running_hostnames(region, dbsilo):
    """
    Find all the running dbsilo mongo instances
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

    running_hostnames = set()
    for instance in instances:
        print instance.private_ip_address, instance.state

        if instance.state['Name'] not in TERMINATED_STATES:
            running_hostnames.add(instance.private_ip_address)

    return running_hostnames


def run(args):
    client = MongoClient()

    # Only run if we're a master
    resp = client['admin'].command('isMaster')
    if resp['ok'] != 1 or not resp['ismaster']:
        return 0

    rs_status = client["admin"].command("replSetGetStatus")

    unreachable_members = [
        member for member in rs_status['members']
        if member['stateStr'] == "(not reachable/healthy)"]

    if not unreachable_members:
        return 0

    running_hostnames = get_running_hostnames(args.region, args.dbsilo)

    # Check if any of the members are terminated instances. If so, filter them
    # out now.
    unhealthy_members = []
    stopped_members = []
    for member in unreachable_members:
        hostname = member['name'].split(':')[0]

        if hostname in running_hostnames:
            unhealthy_members.append(member)
        else:
            stopped_members.append(member)

    if stopped_members:
        for member in stopped_members:
            print \
                str(datetime.datetime.now()), \
                "Removing stopped/terminated instance"

            reconfigure_replicaset(client, member["_id"])

        report(
            title='Removed Stopped MongoDB {} instances'.format(hostname),
            text='\n'.join(
                ' * ' + member['name'] for member in stopped_members
            ),
        )

    if not unhealthy_members:
        return 0

    for member in unhealthy_members:
        hostname = member['name'].split(':')[0]

        time_since_last_heartbeat = datetime.datetime.utcnow() - \
            member["lastHeartbeatRecv"]

        if time_since_last_heartbeat.seconds < args.delay:
            print \
                str(datetime.datetime.now()), \
                "Unhealthy Replica set member detected but not removed:", \
                hostname

            print \
                str(datetime.datetime.now()), \
                "Auto-removal scheduled in", \
                args.delay - time_since_last_heartbeat.seconds, \
                "seconds"

            title = 'MongoDB Unhealthy Replica'
            text = 'Unhealthy replica: {}'.format(member['name'])
        else:
            print \
                str(datetime.datetime.now()), \
                "Removing from MongoDB replica set:", \
                str(member['name'])

            reconfigure_replicaset(client, member["_id"])

            title = 'MongoDB Unhealthy Replica Removed'
            text = 'Removed unhealthy replica: {}'.format(member['name'])

    raise Error(
        title=title,
        text=text,
        timestamp=calendar.timegm(
            member["lastHeartbeatRecv"].utctimetuple()
        ),
    )

    return 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', required=True)
    parser.add_argument('--dbsilo', required=True)
    parser.add_argument('--delay', type=int, default=AUTOREMOVAL_DELAY_SECONDS)
    args = parser.parse_args()

    try:
        return run(args)
    except Error as err:
        err.report()
        return 1


if __name__ == '__main__':
    sys.exit(main())
