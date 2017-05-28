import json
import logging
import redis
import redis.sentinel
import time

LOG = logging.getLogger(__name__)


def join_cluster():
    logging.basicConfig()

    with open('/etc/navoptenv.json') as f:
        env = json.load(f)
        sentinel_port = env['redis_sentinel_port']
        master_name = env['redis_master_name']
        quorum_size = env['redis_quorum_size']

    client = redis.StrictRedis(host='localhost', port=sentinel_port)

    # check if the sentinel already has this master registered.
    try:
        client.sentinel_master(master_name)
    except redis.ResponseError:
        # Local sentinel not aware of this master, so lets set it up.
        pass
    else:
        # Local sentinel is already setup, so just exit.
        return

    LOG.info('registering sentinel master %s', master_name)

    # Check the master sentinel to see if it has a quorum. Otherwise, error out.
    sentinel = redis.StrictRedis(master_name, sentinel_port)
    try:
        sentinel.execute_command('sentinel', 'ckquorum', master_name)
    except redis.ResponseError:
        sentinel_info = sentinel.sentinel_master(master_name)
        if sentinel_info['num-other-sentinels'] + 1 < sentinel_info['quorum']:
            LOG.exception('sentinel master is under quorum')
            return 1

    # Connect to the master sentinel, and see if it knows about the master.
    master_sentinel = redis.sentinel.Sentinel([(master_name, sentinel_port)])

    try:
        master_host, master_port = master_sentinel.discover_master(master_name)
    except redis.sentinel.MasterNotFoundError:
        LOG.error('sentinel %s not aware of master %s',
                  master_sentinel,
                  master_name)
        return 1

    # Register the sentinel to track the master.
    client.sentinel_monitor(
        master_name,
        master_host,
        master_port,
        quorum_size)
    client.sentinel_set(
        master_name,
        'down-after-milliseconds',
        30000)
    client.sentinel_set(master_name, 'parallel-syncs', 1)
    client.sentinel_set(master_name, 'failover-timeout', 180000)
    client.sentinel_set(
        master_name,
        'client-reconfig-script',
        '/usr/local/bin/redis-sentinel-client-reconfig')
