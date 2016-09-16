#!/usr/bin/python

"""
Application API to get details for a given SQL query

"""
__copyright__ = 'Copyright 2014, Xplain.IO Inc.'
__license__ = ''
__version__ = '0.1'

from pymongo import MongoClient
from flightpath.MongoConnector import *
import json
from flightpath.Provenance import getMongoServer
import sys
import pprint
import flightpath.utils as utils
from flightpath.RedisConnector import *


def execute(tenantid, msg_dict):
    '''
    Returns the details of the query with give entity_id.
    '''
    client = getMongoServer(tenantid)
    redis_conn = RedisConnector(tenantid)
    db = client[tenantid]
    uploadStats = db.uploadStats

    is_active = True
    if 'inActive' in msg_dict:
        is_active = msg_dict['inActive']

    ret_list = []
    '''
    This case handles a request for summarized upload info
    '''
    if "workloadId" not in msg_dict:
        upload_cursor = uploadStats.find({'active':is_active},
            {"uid":1,"filename":1, "total_queries":1})
 
        for upload in upload_cursor:
            t_dict = {}
            if "uid" in upload:
                t_dict["workloadId"] = upload["uid"]
            if "filename" in upload:
                try:
                    t_dict["workloadName"] = upload["filename"].split("/")[2]
                except:
                    pass
            if "total_queries" in upload:
                t_dict["queries"] = upload["total_queries"]
            if t_dict is not None:
                ret_list.append(t_dict)
    else:
        is_detail = False
        if 'details' in msg_dict:
            is_detail = msg_dict['details']
        upload_cursor = uploadStats.find({'active':is_active, "uid":msg_dict["workloadId"]}, {"_id":0})
        for upload in upload_cursor:
            t_dict = {}
            if is_detail:
                upload["workloadName"] = upload["filename"].split("/")[2]
                upload["queries"] = upload["total_queries"]
                upload["workloadId"] = upload["uid"]
                upload.pop("uid")
                upload.pop("filename")
                upload.pop("total_queries")
                upload.pop("FPProcessing")
                upload.pop("Phase2MessageProcessed")
                upload.pop("Math")
                upload.pop("LastMessageProcessed")
                upload.pop("StatsFileProcessed")
                upload.pop("eid")
                upload.pop('Compiler')
                upload.pop('current_phase')
                ret_list.append(upload)
            else:
                if "uid" in upload:
                    t_dict["workloadId"] = upload["uid"]
                if "total_queries" in upload:
                    t_dict["queries"] = upload["total_queries"]
                if "source_plaform" in upload:
                    t_dict["source_platform"] = upload["source_platform"]
                if "status" in upload:
                    t_dict["status"] = upload["status"]
                if "filename" in upload:
                    t_dict["workloadName"] = upload["filename"].split("/")[2]
                if t_dict is not None:
                    ret_list.append(t_dict)
                 
    return ret_list 

if __name__ == '__main__':
    #pprint.pprint(execute(sys.argv[1], {}))      
    #pprint.pprint(execute(sys.argv[1], {'inActive': False}))      
    #pprint.pprint(execute(sys.argv[1], {'workloadId': 'd9808f72-143c-530b-0270-84d5fa3d5cdb'}))      
    pprint.pprint(execute(sys.argv[1], {'workloadId': '6df7063a-ed15-bea7-415b-86f641d23a15', 'details':True}))      
