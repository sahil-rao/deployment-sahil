# (c) Copyright 2015 Cloudera, Inc. All rights reserved.

"""
Script to extract fields Optimizer needs from Navigator all queries api output.

README

This script takes in a url, login, and password for a navigator instance.
The url, login, and platform are passed in.
The password is requested securely after the params are passed in.

Optimizer only wants the identity and the queryText fields.
If there are additional fields, we delete them.

Using the cleaned array, we write a new file named out_file_name.
This file can then be uploaded onto Optimizer.

Use the following configuration when uploading your file.

column delimiter    : ','
row delimiter       : '~~'

Column Name |   Column Type
----------------------------
identity    |   SQL ID
queryText   |   SQL FULLTEXT

"""

import sys
import csv
import json
import requests
import argparse
import getpass

DEFAULT_OUTPUT_FILENAME = 'navigator_optimizer_queries.csv'
DEFAULT_PLATFORM = 'hive'


def execute(params):
    try:
        '''
        Extract the variables from the params.
        '''
        navigator_url = params['navigator_url']
        out_file_name = params['out_file_name']
        login = params['login']
        password = params['password']
        platform = params['platform']

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

        api_params = "/api/"+version+"/entities/?query=%2BsourceType%3A"+platform+"%20%2Btype%3Aoperation&limit=1000&offset=0"
        full_url = navigator_url + api_params
        r = requests.get(full_url, auth=(login, password))
        if r.status_code == 200:
            data = r.json()
        else:
            return 'fail in query api: got error code %s' % (r.status_code)

        '''
        Write to the out_file_name.
        '''
        keys = ['identity', 'queryText']

        '''
        Removes extra keys from the user information dictionary
        '''
        for i, elem in enumerate(data):
            extras = set(elem.keys()) - set(keys)
            if extras:
                for x in extras:
                    del data[i][x]

        with open(out_file_name, 'wb') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, lineterminator='~~')
            dict_writer.writeheader()
            dict_writer.writerows(data)

        return 'success'
    except:
        return 'fail: %s'%(sys.exc_info())

if __name__ == '__main__':
    params = {}

    parser = argparse.ArgumentParser()
    parser.add_argument('--login', nargs=1, help='Navigator Username.')
    parser.add_argument('--url', nargs=1, help='Url for Navigator instance.')
    parser.add_argument('--out_file_name', nargs=1, help='Output file name.')
    parser.add_argument('--platform', nargs=1,
                        help='Platform to retrieve queries of, defaults to hive. [hive, impala]')
    args = parser.parse_args()

    if not args.login:
        raise Exception('fail: No login provided.')
    else:
        params['login'] = args.login[0]

    params['password'] = getpass.getpass('Password:')

    if not args.url:
        raise Exception('fail: No url provided.')
    else:
        params['navigator_url'] = args.url[0]

    if not args.out_file_name:
        params['out_file_name'] = DEFAULT_OUTPUT_FILENAME
    else:
        params['out_file_name'] = args.out_file_name[0]

    if not args.platform:
        params['platform'] = DEFAULT_PLATFORM
    else:
        params['platform'] = args.platform[0]

    print execute(params)
