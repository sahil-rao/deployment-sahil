import sys
import socket
import re
import os
from datetime import datetime as dt

from boto.route53.record import ResourceRecordSets
import boto.ec2.autoscale


SUFFIX = 'xplain.io'
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-west-1')


def get_new_service_num(route53_zone, db_silo_name, service_name):
    """
    If there exists a record like mongo3.dbsilo1.alpha.xplain.io, returns the next number (4)
    """
    # Match records belonging to the service for particular dbsilo and cluster
    match_regex = "(?<={0})\d+(?=\.{1}\.{2}\.?)" \
                  .format(service_name, db_silo_name, route53_zone.name)

    # Initialize with 0 because we want 1-indexing
    service_nums = [0]
    for record in route53_zone.get_records():
        match = re.search(match_regex, record.name)
        if match:
            service_num = int(match.group(0))
            service_nums.append(service_num)

    return max(service_nums) + 1


def record_exists(route53_zone, db_silo_name, service_name, ip):
    """
    Check if a record exists matching the service pattern with the current host's ip
    """
    # Match records belonging to the service for particular dbsilo and cluster
    match_regex = "{0}\d+\.{1}\.{2}\.?" \
                  .format(service_name, db_silo_name, route53_zone.name)

    for record in route53_zone.get_records():
        match = re.match(match_regex, record.name)
        if match and ip in record.resource_records:
            return True

    return False
    

def upsert_record(route53_zone, record_name, ip):
    """
    Creates record with record_name and ip; updates record if it already exists with different ip
    Does nothing if record already exists with same ip
    """
    record = route53_zone.get_a(record_name)
    
    if record and ip not in record.resource_records:
        route53_zone.update_a(record_name, ip)
    elif not record:
        route53_zone.add_a(record_name, ip)
    else:
        pass

        
def register_host(cluster_name, db_silo_name, service_name, is_master=False):

    zone_name = "{0}.{1}".format(cluster_name, SUFFIX)
    my_ip = socket.gethostbyname(socket.gethostname())
    conn = boto.route53.connect_to_region(AWS_REGION)
    route53_zone = conn.get_zone(zone_name)

    if is_master:
        record_name = "{0}{1}.{2}.{3}".format(service_name, 'master',
                                              db_silo_name, zone_name)
        print str(dt.now()), "Registering host as", record_name        
        upsert_record(route53_zone, record_name, my_ip)

    if not record_exists(route53_zone, db_silo_name, service_name, my_ip):
        service_num = get_new_service_num(route53_zone, db_silo_name, service_name)
        record_name = "{0}{1}.{2}.{3}".format(service_name, service_num,
                                              db_silo_name, zone_name)
        print str(dt.now()), "Registering host as", record_name        
        upsert_record(route53_zone, record_name, my_ip)


        
if len(sys.argv) > 4 and sys.argv[4] == 'master':
    register_host(sys.argv[1], sys.argv[2], sys.argv[3], True)
else:
    register_host(sys.argv[1], sys.argv[2], sys.argv[3])


