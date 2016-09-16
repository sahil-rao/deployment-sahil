#!/usr/bin/python
"""
Application API to information for the desired columns histogram.
"""
__author__ = 'Prithviraj Pandian'
__copyright__ = 'Copyright 2014, Xplain.IO Inc.'
__license__ = ''
__version__ = '0.1'
__maintainer__ = 'Prithviraj Pandian'
__email__ = 'prithvi@xplain.io'

from pymongo import MongoClient
from flightpath.RedisConnector import RedisConnector
from flightpath.Provenance import getMongoServer
import json

def execute(tenantid, msg_dict):
    '''                                                                                                                                                                                                                                                                           Takes the tenant id as an input then returns the top select columns                                                                                                                                                                                                           '''
    client = getMongoServer(tenantid)
    db = client[tenantid]
    entities = db.entities

    redis_conn = RedisConnector(tenantid)

    ret_dict = {}
    if 'opType' not in msg_dict:
        potential_operators = ["SELECTCOUNT", "JOINCOUNT", "FILTERCOUNT",
                            "ORDERBYCOUNT", "GROUPBYCOUNT"]
    else:
        potential_operators = [msg_dict['opType'].upper()+'COUNT']

    for operator in potential_operators:
        ret_list = []
        columns = redis_conn.getTopEtypeCounts("SQL_TABLE_COLUMN", operator, 0, 9)
        column_eid_list = [col[0] for col in columns]
        tableeid_type_map = {}
        tableeid_view_map = {}
        tableeid_iview_map = {}
        mongo_column_cursor = entities.find({"eid": {"$in": column_eid_list}, "tableEid": {"$exists": True}}, {'eid': 1, 'columnName':1, 'tableName':1, 'tableEid':1, '_id':0})
        for colinfo in mongo_column_cursor:
            column_dict = {
                'columnName': colinfo['columnName'],
                'tableName': colinfo['tableName'],
                'cid': colinfo['eid'],
                'tid': colinfo['tableEid'],
                'columnCount': dict(columns)[colinfo['eid']]
            }
            redis_column_info = redis_conn.getEntityProfile(colinfo['eid'])
            for op in potential_operators:
                key = op.lower()
                key = key.replace("count", "Count")
                column_dict[key] = int(redis_column_info[op]) if op in redis_column_info else 0
            tableeid_type_map[colinfo['tableEid']] = 'Dim'
            tableeid_view_map[colinfo['tableEid']] = False
            tableeid_iview_map[colinfo['tableEid']] = False
            ret_list.append(column_dict)

        mongo_table_cursor = entities.find({'etype':"SQL_TABLE","eid": {"$in": tableeid_type_map.keys()}}, {'_id':0, 'eid':1, "profile":1, 'name':1})
        for tblinfo in mongo_table_cursor:
            tableeid_type_map[tblinfo['eid']] = tblinfo['profile']['table_type']
            if 'is_view' in tblinfo['profile']:
                tableeid_view_map[tblinfo['eid']] = tblinfo['profile']['is_view']
            if 'is_inline_view' in tblinfo['profile']:
                tableeid_iview_map[tblinfo['eid']] = tblinfo['profile']['is_inline_view']

        for col_dict in ret_list:
            col_dict['tableType'] = tableeid_type_map[col_dict['tid']]

        operator_type = operator.lower()
        operator_type = operator_type.replace("count", "Columns")
        ret_dict[operator_type] = sorted(ret_list, key=lambda e: e['columnCount'], reverse=True)

    return ret_dict
if __name__ == '__main__':
    print json.dumps(execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f", {}), indent=2)
    #print "NEXT"
    #print json.dumps(execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f", {'opType':'join'}), indent=2)
