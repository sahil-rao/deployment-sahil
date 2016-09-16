#!/usr/bin/python

"""
Application API to get details for a given SQL table.
"""

import json
from flightpath.MongoConnector import *
from flightpath.RedisConnector import RedisConnector
from flightpath.Provenance import getMongoServer
import flightpath.services.app_get_table_col_stats as get_table_column_stats
import flightpath.utils as utils


def recurse_and_find_child(entities, redis_conn, eid, is_iview=False):
    child_list = []
    child = {}
    if is_iview:
        table_list = redis_conn.getRelationships(eid, None, "IVIEW_TABLE")
    else:
        table_list = redis_conn.getRelationships(eid, None, "VIEW_TABLE")
    if table_list is None:
        return None
    for eid in table_list:
        view_table = entities.find_one({"eid": eid})
        if view_table is not None:
            child['name'] = view_table['name']
            child['type'] = view_table['profile']['type']
            child['eid'] = view_table['eid']
            if is_iview:
                is_inline_view = False
                if 'profile' in tbl and 'is_inline_view' in tbl['profile']:
                    is_inline_view = tbl['is_inline_view']
                child['is_inline_view'] = is_inline_view
            else:
                is_view = False
                if 'profile' in tbl and 'is_view' in tbl['profile']:
                    is_view = tbl['is_view']
                child['is_view'] = is_view
            child['children'] = recurse_and_find_child(entities, redis_conn, view_table['eid'], is_iview)
            child_list.append(child)
            return child_list

def get_view_child_and_ddl(entities, redis_conn, table, is_view):
    child_list = []
    child = {}
    view_ddl = None
    if is_view:
        #found a view, get list of table eid...
        table_list = redis_conn.getRelationships(table['eid'], None, "VIEW_TABLE")
    else:
        #found a view, get list of table eid...
        table_list = redis_conn.getRelationships(table['eid'], None, "IVIEW_TABLE")

    for entry in table_list:
        view_table = entities.find_one({"eid": entry['end_en']})
        if view_table is not None:
            child['name'] = view_table['name']
            child['table_type'] = view_table['profile']['table_type']
            child['eid'] = view_table['eid']
            child['eid'] = view_table['eid']
            tmp_is_view = False
            if 'is_view' in view_table['profile']:
                tmp_is_view = view_table['profile']['is_view']
            if 'is_inline_view' in view_table['profile']:
                tmp_is_view = view_table['profile']['is_inline_view']
            if is_view:
                child['is_view'] = tmp_is_view
                child['children'] = recurse_and_find_child(entities, redis_conn, view_table['eid'])
            else:
                child['is_inline_view'] = tmp_is_view
                child['children'] = recurse_and_find_child(entities, redis_conn, view_table['eid'], True)
            child_list.append(child)
            child = {}

    query_rel = redis_conn.getRelationships(None, table['eid'], 'WRITE')
    for entry in query_rel:
        if 'start_en' in entry:
            view_query_detail_cursor = entities.find({"eid": entry['start_en']}, {'profile.Compiler':1, 'compiler_to_use':1})
            for view_query_detail in view_query_detail_cursor:
                compiler_to_use = view_query_detail['compiler_to_use'] if 'compiler_to_use' in view_query_detail else 'gsp'
                if 'profile' in view_query_detail and 'Compiler' in view_query_detail['profile'] and compiler_to_use in view_query_detail['profile']['Compiler']:
                    if 'queryTemplate' in view_query_detail['profile']['Compiler'][compiler_to_use]:
                        view_ddl = view_query_detail['profile']['Compiler'][compiler_to_use]['queryTemplate']
    return child_list, view_ddl

def execute(tenantid, msg_dict):
    '''
    Returns the details of the table with give entity_id.
    '''
    if 'eid' not in msg_dict:
        return

    entity_id = msg_dict['eid']
    client = getMongoServer(tenantid)

    db = client[tenantid]
    entities = db.entities

    redis_conn = RedisConnector(tenantid)
    normalizer = utils.ComplexityScoreNormalizer(tenantid)

    t_dict = {}

    table = entities.find_one({"eid": entity_id}, {"_id":0, "eid":1, "name":1, "profile.table_type":1, "profile.is_view":1, 
                               "profile.is_inline_view":1, 'accessPatterns':1, 'display_name':1, 'description':1, 'stats':1})
    if table is not None:
        accessPatterns = []

        prof_dict = redis_conn.getEntityProfile(entity_id)
        if prof_dict is not None and "instance_count" in prof_dict:
            value = prof_dict["instance_count"]
        else:
            value = 0

        semantically_unique_count = 0
        hive_success_count = 0
        column_count = 0
        joinCount = 0
        columns = []
        query_set = set()
        alias = []
        query_info_list = []
        selectCount = insertCount = updateCount = deleteCount = createCount = 0
        table_stats = {}
        column_stats = []
        child_list = []
        view_ddl = None
        iview_ddl = None
        table_ddl = None
        is_view = False
        is_inline_view = False

        if "is_view" in table['profile'] and table['profile']['is_view'] == True:
            is_view = True
            child_list, view_ddl = get_view_child_and_ddl(entities, redis_conn, table, is_view)
        elif "is_inline_view" in table['profile'] and table['profile']['is_inline_view'] == True:
            is_inline_view = True
            child_list, iview_ddl = get_view_child_and_ddl(entities, redis_conn, table, is_view)
        else:
            #this means its a table.
            query_rel = redis_conn.getRelationships(None, table['eid'], 'CREATE')
            for entry in query_rel:
                if 'start_en' in entry:
                    ddl_query_detail_cursor = entities.find({"eid": entry['start_en']}, {'profile.Compiler':1, 'compiler_to_use':1})
                    for ddl_query_detail in ddl_query_detail_cursor:
                        compiler_to_use = ddl_query_detail['compiler_to_use'] if 'compiler_to_use' in ddl_query_detail else 'gsp'
                        if 'profile' in ddl_query_detail and 'Compiler' in ddl_query_detail['profile'] and compiler_to_use in ddl_query_detail['profile']['Compiler']:
                            if 'queryTemplate' in ddl_query_detail['profile']['Compiler'][compiler_to_use]:
                                table_ddl = ddl_query_detail['profile']['Compiler'][compiler_to_use]['queryTemplate']

        if is_inline_view:
            #get alias for the table
            set_key = tenantid + ":eid:" + entity_id + ":list:iview_alias"
            table_alias = redis_conn.getListElems(set_key)
            set_alias = set(table_alias)
            alias = list(set_alias)

        if 'selectCount' in prof_dict:
            selectCount += int(prof_dict['selectCount'])
        if 'createCount' in prof_dict:
            createCount += int(prof_dict['createCount'])
        if 'insertCount' in prof_dict:
            insertCount += int(prof_dict['insertCount'])
        if 'updateCount' in prof_dict:
            updateCount += int(prof_dict['updateCount'])
        if 'deleteCount' in prof_dict:
            deleteCount += int(prof_dict['deleteCount'])

        relations_to = redis_conn.getRelationships(table['eid'], None, None)
        for rel in relations_to:
            if rel['rtype'] == 'TABLE_COLUMN':
                column_count = column_count + 1
                col = {
                        "groupbyCount" : 0,
                        "selectCount" : 0,
                        "filterCount" : 0,
                        "joinCount" : 0,
                        "orderbyCount" : 0,
                        "totalCount" :0,
                        "columnName" : rel["columnName"],
                        "columnEid" : rel["end_en"]
                        }
                if "GROUPBYCOUNT" in rel:
                    col["groupbyCount"] = int(rel["GROUPBYCOUNT"])
                    col["totalCount"] += int(rel["GROUPBYCOUNT"])
                if "SELECTCOUNT" in rel:
                    col["selectCount"] = int(rel["SELECTCOUNT"])
                    col["totalCount"] += int(rel["SELECTCOUNT"])
                if "FILTERCOUNT" in rel:
                    col["filterCount"] = int(rel["FILTERCOUNT"])
                    col["totalCount"] += int(rel["FILTERCOUNT"])
                if "JOINCOUNT" in rel:
                    col["joinCount"] = int(rel["JOINCOUNT"])
                    col["totalCount"] += int(rel["JOINCOUNT"])
                    joinCount += int(rel["JOINCOUNT"])
                if "ORDERBYCOUNT" in rel:
                    col["orderbyCount"] = int(rel["ORDERBYCOUNT"])
                    col["totalCount"] += int(rel["ORDERBYCOUNT"])

                columns.append(col)

            elif rel['rtype'] in ['READ','WRITE']:
                semantically_unique_count += 1
                query_set.add(rel['end_en'])
            elif rel['rtype'] == "TABLE_ACCESS_PATTERN":
                accessPatterns.append(rel['end_en'])

            if 'hive_compatible' in rel:
                hive_success_count = hive_success_count + rel['hive_compatible']

        ttype = None
        relations_from = redis_conn.getRelationships(None, table['eid'], None)
        for rel in relations_from:
            #only count outer query for inline view
            if is_inline_view:
                if "OQ_IVIEW" in rel['rtype']:
                    semantically_unique_count += 1
                    query_set.add(rel['start_en'])
            elif rel['rtype'] in ['READ','WRITE']:
                semantically_unique_count += 1
                query_set.add(rel['start_en'])

            if 'hive_compatible' in rel:
                hive_success_count = hive_success_count + int(rel['hive_compatible'])

        if 'profile' in table and 'table_type' in table['profile']:
            if table['profile']['table_type'] == "Dim":
                ttype = "Dimension"
            elif table['profile']['table_type'] == "Fact":
                ttype = "Fact"

        '''
        Related query information.
        '''
        total_query_count = 0
        for qEid in query_set:
            redis_query_info = redis_conn.getEntityProfile(qEid)
            if 'instance_count' in redis_query_info:
                total_query_count += int(redis_query_info['instance_count'])


        if 'stats' in table:
            table_stats = table['stats']

        column_stats = []
        all_column_info = get_table_column_stats.execute(tenantid, {'tableEIDs': [entity_id]})
        if all_column_info is not None and table['name'] in all_column_info:
            column_stats = all_column_info[table['name']]

        #count outer query instance count for inline view
        if is_inline_view:
            value = total_query_count

        #This list is used for the column access chart
        t_dict = {"name": table['name'], 'queryCount': value,
                  "type": table['profile']['table_type'],
                  "tid": table["eid"],
                  'columnCount': column_count,
                  'joinCount': joinCount,
                  "selectCount": selectCount, "createCount": createCount,
                  "insertCount": insertCount, "updateCount": updateCount,
                  "deleteCount": deleteCount, 'tableStats': table_stats,
                  'columnStats': column_stats['columns'],
                  'view_ddl': view_ddl, 'table_ddl': table_ddl,
                  'iview_ddl': iview_ddl}

        if ttype is not None:
            t_dict['type'] = ttype
        if 'description' in table:
            t_dict['description'] = table['description']
        if 'display_name' in table:
            t_dict['display_name'] = table['display_name']

    return t_dict

if __name__ == '__main__':
    print json.dumps(execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f", {"eid":"31718"}), indent=2)
