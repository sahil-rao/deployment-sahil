#!/usr/bin/python

import argparse
import dbsilo_redis
import dd
import logging
import sys


def run(args):
    running_instances = dbsilo_redis.get_instances(args.region, args.dbsilo)
    clients = dbsilo_redis.get_clients(args.dbsilo, running_instances, 6379)

    master = dbsilo_redis.get_master(clients)

    print 'primary:', master

    for client in clients:
        if master is client:
            continue

        print 'registering replica:', client
        client.slaveof(master.host, master.port)


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument('--region', required=True)
    parser.add_argument('--dbsilo', required=True)
    args = parser.parse_args()

    try:
        return run(args)
    except dd.Error as err:
        err.report()
        return 1


if __name__ == '__main__':
    sys.exit(main())
