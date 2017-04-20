# (c) Copyright 2017 Cloudera, Inc. All rights reserved.

"""
Script to get upload timings for a given tenant
Outputs to files: <tenantid>_<service name>_timings.csv
"""
from __future__ import print_function
from flightpath.RedisConnector import *

def execute(tenantid):
    redis_conn = RedisConnector(tenantid)
    for service_name in ['compile', 'math']:
        processing_times_key = "_".join([tenantid, service_name, "block_processing_times"])
        output_file = "_".join([tenantid, service_name, "timings"]) + ".csv"
        timings = redis_conn.r.hgetall(processing_times_key)

        print("Writing " + service_name + " timings")
        with open(output_file, "w") as f:
            print(",".join(["Query Block", "Average Processing Time"]), file=f)
            
            for k in sorted(timings.keys()):
                print(",".join([k, timings[k]]), file=f)

if __name__ == '__main__':
    tenantid = "4b1a2f74-bfd3-1e6d-db0f-51355bddb8dc"
    execute(tenantid)
