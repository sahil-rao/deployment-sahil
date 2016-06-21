#!/usr/bin/env python

import datetime
import time
import sys
import os
import traceback
import boto.ec2

AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-west-1')
SNAPSHOT_TTL_IN_DAYS = 14
DEVICE_NAME = '/dev/xvdf'


def backup(instance_id, cluster, dbsilo):

    conn = boto.ec2.connect_to_region(AWS_REGION)
    inst_attrs = conn.get_instance_attribute(instance_id, 'blockDeviceMapping')
    volume_id = inst_attrs['blockDeviceMapping'][DEVICE_NAME].volume_id
    snapshots = conn.get_all_snapshots(filters={'volume-id': volume_id})
    
    # Delete snapshots more than SNAPSHOT_TTL_IN_DAYS days old
    for snap in snapshots:
        snap_datetime = datetime.datetime(*time.strptime(snap.start_time, "%Y-%m-%dT%H:%M:%S.%fZ")[:6])
        if snap_datetime < datetime.datetime.now() - datetime.timedelta(days=SNAPSHOT_TTL_IN_DAYS):
            print str(datetime.datetime.now()), "Deleting snapshot", snap.id
            snap.delete()

    # Create new snapshot
    snap = conn.create_snapshot(volume_id)
    # TODO: Fix IAM role policies so that this works
    # snap.add_tags({
    #     'cluster': cluster,
    #     'dbsilo': dbsilo,
    #     'service': 'mongodb',
    #     'instance': instance_id,
    #     'created': str(datetime.datetime.now())
    # })


if len(sys.argv) < 4:
    sys.exit(2)
try:
    backup(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0)
except Exception as e:
    print "MongoDB backup failed on instance", str(sys.argv[1])
    traceback.print_exc()
    sys.exit(1)
