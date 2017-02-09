#!/usr/bin/env python

import argparse
import boto.ec2
import datetime
import dd
import logging
import sys
import time

DEVICE_NAME = '/dev/xvdf'


def backup(region, env, service, instance_id, ttl):
    logging.info('Starting backup for %s %s %s', instance_id, env, service)

    conn = boto.ec2.connect_to_region(region)
    inst_attrs = conn.get_instance_attribute(instance_id, 'blockDeviceMapping')
    volume_id = inst_attrs['blockDeviceMapping'][DEVICE_NAME].volume_id
    snapshots = conn.get_all_snapshots(filters={'volume-id': volume_id})

    # Delete snapshots more than ttl days old
    for snap in snapshots:
        snap_datetime = datetime.datetime(
            *time.strptime(snap.start_time,
                           "%Y-%m-%dT%H:%M:%S.%fZ")[:6])

        now = datetime.datetime.utcnow()
        if snap_datetime < now - datetime.timedelta(days=ttl):
            logging.info('Deleting snapshot %s', snap.id)
            snap.delete()

    # Create new snapshot
    max_attempts = 10
    for attempt in xrange(max_attempts):
        logging.info('Creating snapshot for volume %s [attempt %s/%s]',
                     volume_id,
                     attempt + 1,
                     max_attempts)
        try:
            snap = conn.create_snapshot(volume_id)
        except boto.exception.EC2ResponseError as e:
            if e.error_code == 'SnapshotCreationPerVolumeRateExceeded':
                logging.warning('Snapshot rate limit exceeded, sleeping')
                time.sleep(60)
        else:
            break
    else:
        raise dd.Error(
            title='timed out creating snapshots',
            text='timed out creating snapshot for {}'.format(instance_id))

    logging.info('Finished creating snapshot %s for volume %s',
                 snap.id,
                 volume_id)

    snap.add_tags({
        'env': env,
        'service': service,
        'type': 'mongo',
        'instance': instance_id,
        'created': datetime.datetime.utcnow().isoformat(),
    })


def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)s '
               '[%(module)s.%(funcName)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--region', required=True)
    parser.add_argument('--service', required=True)
    parser.add_argument('--instance-id', required=True)
    parser.add_argument('--ttl', type=int, default=14)
    args = parser.parse_args()

    try:
        backup(
            region=args.region,
            env=args.env,
            service=args.service,
            instance_id=args.instance_id,
            ttl=args.ttl)
    except dd.Error as err:
        err.report()
        return 1
    except Exception as err:
        dd.report('exception thrown backing up {}'.format(args.service))
        raise
    else:
        return 0

if __name__ == '__main__':
    sys.exit(main())
