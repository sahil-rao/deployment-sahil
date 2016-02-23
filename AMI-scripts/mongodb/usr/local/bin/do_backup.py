#!/usr/bin/env python

import datetime
import time
import sys
import boto.ec2

AWS_REGION = 'us-west-1'
SNAPSHOT_TTL_IN_DAYS = 3
DEVICE_NAME = '/dev/xvdf'


def backup(instance_id):

    conn = boto.ec2.connect_to_region(AWS_REGION)
    inst_attrs = conn.get_instance_attribute(instance_id, 'blockDeviceMapping')
    volume_id = inst_attrs['blockDeviceMapping'][DEVICE_NAME].volume_id
    snapshots = conn.get_all_snapshots(filters={'volume-id': volume_id})
    
    # Delete snapshots more than 3 days old
    for snap in snapshots:
        snap_datetime = datetime.datetime(*time.strptime(snap.start_time, "%Y-%m-%dT%H:%M:%S.%fZ")[:6])
        if snap_datetime < datetime.datetime.now() - datetime.timedelta(days=SNAPSHOT_TTL_IN_DAYS):
            print "Deleting snapshot ", snap.id
            snap.delete()

    # Create new snapshot
    conn.create_snapshot(volume_id)


# First argument should be the instance id, env var ${EC2_INSTANCE_ID}
backup(sys.argv[1])
