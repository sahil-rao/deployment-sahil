# (c) Copyright 2015 Cloudera, Inc. All rights reserved.

"""
Application API to get information for the top parsed queries.
Done by either instance_count or total_elapsed_time.
"""

import sys
import collections
import operator
from flightpath.RedisConnector import RedisConnector
from flightpath.Provenance import getMongoServer
import flightpath.utils as utils
import json

RETURN_COUNT = 5
DEFAULT_COMPILER = 'gsp'
MIN_WORKLOAD_PERCENT = 0


def execute(tenantid, msg_dict):
    '''
    Takes the tenant id as an input
    returns the top queries in the workload.
    '''
    client = getMongoServer(tenantid)

    db = client[tenantid]
    entities = db.entities

    redis_conn = RedisConnector(tenantid)
    ret_list = []

    total_count = 0
    current_query_count = 0

    metric = 'instance_count'
    if 'metric' in msg_dict and msg_dict['metric']:
        metric = msg_dict['metric']

    '''
    Gets the correct count to make the pie chart on.
    '''
    dashboard_info = redis_conn.getEntityProfile('dashboard_data')
    if metric == 'total_elapsed_time':
        if 'total_elapsed_time' in dashboard_info:
            total_count = float(dashboard_info['total_elapsed_time'])
        else:
            return []
    elif metric == "instance_count":
        if 'TotalQueries' in dashboard_info:
            total_count = int(dashboard_info['TotalQueries'])
        else:
            return []
    else:
        if "total_"+metric in dashboard_info:
            total_count = int(dashboard_info["total_"+metric])
        else:
            if 'TotalQueries' in dashboard_info:
                total_count = int(dashboard_info['TotalQueries'])
            else:
                return []


    queries = redis_conn.getTopEtypeCounts("SQL_QUERY", metric,
                                                     0, RETURN_COUNT)
    query_eids = [x[0] for x in queries]

    '''
    Store mongo entity information into in memory dictionary.
    '''
    query_map = {}
    query_infos = entities.find({'eid': {'$in': query_eids},
                                 'parse_success': True},
                                {'custom_id': 1, 'profile.Compiler': 1,
                                 '_id': 0, 'profile.character': 1, 'profile.stats': 1,
                                 'compiler_to_use': 1, 'eid': 1})

    normalizer = utils.ComplexityScoreNormalizer(tenantid)

    for query in query_infos:
        query_map[query['eid']] = query

    for query in queries:
        q_eid = query[0]
        if q_eid not in query_map:
            continue

        query_info = query_map[q_eid]
        ret_dict = {'eid': q_eid, 'instanceCount': 0, 'character': [],
                    'elapsedTime': 0,
                    'hiveCompatible': False, 
                    'impalaCompatible': False}

        percent = 0
        redis_q_info = redis_conn.getEntityProfile(q_eid)
        if 'instance_count' in redis_q_info:
            ret_dict['instanceCount'] = float(redis_q_info['instance_count'])
            if metric == 'instance_count':
                percent = int(ret_dict['instanceCount']*1.0/total_count*100)
        if 'total_elapsed_time' in redis_q_info:
            ret_dict['elapsedTime'] = float(redis_q_info['total_elapsed_time'])
            if metric == 'total_elapsed_time':
                percent = int(ret_dict['elapsedTime']*1.0/total_count*100)

        '''
        Returning early if the percent is too low. No need to process further.
        '''
        if percent < MIN_WORKLOAD_PERCENT:
            break

        compiler_to_use = DEFAULT_COMPILER
        if 'compiler_to_use' in query_info:
            compiler_to_use = query_info['compiler_to_use']

        try:
            compile_doc = query_info['profile']['Compiler'][compiler_to_use]
        except KeyError:
            continue

        if 'profile' in query_info and 'character' in query_info['profile']:
            ret_dict['character'] = query_info['profile']['character']

        if "custom_id" in query_info:
            ret_dict["custom_id"] = query_info['custom_id']

        '''
        Normalizing complexity score across the workload.
        Using the feature scaling method.
        x' = (x - min(x)) / (max(x) - min(x))
        '''
        ret_dict['complexity'] = normalizer.normalize(compile_doc['ComplexityScore'])

        if 'profile' in query_info and 'Compiler' in query_info['profile']:
            if 'impala' in query_info['profile']['Compiler'] and 'ErrorSignature' in query_info['profile']['Compiler']['impala']:
                if query_info['profile']['Compiler']['impala']['ErrorSignature'] == "":
                    ret_dict['impalaCompatible'] = True
            if 'hive' in query_info['profile']['Compiler'] and 'ErrorSignature' in query_info['profile']['Compiler']['hive']:
                if query_info['profile']['Compiler']['hive']['ErrorSignature'] == "":
                    ret_dict['hiveCompatible'] = True

        ret_list.append(ret_dict)
        current_query_count += 1
        if current_query_count == RETURN_COUNT:
            break

    return ret_list

if __name__ == '__main__':
    tenantid = sys.argv[1]
    elapsedTime = False
    if len(sys.argv) > 2:
        elapsedTime = sys.argv[2]
    params = {'byElapsedTime': elapsedTime}
    a = execute(tenantid, params)
    print json.dumps(a, indent=2)
