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

PAGINATION_LIMIT = 50

def execute(tenantid, msg_dict):
    '''
    Returns the details of the query with give entity_id.
    '''
    client = getMongoServer(tenantid)

    db = client[tenantid]
    entities = db.entities
    redis_conn = RedisConnector(tenantid)

    col_data = entities.find_one({"etype":"SQL_TABLE_COLUMN", "eid": msg_dict['cid']},
                             {"tableEid":1, "stats" : 1, "tableName":1, "columnName":1, "eid":1, "_id":0})
    return col_data

if __name__ == '__main__':
    pprint.pprint(execute(sys.argv[1], {'cid': '31742'}))
