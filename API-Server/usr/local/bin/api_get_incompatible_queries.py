#!/usr/bin/python

"""
Application API to get details for incomaptible queries.
"""

from pymongo import MongoClient
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from json import *
from flightpath.Provenance import getMongoServer
from flightpath.services.app_get_query_detail import getCompatibilityStats
import numpy as np
import json

def execute(tenantid, msg_dict):
    '''
    Retrieves information about number of impala incompatibilities.
        Either all queries or queries related to patterns passed in.
    impala_incompatible :: number of impala incompatibilities.
    hive_incompatible :: number of hive incompatibilities.
    Number of errors in each clause. Total and Unique Errors.
    number of queries that can be auto_corrected.
    Number of unique queries that can't be auto_corrected.
    Top 10 queries by number of errors.
    '''
    entities = getMongoServer(tenantid)[tenantid].entities
    dashboard_data = getMongoServer(tenantid)[tenantid].dashboard_data
    redis_conn = RedisConnector(tenantid)

    t_dict = {}

    if 'targetPlatform' not in msg_dict or msg_dict['targetPlatform'] == 'impala':
        t_dict['impala'] = []
        #get impala incompatible query details
        query_cursor = entities.find({'parse_success':True, 'etype': 'SQL_QUERY', 'profile.Compiler.impala.ErrorSignature': {'$ne': ''}},{"_id": 0, "eid": 1, "uid": 1, "name": 1, 'profile.Compiler': 1})
        for query_data in query_cursor:
            impala_stats_dict = getCompatibilityStats(entities, redis_conn, query_data['eid'], query_data, 'impala')
            impala_stats_dict.pop('highLightInfo')
            if 'unique_other_count' in impala_stats_dict:
                impala_stats_dict.pop('unique_other_count')
            if 'unique_from_count' in impala_stats_dict:
                impala_stats_dict.pop('unique_from_count')
            if 'unique_select_count' in impala_stats_dict:
                impala_stats_dict.pop('unique_select_count')
            if 'unique_where_count' in impala_stats_dict:
                impala_stats_dict.pop('unique_where_count')
            if 'unique_orderby_count' in impala_stats_dict:
                impala_stats_dict.pop('unique_orderby_count')
            if 'unique_groupby_count' in impala_stats_dict:
                impala_stats_dict.pop('unique_groupby_count')
            impala_stats_dict.pop('status')
            impala_stats_dict['qid'] = query_data['eid']
            t_dict['impala'].append(impala_stats_dict)

    if 'targetPlatform' not in msg_dict or msg_dict['targetPlatform'] == 'hive':
        t_dict['hive'] = []
        #get impala incompatible query details
        query_cursor = entities.find({'parse_success':True, 'etype': 'SQL_QUERY', 'profile.Compiler.hive.ErrorSignature': {'$ne': ''}},{"_id": 0, "eid": 1, "uid": 1, "name": 1, 'profile.Compiler': 1})
        for query_data in query_cursor:
            hive_stats_dict = getCompatibilityStats(entities, redis_conn, query_data['eid'], query_data, 'hive')
            hive_stats_dict.pop('highLightInfo')
            if 'unique_other_count' in hive_stats_dict:
                hive_stats_dict.pop('unique_other_count')
            if 'unique_from_count' in hive_stats_dict:
                hive_stats_dict.pop('unique_from_count')
            if 'unique_select_count' in hive_stats_dict:
                hive_stats_dict.pop('unique_select_count')
            if 'unique_where_count' in hive_stats_dict:
                hive_stats_dict.pop('unique_where_count')
            if 'unique_orderby_count' in hive_stats_dict:
                hive_stats_dict.pop('unique_orderby_count')
            if 'unique_groupby_count' in hive_stats_dict:
                hive_stats_dict.pop('unique_groupby_count')
            hive_stats_dict.pop('status')
            hive_stats_dict['qid'] = query_data['eid']
            t_dict['hive'].append(hive_stats_dict)

    return t_dict

if __name__ == '__main__':
    print json.dumps(execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f", {}), indent=2)
    #print json.dumps(execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f", {'targetPlatform': 'impala'}), indent=2)
    #print json.dumps(execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f", {'targetPlatform': 'hive'}), indent=2)
