#!/usr/bin/python

import argparse
import dbsilo_redis
import dd
import logging
import sys


def run(args):
    running_instances = dbsilo_redis.get_instances(args.region, args.dbsilo)
    server_clients = dbsilo_redis.get_clients(
        args.dbsilo,
        running_instances,
        6379)

    master = dbsilo_redis.get_master(server_clients)
    sentinel = dbsilo_redis.RedisClient('localhost', 26379)

    master_name = 'redismaster.{}.{}'.format(args.dbsilo, args.zone)
    sentinel.sentinel_monitor(
        master_name,
        master.host,
        master.port,
        args.quorum_size)
    sentinel.sentinel_set(master_name, 'down-after-milliseconds', 30000)
    sentinel.sentinel_set(master_name, 'parallel-syncs', 1)
    sentinel.sentinel_set(master_name, 'failover-timeout', 180000)


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument('--region', required=True)
    parser.add_argument('--dbsilo', required=True)
    parser.add_argument('--zone', required=True)
    parser.add_argument('--quorum-size', required=True)
    args = parser.parse_args()

    try:
        return run(args)
    except dd.Error as err:
        err.report()
        return 1


if __name__ == '__main__':
    sys.exit(main())
