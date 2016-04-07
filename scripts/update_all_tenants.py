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
    client = getMongoServer('xplainIO')

    db = client['xplainIO']
    org_cursor = db.organizations.find({}, {"_id": 0})

    for org in org_cursor:
        tmp_tenant = org["guid"]
        tenant_client = getMongoServer(tmp_tenant)
        db = tenant_client[tmp_tenant]
        bucket_list = db.interactions.find_one({'statename': 'bucketList'})
        if bucket_list and 'items' in bucket_list:
            if len(bucket_list['items']) > 0 and bucket_list['items'][0]['listName'] == 'list1':
                bucket_list['items'][0]['listName'] = 'Default Design Block'
                db.interactions.update({'statename': 'bucketList'}, bucket_list)
                print tmp_tenant

if __name__ == '__main__':
    tenantid = sys.argv[1]
    params = {}
    a = execute(tenantid, params)
    pprint.pprint(a)