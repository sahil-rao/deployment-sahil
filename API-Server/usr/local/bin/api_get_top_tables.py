#!/usr/bin/python

"""
Application API to get details for a the top dim tables.

"""
__author__ = 'Samir Pujari'
__copyright__ = 'Copyright 2014, Xplain.IO Inc.'
__license__ = ''
__version__ = '0.1'
__maintainer__ = 'Samir Pujari'
__email__ = 'samir@xplain.io'

from pymongo import MongoClient
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from json import *
from flightpath.Provenance import getMongoServer
import numpy as np
import json

def execute(tenantid, upload_id = None):
    '''
    Returns the top 10 Dimension tables sorted by query count.

    Each table in the array has the following information:

        name
        eid
        type
        query access percentage
        column count
        number of access patterns
    '''
    client = getMongoServer(tenantid)

    db = client[tenantid]
    entities = db.entities
    dashboard_data = db.dashboard_data

    redis_conn = RedisConnector(tenantid)

    found_count = 0
    
    TOTAL_QUERY_COUNT = 0
    TABLE_COUNT = redis_conn.getSortedSetCardinality("SQL_TABLE", 'instance_count')
    RETURN_LIST_LEN = 20
    MAX_FILTERS = 3

    dashboard_info = dashboard_data.find_one()
    if "TotalQueries" in dashboard_info:
        TOTAL_QUERY_COUNT = int(dashboard_info['TotalQueries'])

    final_list = []

    if TABLE_COUNT == 0:
        return final_list

    topTables = redis_conn.getTopEtypeCounts("SQL_TABLE", 'instance_count', 0, 99)

    for table in topTables:
        tableEid = table[0]
        table_info = entities.find_one({"eid":tableEid}, 
                            {"_id":0, "eid":1, "name":1, "profile":1, 'accessPatterns':1})

        if table_info is None or 'profile' not in table_info or \
            'table_type' not in table_info['profile']:
            continue

        if 'profile' in table_info and 'is_view' in table_info['profile'] and \
           table_info['profile']['is_view'] == True:
            continue

        if 'profile' in table_info and 'is_inline_view' in table_info['profile'] and \
           table_info['profile']['is_inline_view'] == True:
            continue

        found_count += 1
        ret_info = {"name": table_info['name'], "eid":table[0],
                    "total" :table[1], 'type': 'Dimension'}

        columns = redis_conn.getRelationships(table_info['eid'], None, "TABLE_COLUMN")
        patterns = redis_conn.getRelationships(table_info['eid'], None, "TABLE_ACCESS_PATTERN")
        ret_info['columnCount'] = len(columns)

        ret_info['patternCount'] = len(patterns)

        if 'profile' in table_info and \
            'table_type' in table_info['profile'] and \
            table_info['profile']['table_type'] != "Dim":
            ret_info["type"] = table_info['profile']['table_type']

        final_list.append(ret_info)

        if found_count == RETURN_LIST_LEN:
            return final_list

    return final_list

if __name__ == '__main__':
    print json.dumps(execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f"), indent=2)
