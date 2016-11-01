#!/usr/bin/env python

import logging
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
    logging.info('Starting backup for %s %s %s', instance_id, cluster, dbsilo)

    conn = boto.ec2.connect_to_region(AWS_REGION)
    inst_attrs = conn.get_instance_attribute(instance_id, 'blockDeviceMapping')
    volume_id = inst_attrs['blockDeviceMapping'][DEVICE_NAME].volume_id
    snapshots = conn.get_all_snapshots(filters={'volume-id': volume_id})

    # Delete snapshots more than SNAPSHOT_TTL_IN_DAYS days old
    for snap in snapshots:
        snap_datetime = datetime.datetime(*time.strptime(snap.start_time, "%Y-%m-%dT%H:%M:%S.%fZ")[:6])
        if snap_datetime < datetime.datetime.now() - datetime.timedelta(days=SNAPSHOT_TTL_IN_DAYS):
            logging.info('Deleting snapshot %s', snap.id)
            snap.delete()

    # Create new snapshot
    max_attempts = 10
    for attempt in xrange(max_attempts):
        logging.info('Creating snapshot for volume %s [attempt %s/%s]', volume_id, attempt + 1, max_attempts)
        try:
            snap = conn.create_snapshot(volume_id)
        except boto.exception.EC2ResponseError as e:
            if e.error_code == 'SnapshotCreationPerVolumeRateExceeded':
                logging.warning('Snapshot rate limit exceeded, sleeping')
                time.sleep(60)
        else:
            break
    else:
        raise Exception('Timed out trying to create snapshot')

    logging.info('Finished creating snapshot %s for volume %s', snap.id, volume_id)

    # TODO: Fix IAM role policies so that this works
    snap.add_tags({
        'cluster': cluster,
        'dbsilo': dbsilo,
        'service': 'mongodb',
        'instance': instance_id,
        'created': str(datetime.datetime.now())
    })


def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)s [%(module)s.%(funcName)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO)

    if len(sys.argv) < 4:
        print >> sys.stderr, 'Logging takes 4 arguments'
        return 2

    instance_id = sys.argv[1]
    cluster = sys.argv[2]
    dbsilo = sys.argv[3]

    try:
        backup(instance_id, cluster, dbsilo)
    except Exception:
        logging.exception('MongoDB backup failed on instance %s', instance_id)
        return 1
    else:
        return 0

if __name__ == '__main__':
    sys.exit(main())
