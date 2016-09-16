#!/usr/bin/python

"""
Application API to get details for a given SQL query

"""
__author__ = 'Rituparna Agrawal'
__copyright__ = 'Copyright 2014, Xplain.IO Inc.'
__license__ = ''
__version__ = '0.1'
__maintainer__ = 'Rituparna Agrawal'
__email__ = 'parna@xplain.io'

from pymongo import MongoClient
from bson.objectid import ObjectId
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
import json
from flightpath.Provenance import getMongoServer
import flightpath.thriftclient.compilerthriftclient as tclient
import sys
import flightpath.utils as utils
import socket
import pprint
import time
import calendar

PAGINATION_LIMIT = 4

def execute(tenantid, msg_dict):
    '''
    Returns the details of the query with give entity_id.
    '''
    client = getMongoServer(tenantid)

    db = client[tenantid]
    entities = db.entities
    ret_dict = {}
    last_record = None
    redis_conn = RedisConnector(tenantid)
    ret_list = []

    if 'next' not in msg_dict:
        table_data = entities.find({"etype":"SQL_TABLE"}, {"eid": 1, "name": 1}).sort("_id", 1).limit(PAGINATION_LIMIT)
    else:
        table_data = entities.find({"_id": {'$gt':ObjectId(msg_dict['next'])}, "etype":"SQL_TABLE"}, {"eid": 1, "name": 1}).sort("_id", 1).limit(PAGINATION_LIMIT)
    for ret_count, table in enumerate(table_data):
        if ret_count == PAGINATION_LIMIT - 1:
            last_record = table['_id']
        table.pop("_id")
        ret_list.append(table)

    ret_dict['data'] = ret_list
    if last_record:
        ret_dict['next'] = str(last_record)
    return ret_dict

if __name__ == '__main__':
    print "First Four"
    pprint.pprint(execute(sys.argv[1], {}))
    print "Second Four"
    pprint.pprint(execute(sys.argv[1], {'since':'57c5d6efad9d8b693f569684'}))   
    print "Third Four"
    pprint.pprint(execute(sys.argv[1], {'since':'57c5d6efad9d8b693f5696a3'}))   
    print "Fourth Four"
    pprint.pprint(execute(sys.argv[1], {'since':'57c5d6f1ad9d8b693f5696ed'}))   
    '''
    print "Fifth Four"
    pprint.pprint(execute(sys.argv[1], {'since':'57c5d6f3ad9d8b693f56971b'}))
    print "Sixth Four"
    pprint.pprint(execute(sys.argv[1], {'since':'57c5d6f4ad9d8b693f569735'}))
    '''
