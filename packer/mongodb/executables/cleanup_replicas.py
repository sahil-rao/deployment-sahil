#!/usr/bin/python

from pymongo import MongoClient
import datetime
import dd
import sys


AUTOREMOVAL_DELAY_SECONDS = 10800   # 3 hours


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


def main():
    client = MongoClient()

    # Only run if we're a master
    resp = client['admin'].command('isMaster')
    if resp['ok'] != 1 or not resp['ismaster']:
        return 0

    rs_status = client["admin"].command("replSetGetStatus")

    unhealthy_members = [
        member for member in rs_status['members']
        if member['stateStr'] == "(not reachable/healthy)"]

    if not unhealthy_members:
        return 0

    for member in unhealthy_members:
        time_since_last_heartbeat = datetime.datetime.utcnow() - \
            member["lastHeartbeatRecv"]

        if time_since_last_heartbeat.seconds < AUTOREMOVAL_DELAY_SECONDS:
            print \
                str(datetime.datetime.now()), \
                "Unhealthy Replica set member detected but not removed"

            print \
                str(datetime.datetime.now()), \
                "Auto-removal scheduled in", \
                AUTOREMOVAL_DELAY_SECONDS - time_since_last_heartbeat.seconds, \
                "seconds"

            title = 'MongoDB Unhealthy Replica'
            text = 'Unhealthy replica: {}'.format(member['name'])
        else:
            print \
                str(datetime.datetime.now()), \
                "Removing", \
                str(member['name']), \
                "from MongoDB replica set"

            reconfigure_replicaset(client, member["_id"])

            title = 'MongoDB Unhealthy Replica Removed'
            text = 'Removed unhealthy replica: {}'.format(member['name'])

        dd.create_event(
            title=title,
            text=text,
            timestamp=member["lastHeartbeatRecv"],
            alert_type='error',
            hosts=[member['name'].split(':')[0]],
        )

    return 1


if __name__ == '__main__':
    sys.exit(main())
