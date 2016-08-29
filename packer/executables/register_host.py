#!/usr/bin/python

from datetime import datetime as dt
import argparse
import boto.ec2.autoscale
import boto.route53
import re
import socket
import sys


def get_new_service_num(route53_zone, service_name):
    """
    If there exists a record like mongo3.dbsilo1.alpha.xplain.io, returns the
    next number (4)
    """

    # Match records belonging to the service for particular dbsilo and cluster
    match_regex = "(?<={})\d+(?=\.{}\.?)" \
                  .format(service_name, route53_zone.name)

    # Initialize with 0 because we want 1-indexing
    service_nums = [0]
    for record in route53_zone.get_records():
        match = re.search(match_regex, record.name)
        if match:
            service_num = int(match.group(0))
            service_nums.append(service_num)

    return max(service_nums) + 1


def record_exists(route53_zone, service_name, ip):
    """
    Check if a record exists matching the service pattern with the current
    host's ip
    """
    # Match records belonging to the service for particular dbsilo and cluster
    match_regex = "{}\d+\.{}\.?".format(service_name, route53_zone.name)

    for record in route53_zone.get_records():
        match = re.match(match_regex, record.name)
        if match and ip in record.resource_records:
            return True

    return False


def upsert_record(route53_zone, record_name, ip):
    """
    Creates record with record_name and ip; updates record if it already exists
    with different ip does nothing if record already exists with same ip
    """

    # Only upsert the dns record if it doesn't resolve to us.
    try:
        record_ip = socket.gethostbyname(record_name)
    except socket.error:
        # Ignore if we can't connect to the host
        pass
    else:
        if ip == record_ip:
            return

    print str(dt.now()), "Registering host as", record_name
    record = route53_zone.get_a(record_name)

    if record and ip not in record.resource_records:
        route53_zone.update_a(record_name, ip)
    elif not record:
        route53_zone.add_a(record_name, ip)


def register_host(region, service_name, zone_name, is_master=False):
    my_ip = socket.gethostbyname(socket.gethostname())
    conn = boto.route53.connect_to_region(region)
    route53_zone = conn.get_zone(zone_name)

    if is_master:
        record_name = "{}-master.{}".format(service_name, zone_name)
        upsert_record(route53_zone, record_name, my_ip)

    elif not record_exists(route53_zone, service_name, my_ip):
        service_num = get_new_service_num(
            route53_zone,
            service_name)

        record_name = "{}-{}.{}".format(service_name, service_num, zone_name)
        upsert_record(route53_zone, record_name, my_ip)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', required=True)
    parser.add_argument('--service', required=True)
    parser.add_argument('--zone', required=True)
    parser.add_argument('--master', action='store_true', default=False)
    args = parser.parse_args()

    register_host(
        region=args.region,
        service_name=args.service,
        zone_name=args.zone,
        is_master=args.master)


if __name__ == '__main__':
    sys.exit(main())
