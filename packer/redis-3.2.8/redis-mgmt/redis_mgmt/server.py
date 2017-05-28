#!/usr/bin/env python

import contextlib
import json
import logging
import redis
import redis.sentinel
import time
import urllib

LOG = logging.getLogger(__name__)
LOCAL_IP_URL = 'http://169.254.169.254/latest/meta-data/local-ipv4'


def is_master():
    # First, figure out if we think we are master.
    client = redis.StrictRedis(host='localhost', port=6379)
    role = client.info()['role']

    if role == 'master':
        # We think we are master, but it's possible we are a new instance. To be
        # safe, we'll check with the sentinel and see if the sentinel agrees
        # that we are master.

        with open('/etc/navoptenv.json') as f:
            env = json.load(f)
            master_name = env['redis_master_name']

        sentinel = redis.sentinel.Sentinel([(master_name, 26379)])
        master_address = sentinel.discover_master(master_name)

        with contextlib.closing(urllib.urlopen(LOCAL_IP_URL)) as f:
            local_ip = f.read()

        if master_address == (local_ip, 6379):
            # Ok, everyone agrees we're master.
            print 'yes'
        else:
            # Otherwise, we must be a new instance, so don't claim we're master.
            print 'no'
    else:
        print 'no'


def join_cluster():
    logging.basicConfig()

    with open('/etc/navoptenv.json') as f:
        env = json.load(f)
        server_port = env['redis_server_port']
        sentinel_port = env['redis_sentinel_port']
        master_name = env['redis_master_name']

    # First, connect to Redis and wait for it to load
    client = redis.StrictRedis(host='localhost', port=server_port)

    while client.info()['loading']:
        LOG.info('Waiting for redis server to finish loading')
        time.sleep(10)

    # Check the master sentinel to see if it has a quorum. Otherwise, error out.
    sentinel = redis.StrictRedis(master_name, sentinel_port)
    try:
        sentinel.execute_command('sentinel', 'ckquorum', master_name)
    except redis.ResponseError:
        sentinel_info = sentinel.sentinel_master(master_name)
        if sentinel_info['num-other-sentinels'] + 1 < sentinel_info['quorum']:
            LOG.exception('sentinel master is under quorum')
            return 1

    # Connect to the master sentinel so we can know who the real master is.
    master_sentinel = redis.sentinel.Sentinel([(master_name, sentinel_port)])

    try:
        master_address = master_sentinel.discover_master(master_name)
    except redis.sentinel.MasterNotFoundError:
        LOG.exception('sentinel %s not aware of master %s',
                      master_sentinel,
                      master_name)
        return 1

    info = client.info()
    role = info['role']

    if role == 'master':
        # If we think we're the master node, we need to check if the sentinel
        # agrees with us.
        with contextlib.closing(urllib.urlopen(LOCAL_IP_URL)) as f:
            local_ip = f.read()

        if master_address == (local_ip, server_port):
            # We are the master, so we're done.
            return

        # If we hit this point, we must be a brand new instance. Set it to be
        # the slave of this master. But before we do, just to be safe, we only
        # do this if we have no slaves of our own, and no records.
        if info['connected_slaves'] != 0:
            LOG.error('failed to make slave, has %s connected slaves',
                      info['connected_slaves'])
            return 1

        dbsize = client.dbsize()
        if dbsize != 0:
            LOG.error('failed to make slave, database is not empty: %s', dbsize)
            return 1

        LOG.info('setting server to be slave of %s', master_address)
        client.slaveof(master_address[0], master_address[1])

    elif role == 'slave':
        if master_address == (info['master_host'], info['master_port']):
            # We're following the right master, so we're done.
            return
        else:
            LOG.error('server thinks it is a slave, but tracking')
            return 1

    else:
        LOG.error('unexpected role %s', role)
        return 1
