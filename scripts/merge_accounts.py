# (c) Copyright 2015 Cloudera, Inc. All rights reserved.

"""
Script to merge two user accounts.
"""

import sys
import csv
import pprint
from flightpath.Provenance import getMongoServer


def execute(msg_dict):
    '''
    Returns information about all users in the system.
    '''
    client = getMongoServer('xplainIO')

    db = client['xplainIO']
    if msg_dict['old_tenantid'] == msg_dict['merge_into_email']:
        return
    user = db.users.find_one({'email': msg_dict['merge_into_email']})
    if user:
        db.organizations.update({'guid': msg_dict['old_tenantid']},
                                {'$set': {'users': [msg_dict['merge_into_email']]}})
        db.users.update({'email': msg_dict['merge_into_email']},
                        {'$push': {'organizations': msg_dict['old_tenantid']}})
        db.users.remove({'email': msg_dict['old_email']})
    else:
        print msg_dict

if __name__ == '__main__':
    params = []
    for msg_dict in params:
        execute(msg_dict)