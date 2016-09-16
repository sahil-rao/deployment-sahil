#!/usr/bin/python

"""
Application API to get details for a given SQL query

"""
__author__ = 'Samir Pujari'
__copyright__ = 'Copyright 2014, Xplain.IO Inc.'
__license__ = ''
__version__ = '0.1'
__maintainer__ = 'Samir Pujari'
__email__ = 'samir@xplain.io'

from pymongo import MongoClient
from flightpath.MongoConnector import *
import json
from flightpath.Provenance import getMongoServer
import sys
import pprint
import flightpath.utils as utils
from flightpath.RedisConnector import *

def get_phase_2_percent(upload):
    phase_2_percent = 0
    if 'Math' in upload:
        phase_2_workflows = 0
        for entry in upload['Math']:
            value = upload['Math'][entry]
            if isinstance(value, dict) and 'phase' in value and value['phase'] == "2":
                phase_2_workflows += 1

            #per workflow finished update percentage by 10 percent
            phase_2_percent = phase_2_workflows * 10
    return phase_2_percent

def get_failed_query_eid(entities, upload):
    failed_query_eid_list = []
    #no queries in case of stats file
    if "StatsFileProcessed" in upload:
        return failed_query_eid_list
    query_cursor = entities.find({'parse_success':False, 'etype': 'SQL_QUERY'},{'_id':0, 'eid':1})
    for query in query_cursor:
        failed_query_eid_list.append(query['eid'])
    return failed_query_eid_list

def execute(tenantid, msg_dict):
    '''
    Returns the details of the query with give entity_id.
    '''
    if 'workloadId' not in msg_dict:
        return

    upload_id = msg_dict['workloadId']
    client = getMongoServer(tenantid)
    redis_conn = RedisConnector(tenantid)
    db = client[tenantid]
    uploadStats = db.uploadStats

    upload = uploadStats.find_one({"uid":upload_id},
        {"uid":1,"filename":1, "timestamp":1, "Compiler":1, "source_platform":1,
         "Phase2MessageProcessed":1, "_id":0, "userSqlText":1, "limit_reached":1,
         "processed_queries":1, "total_queries":1, "StatsFileProcessed":1,
         "LastMessageProcessed":1, "Math":1})

    t_dict = {}
    uid = upload['uid']
    tmp_upload = redis_conn.getEntityProfile(uid)
    if tmp_upload:
        upload.update(utils.unflatten_dict(tmp_upload))
    if 'timestamp' in upload:
        upload['timestamp'] = float(upload['timestamp'])
    if 'LastMessageProcessed' in upload:
        upload['LastMessageProcessed'] = int(upload['LastMessageProcessed'])
    if 'Phase2MessageProcessed' in upload:
        upload['Phase2MessageProcessed'] = int(upload['Phase2MessageProcessed'])
    if 'total_queries' in upload:
        upload['total_queries'] = int(upload['total_queries'])
    if 'processed_queries' in upload:
        upload['processed_queries'] = int(upload['processed_queries'])
    if 'active' in upload:
        upload['active'] = bool(upload['active'])
    source_platform = None
    if 'source_platform' in upload:
        source_platform = upload['source_platform']
    compiler = utils.get_compiler(source_platform)

    if 'Compiler' in upload and compiler in upload['Compiler']:
        upload['compile_info'] = upload['Compiler'][compiler]
    else:
        upload['compile_info'] = {}

    if "Phase2MessageProcessed" in upload:
        '''
        This marks end of file processing
        '''
        upload['stage_one_process_per'] = 100
        upload['stage_two_process_per'] = 100
        #check for the case if no queries were detected
        if 'Compiler' not in upload:
            upload['status'] = 'failed'
        else:
            upload['status'] = 'finished'
        upload['failed_query_eid_list'] = get_failed_query_eid(db.entities, upload)
    elif "StatsFileProcessed" in upload and\
         ('processed_queries' not in upload and 'total_queries' not in upload):
        '''
        If the processed queries and total queries are not present then this is 
        stats only upload. It is possible to upload a tar file with stats and 
        queries. In which case, the percentage should come from the queries.

        This marks start of stats file processing
        '''
        upload['stage_one_process_per'] = 100
        upload['stage_two_process_per'] = 50
        upload['status'] = 'in-progress'
    elif 'processed_queries' in upload and 'total_queries' in upload:
        '''
        This marks begining of query file waiting and processing stage
        '''
        if upload['processed_queries'] == 0 or upload['total_queries'] == 0:
            upload['stage_one_process_per'] = 0
            upload['stage_two_process_per'] = 0
            upload['status'] = 'waiting'
        else:
            #calculate phase 1 time in percentage processed
            upload['stage_one_process_per'] = ((upload['processed_queries'] * 100) / 
                                                    upload['total_queries'])
            #calculate phase 2 time in percentage processed
            upload['stage_two_process_per'] = get_phase_2_percent(upload)
            upload['status'] = 'in-progress'
    else:
        #file processing not started yet
        upload['stage_one_process_per'] = 0
        upload['stage_two_process_per'] = 0
        upload['status'] = 'waiting'
    if 'Math' in upload: del upload['Math']
    t_dict['status'] = upload['status']
    t_dict['workloadId'] = upload['uid']

    return t_dict

if __name__ == '__main__':
    pprint.pprint(execute(sys.argv[1], {'workloadId':'9de753f6-9e51-4d77-ad37-e2581db87b35'}))
