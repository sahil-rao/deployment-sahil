# (c) Copyright 2016 Cloudera, Inc. All rights reserved.

"""
Template API endpoint.
This is used as an example for creating a new endpoint to point to a system.
"""
import sys
from pprint import pprint
import requests
import logging


def execute(tenantid, msg_dict):
    """
    All endpoints must contain an execute function that takes in two parameters.
    tenantid: This will be used to identify the account to do an action on.
    msg_dict: This will be used to pass in execution time variables.

    """
    '''
    Extract the variables from the msg_dict.
    '''
    navigator_url = msg_dict['navigator_url']
    login = msg_dict['login']
    password = msg_dict['password']
    entity_limit = msg_dict['entity_limit']
    entity_offset = msg_dict['entity_offset']

    '''
    Identify the version.
    Make an api get request for the data using the version.
    '''

    version_url = navigator_url + '/api/version'
    r = requests.get(version_url, auth=(login, password))
    if r.status_code == 200:
        version = r.text
    else:
        return 'failed in version api: got error code %s' % (r.status_code)

    api_msg_dict = "/api/"+version+"/interactive/entities?limit=" + str(entity_limit) + "&offset=" + str(entity_offset)
    full_url = navigator_url + api_msg_dict
    r = requests.get(full_url, auth=(login, password))
    if r.status_code == 200:
        data = r.json()
    else:
        logging.error('fail in query api: got error code %s' % (r.status_code))
        return {}
    return data

if __name__ == '__main__':
    tenantid = 'xplain'
    msg_dict = {'navigator_url': 'http://sudhanshu-navopt.vpc.cloudera.com:7187',
                'login': 'admin',
                'password': 'admin',
                'entity_limit': 0,
                'entity_offset': 0}

    pprint(execute(tenantid, msg_dict))
