#!/usr/bin/python

"""
Application API to get the counts for all tables.

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
from flightpath.Provenance import getMongoServer
import json

def run_workflow(tenantid, msg_dict):
    mongo_host = getMongoServer(tenantid)

    redis_conn = RedisConnector(tenantid)

    client = MongoClient(host=mongo_host)

    # Create alias for the tenant we are interested in
    db = client[tenantid]
    entities = db.entities

    table_cursor = entities.find({"etype":"SQL_TABLE"}, {'eid':1, 'name':1})

    all_tables = {}
    for table in table_cursor:
        all_columns = redis_conn.getRelationships(table['eid'], None, "TABLE_COLUMN")

        all_tables[table['name']] = all_columns

    print json.dumps(all_tables, indent = 2)
run_workflow('e3caad82-0edd-8e5b-d553-475230cb8494', {})