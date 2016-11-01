#!/usr/bin/env python

import sys
import os
import traceback
from datetime import datetime as dt
import boto.ec2.autoscale
import boto.utils

AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-west-1')
NUM_SLAVES = 2


def get_my_autoscale_group(autoscale_conn):
    
    my_instance_id = boto.utils.get_instance_metadata()['instance-id']
    for asg in autoscale_conn.get_all_groups():
        for inst in asg.instances:
            if inst.instance_id == my_instance_id:
                return asg

try:
    autoscale_conn = boto.ec2.autoscale.connect_to_region(AWS_REGION)
    my_autoscale_group = get_my_autoscale_group(autoscale_conn)
    if my_autoscale_group and my_autoscale_group.desired_capacity < NUM_SLAVES + 1:
        print str(dt.now()), "Launching slaves for master"
        my_autoscale_group.set_capacity(NUM_SLAVES + 1)
except Exception as e:
    print str(dt.now()), "Failed to launch slaves"
    traceback.print_exc()

        

