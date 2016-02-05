# (c) Copyright 2015 Cloudera, Inc. All rights reserved.

"""
Script to extract fields Optimizer needs from Navigator all queries api output.

README

This script takes in a file with in_file_name.
The expected format of in_file_name is [{},{},...].
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


def execute(in_file_name, out_file_name):
    try:
        '''
        Open the in_file_name.
        '''
        data = []
        with open(in_file_name) as data_file:
            data = json.load(data_file)

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
        return 'fail'

if __name__ == '__main__':
    in_file_name = sys.argv[1]
    out_file_name = sys.argv[2]
    print execute(in_file_name, out_file_name)
