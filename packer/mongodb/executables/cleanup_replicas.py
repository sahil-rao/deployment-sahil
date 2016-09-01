import datetime
import socket
import os
import sys
import re
import traceback
from pprint import pprint
from pymongo import MongoClient
from boto.route53.record import ResourceRecordSets
import boto

SUFFIX = os.getenv('ZONE_NAME', 'xplain.io')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-west-1')
AUTOREMOVAL_DELAY_SECONDS = 10800   # 3 hours


def get_record(route53_zone, db_silo_name, service_name, ip):
    """
    Check if a record exists matching the service pattern with the current host's ip
    """

    # Match records belonging to the service for particular dbsilo and cluster
    match_regex = "{0}\d+\.{1}\.{2}\.?" \
                  .format(service_name, db_silo_name, route53_zone.name)

    for record in route53_zone.get_records():
        match = re.match(match_regex, record.name)
        if match and ip in record.resource_records:
            return record

    return None


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


def cleanup_route53(cluster_name, db_silo_name, service_name, member_hostname):
    """
    Remove route53 record that matches member hostname
    """

    hname, port = member_hostname.split(":")
    if hname == None:
        return

    hostip = socket.gethostbyname(hname)
    if hostip is None:
        return

    zone_name = "{0}.{1}".format(cluster_name, SUFFIX)
    conn = boto.route53.connect_to_region(AWS_REGION)
    route53_zone = conn.get_zone(zone_name)
    record = get_record(route53_zone, db_silo_name, service_name, hostip)

    if record is not None:
        route53_zone.delete_record(record)


try:
    if len(sys.argv) < 3:
        print "{0} : Insufficent parameter".format(sys.argv[0])
        sys.exit(2)

    cluster_name = sys.argv[1]
    db_silo_name = sys.argv[2]
    service_name = sys.argv[3]

    client = MongoClient()

    resp = client['admin'].command('isMaster')
    if resp['ok'] != 1 or not resp['ismaster']:
        sys.exit(0)

    rs_status = client["admin"].command("replSetGetStatus")
    for member in rs_status['members']:
        if member['stateStr'] == "(not reachable/healthy)":
            time_since_last_heartbeat = datetime.datetime.utcnow() - member["lastHeartbeatRecv"]
            if time_since_last_heartbeat.seconds > AUTOREMOVAL_DELAY_SECONDS:
                print str(datetime.datetime.now()), "Removing", str(member['name']), "from route53 records"
                cleanup_route53(cluster_name, db_silo_name, service_name, member['name'])
                print str(datetime.datetime.now()), "Removing", str(member['name']), "from MongoDB replica set"
                reconfigure_replicaset(client, member["_id"])
                # Exit code 3 signals that a replica set member was removed
                sys.exit(3)
            # Exit code 4 signals a replica set member was detected unhealthy, but not removed
            print str(datetime.datetime.now()), "Unhealthy Replica set member detected but not removed"
            print str(datetime.datetime.now()), "Auto-removal scheduled in", str(AUTOREMOVAL_DELAY_SECONDS - time_since_last_heartbeat.seconds), "seconds"
            sys.exit(4)
except Exception as e:
    print str(datetime.datetime.now()), "Failed to cleanup replica set"
    traceback.print_exc()
    sys.exit(1)

sys.exit(0)


