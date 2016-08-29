#!/usr/bin/python

import argparse
import navopt_redis
import dd
import logging
import sys


def run(args):
    running_instances = navopt_redis.get_instances(args.region, args.service)
    clients = navopt_redis.get_clients(args.service, running_instances, 6379)

    master = navopt_redis.get_master(clients)

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
    parser.add_argument('--service', required=True)
    args = parser.parse_args()

    try:
        return run(args)
    except dd.Error as err:
        err.report()
        return 1


if __name__ == '__main__':
    sys.exit(main())
