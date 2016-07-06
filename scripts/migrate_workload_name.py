# (c) Copyright 2015 Cloudera, Inc. All rights reserved.

"""
Application API to get top level stats about all users.
"""

import sys
import csv
import pprint
from flightpath.Provenance import getMongoServer
from flightpath.RedisConnector import RedisConnector


def execute(tennant_id, msg_dict):
    '''
    Returns information about all users in the system.
    '''
    XPLAIN = 'xplainIO'
    xplain_db = getMongoServer(XPLAIN)[XPLAIN]
    org_cursor = xplain_db.organizations.find({}, {"_id": 0})

    all_orgs = [x['guid'] for x in org_cursor]
    for tenant in all_orgs:
        tenant_db = getMongoServer(tenant)[tenant]
        workload = tenant_db.workload.find_one()
        if not workload:
            continue
        if 'workloadName' not in workload:
            continue
        workload_name = workload['workloadName']
        xplain_db.organizations.update({'guid': tenant}, {'$set': {'workloadName': workload_name}})
        print tenant

    return True

if __name__ == '__main__':
    tenantid = sys.argv[1]
    params = {}
    a = execute(tenantid, params)
    pprint.pprint(a)