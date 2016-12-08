#!/usr/bin/python

"""
Application API to get details for a given SQL query
"""


from flightpath.MongoConnector import *
from flightpath.Provenance import getMongoServer
import flightpath.utils as utils
from flightpath.RedisConnector import *
import json
import datetime


def execute():
    '''
    Returns the details of the query with give entity_id.
    '''
    xplainIOdb = getMongoServer('xplainIO')['xplainIO']
    userCursor = xplainIOdb.users.find({}, {'_id': 0, 'organizations': 1,
                                            'email': 1, 'archived': 1,
                                            'signed_terms_timestamp': 1})

    IGNORE_DOMAINS = ['xplain.io', 'grr.la', 'zanzog.com', 'sharklasers.com',
                      'opayq.com', 'mailinator.com']

    ret_dict = {}
    for tenant_data in userCursor:

        if 'email' not in tenant_data:
            continue

        email = tenant_data['email']

        found_domain = [x for x in IGNORE_DOMAINS if x in email]
        if found_domain:
            continue

        if 'signed_terms_timestamp' in tenant_data:
            event_time = tenant_data['signed_terms_timestamp']/1000
            value = datetime.datetime.fromtimestamp(event_time)
            ret_dict[email] = value.strftime('%Y-%m-%d %H:%M:%S')
            continue

        is_found = False
        if 'organizations' not in tenant_data or 'email' not in tenant_data:
            continue
        archived = tenant_data['archived'] if 'archived' in tenant_data else []
        all_orgs = tenant_data['organizations'] + archived
        for tenant in all_orgs:
            db = getMongoServer(tenant)[tenant]

            events = db.events
            events_cursor = events.find({})
            for event in events_cursor:
                if 'event' not in event:
                    continue
                if event['event'] == "user accepted terms and conditions":
                    event_time = event['timestamp']/1000
                    value = datetime.datetime.fromtimestamp(event_time)
                    ret_dict[email] = value.strftime('%Y-%m-%d %H:%M:%S')
                    is_found = True
                    break
            if is_found:
                break
    return ret_dict

if __name__ == '__main__':
    t_dict = execute()
    for x in t_dict:
        print '%s, %s'%(x, t_dict[x])