#!/usr/bin/python

import argparse
import navopt_redis
import dd
import logging
import sys


def run(args):
    running_instances = navopt_redis.get_instances(args.region, args.service)
    server_clients = navopt_redis.get_clients(
        args.service,
        running_instances,
        6379)

    master = navopt_redis.get_master(server_clients)
    sentinel = navopt_redis.RedisClient('localhost', 26379)

    master_name = '{}-master.{}'.format(args.service, args.zone_name)
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
    parser.add_argument('--service', required=True)
    parser.add_argument('--zone-name', required=True)
    parser.add_argument('--quorum-size', required=True)
    args = parser.parse_args()

    try:
        return run(args)
    except dd.Error as err:
        err.report()
        return 1


if __name__ == '__main__':
    sys.exit(main())
