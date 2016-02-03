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
    activeUploads = db.activeUploadsUIDs

    return_list = []
    for user in org_cursor:
        tmp_tenant = user["guid"]
        active_uploads = activeUploads.find({'guid': tmp_tenant})

        if 'queries' in user:
            user['queries'] = int(user['queries'])
        else:
            user['queries'] = 0

        if active_uploads:
            redis_conn = RedisConnector(tmp_tenant)
        for active_upload in active_uploads:
            tmp_upload = redis_conn.getEntityProfile(active_upload["upUID"])
            if 'processed_queries' in tmp_upload:
                user['queries'] += int(tmp_upload["processed_queries"])

        return_list.append(user)

    keys = [u'users', u'isDemo', u'uploads',
            u'queries', u'scaleMode', u'guid',
            u'upLimit', u'lastTimeStamp']
    '''
    Removes extra keys from the user information dictionary
    '''
    for i, user in enumerate(return_list):
        extras = set(user.keys()) - set(keys)
        if extras:
            for x in extras:
                del return_list[i][x]

    '''
    Write to the people.csv file.
    '''
    with open('people.csv', 'wb') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(return_list)

    return return_list

if __name__ == '__main__':
    tenantid = sys.argv[1]
    params = {}
    a = execute(tenantid, params)
    print pprint.pprint(a)