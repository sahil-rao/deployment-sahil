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
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
import json
from flightpath.Provenance import getMongoServer
import flightpath.thriftclient.compilerthriftclient as tclient
import sys
import flightpath.utils as utils
import socket

# A utility function to build top level and sub operator from the query entity


def getQueryOperatorSignature(queryEntity, db, redis_conn, min_max, compiler_to_use, params):
    stmtOps = {'SELECT': 'SELECT', 'INSERT': 'INSERT', 'UPDATE': 'UPDATE', 'DELETE': 'DELETE', 'CREATE': 'CREATE', 'CREATE_TABLE': 'CREATE'}
    clauseOps = {'GROUP BY': 'AGGREGATE', 'JOIN': 'JOIN', 'WHERE': 'FILTER', 'ORDER BY': 'SORT'}
    exprOps = {'CASE': 'CASE', 'HAVING': 'HAVING', 'VIEW': 'VIEW'}

    # initialize all possible signatures to empty strings
    stmtSignature = "UNKNOWN"
    clauseSignature = "NONE"
    exprSignature = "UNKNOWN"
    queryExecutionScore = 0
    queryComplexityScore = 0
    signatureKeywords = []
    union_query_block = []
    union_all_query_block = []
    tables = []
    selectCount = 0
    joinCount = 0
    orderByCount = 0
    filterCount = 0
    groupByCount = 0
    queryEntityGSP = None
    complexityCharacter = None
    normComplexity = None
    queryTemp = ""
    sqlSummary = "Summary not computed for Impala/Hive workloads."
    # Check whether the gsp profile exists for this query entity object
    if "Compiler" in queryEntity['profile'] and compiler_to_use in queryEntity['profile']['Compiler']:
        queryEntityGSP = queryEntity['profile']['Compiler'][compiler_to_use]

        # Extract a logical signature by concatenating
        operatorList = queryEntityGSP['OperatorList']
        queryExecutionScore = queryEntityGSP['ExecutionTimeScore']
        queryComplexityScore = queryEntityGSP['ComplexityScore']
        normComplexity = (queryComplexityScore - min_max["num_diff"])/min_max["den"]

        if normComplexity <= .25:
            complexityCharacter = "Low"
        elif normComplexity <= .75:
            complexityCharacter = "Medium"
        else:
            complexityCharacter = "High"

        if "queryTemplate" in queryEntityGSP:
            queryTemp = queryEntityGSP["queryTemplate"]

        if "combinedQueryList" in queryEntityGSP:
            for entry in queryEntityGSP["combinedQueryList"]:
                if entry["combinerClause"] == "UNION":
                    union_query_block.append(entry["combinedQuery"])
                elif entry["combinerClause"] == "UNION_ALL":
                    union_all_query_block.append(entry["combinedQuery"])

        for operator in operatorList:
            # Use the statement and clause dictionaries to map the operator
            stmtOp = stmtOps.get(operator, "NOT_STMT_OPERATOR")
            clauseOp = clauseOps.get(operator, "NOT_CLAUSE_OPERATOR")

            if stmtOp != "NOT_STMT_OPERATOR":
                # We only want the first statement level operator as part of the
                # top signature.
                if stmtSignature == "UNKNOWN":
                    stmtSignature = stmtOp
            else:
                if clauseOp != "NOT_CLAUSE_OPERATOR":
                    if clauseSignature == "NONE":
                        clauseSignature = clauseOp
                    else:
                        clauseSignature = clauseSignature + "-" + clauseOp
                else:
                    if exprSignature == "UNKNOWN":
                        exprSignature = operator
                    else:
                        exprSignature = exprSignature + "-" + operator

    if "selectCount" in queryEntity['profile']:
        selectCount = queryEntity['profile']['selectCount']

    if "joinCount" in queryEntity['profile']:
        joinCount = queryEntity['profile']['joinCount']

    if "orderbyCount" in queryEntity['profile']:
        orderByCount = queryEntity['profile']['orderbyCount']

    if "whereCount" in queryEntity['profile']:
        filterCount = queryEntity['profile']['whereCount']

    if "groupbyCount" in queryEntity['profile']:
        groupByCount = queryEntity['profile']['groupbyCount']

    subqueries = list(utils.get_all_subqueries(redis_conn, queryEntity['eid']))
    params['subqueries'] = subqueries

    subquery_cursor = db.entities.find({"eid": {"$in": subqueries}}, {"eid": 1, "profile.Compiler": 1,
                                               "profile.selectCount": 1, "profile.joinCount": 1, '_id': 0,
                                               "profile.orderbyCount": 1, "profile.whereCount": 1,
                                               "profile.groupbyCount": 1, 'compiler_to_use': 1})

    unique_union_count = 0
    total_union_count = 0
    unique_union_all_count = 0
    total_union_all_count = 0

    for subquery in subquery_cursor:
        if ("Compiler" in subquery['profile'] and
            compiler_to_use in subquery['profile']['Compiler']):
            subqueryEntityGSP = subquery['profile']['Compiler'][compiler_to_use]
            if "combinedQueryList" in subqueryEntityGSP:
                for entry in subqueryEntityGSP["combinedQueryList"]:
                    if entry["combinerClause"] == "UNION":
                        union_query_block.append(entry["combinedQuery"])
                    elif entry["combinerClause"] == "UNION_ALL":
                        union_all_query_block.append(entry["combinedQuery"])

        if 'profile' in subquery:

            if "selectCount" in subquery['profile']:
                selectCount += subquery['profile']['selectCount']

            if "joinCount" in subquery['profile']:
                joinCount += subquery['profile']['joinCount']

            if "orderbyCount" in subquery['profile']:
                orderByCount += subquery['profile']['orderbyCount']

            if "whereCount" in subquery['profile']:
                filterCount += subquery['profile']['whereCount']

            if "groupbyCount" in subquery['profile']:
                groupByCount += subquery['profile']['groupbyCount']

            profile = redis_conn.getEntityProfile(subquery["eid"])
            if 'list:union' in profile:
                unique_union_count += len(set(redis_conn.getListElems(profile['list:union'])))
                total_union_count += len(redis_conn.getListElems(profile['list:union']))
            if 'list:union_all' in profile:
                unique_union_all_count += len(set(redis_conn.getListElems(profile['list:union_all'])))
                total_union_all_count += len(redis_conn.getListElems(profile['list:union_all']))

    if queryEntityGSP and "sqlSummary" in queryEntityGSP:
        sqlSummary = queryEntityGSP["sqlSummary"]

    if 'character' in queryEntity['profile']:
        signatureKeywords = queryEntity['profile']['character']
    elif queryEntityGSP and "SignatureKeywords" in queryEntityGSP:
        signatureKeywords = queryEntityGSP["SignatureKeywords"]

    hive_compatible = 0
    if "Compiler" in queryEntity['profile'] and "hive" in queryEntity['profile']['Compiler']\
       and "ErrorSignature" in queryEntity['profile']['Compiler']['hive']:
        if len(queryEntity['profile']['Compiler']['hive']['ErrorSignature']) == 0:
            hive_compatible = 1

    querySignature = {}

    if "custom_id" in queryEntity:
        querySignature["customId"] = queryEntity['custom_id']

    q_profile = redis_conn.getEntityProfile(queryEntity["eid"])
    querySignature["instanceCount"] = 1
    if "instance_count" in q_profile:
        if q_profile["instance_count"] is None:
            entity_instances = db.entity_instances
            logging.info("No instance count for eid " + str(queryEntity["eid"]))
            q_profile["instance_count"] = int(entity_instances.find({"eid": queryEntity["eid"]}).count())
        querySignature["instanceCount"] = int(q_profile["instance_count"])

    if "total_elapsed_time" in q_profile:
        querySignature["averageElapsedTime"] = float(q_profile['total_elapsed_time']) / querySignature['instanceCount']
        querySignature["elapsedTimeUnit"] = 'ms'

    profile = redis_conn.getEntityProfile(queryEntity["eid"])
    if 'list:union' in profile:
        unique_union_count += len(set(redis_conn.getListElems(profile['list:union'])))
        total_union_count += len(redis_conn.getListElems(profile['list:union']))
    if 'list:union_all' in profile:
        unique_union_all_count += len(set(redis_conn.getListElems(profile['list:union_all'])))
        total_union_all_count += len(redis_conn.getListElems(profile['list:union_all']))

    querySignature['unique_union_count'] = unique_union_count
    querySignature['unionCount'] = total_union_count
    querySignature['unique_union_all_count'] = unique_union_all_count
    querySignature['unionAllCount'] = total_union_all_count
    querySignature['union_query_block'] = union_query_block
    querySignature['union_all_query_block'] = union_all_query_block

    relations_from = redis_conn.getRelationships(None, queryEntity['eid'], "READ")
    relations_to = redis_conn.getRelationships(queryEntity['eid'], None, "WRITE")
    tables += [{'eid': rel['start_en']} for rel in relations_from if {'eid': rel['start_en']} not in tables]
    tables += [{'eid': rel['end_en']} for rel in relations_to if {'eid': rel['end_en']} not in tables]

    querySignature["qid"] = queryEntity['eid']
    querySignature["StmtSignature"] = stmtSignature
    #querySignature["ClauseSignature"] = clauseSignature
    #querySignature["ExpressionSignature"] = exprSignature
    #querySignature["ExecutionTimeScore"] = queryExecutionScore
    #querySignature["ComplexityScore"] = queryComplexityScore
    querySignature["complexityCharacter"] = complexityCharacter
    #querySignature["normComplexity"] = normComplexity
    querySignature["tables"] = tables
    querySignature["selectCount"] = selectCount
    querySignature["joinCount"] = joinCount
    querySignature["orderByCount"] = orderByCount
    querySignature["filterCount"] = filterCount
    querySignature["groupByCount"] = groupByCount
    querySignature["hiveCompatible"] = hive_compatible
    querySignature["sqlSummary"] = sqlSummary
    querySignature["SignatureKeywords"] = signatureKeywords

    return querySignature

'''
Talks with compiler to get the start and end indices of inline view.
'''


def getInlineViewLocation(query, vendor):
    """
    Process now for Inline view DETECTION
    """

    data_dict = {"input_query": query, "source_platform": vendor, "Compiler": "gsp", "EntityId": "100", "TenantId": "100"}

    """ For iv detection the opcode is 8.
    """
    opcode = 8
    retries = 3
    response = tclient.send_compiler_request(opcode, data_dict, retries)
    if response.isSuccess == True:
        status = "SUCCESS"
    else:
        status = "FAILED"


    location_doc = None
    """ 4. Read the output file as a JSON.
    """

    if not response.isSuccess:
        logging.error("compiler request failed")
    else:
        location_doc = None
        location_doc = json.loads(response.result)
    return location_doc

def getCompatibilityStats(entities, redis_conn, qID, query_data, target_platform):
    """ 
    Build the compatibility data for front end view.
    The data format is for each "select", "from", "where", "groupby", other":
    { "select_count" : <number of failures in select",
      "unique_select_count" : <Unique select failures>,
      "select_clauses" : <failed clause string>,
      ...
    }
    Note for a query block to be present there must be a failure in it.
    If there are no failures in a block the output would not contain
    any key for that block.
    """
    # Reassigning for convenience
    t = target_platform

    """ 
    The following list of tuples define they keys that needs to be checked.
     (<redis key for HAQR clause>, <profile key for sub clause list>, <output key for failure count>,
    <output key for unique failure>, <output key for list of clause strings>)
    """
    # Reassigning for convenience
    t = target_platform
    
    key_list = [("HAQR{0}QueryByClauseSelectFailure".format(t),
                  "profile.Compiler.HAQR.platformCompilationStatus.{0}.clauseStatus.Select.subClauseList".format(t.title()),
                  "select_count", "unique_select_count", "select_clauses"),
                 ("HAQR{0}QueryByClauseFromFailure".format(t),
                  "profile.Compiler.HAQR.platformCompilationStatus.{0}.clauseStatus.From.subClauseList".format(t.title()),
                  "from_count", "unique_from_count", "from_clauses"),
                 ("HAQR{0}QueryByClauseGroupByFailure".format(t),
                  "profile.Compiler.HAQR.platformCompilationStatus.{0}.clauseStatus.Group By.subClauseList".format(t.title()),
                  "groupby_count", "unique_groupby_count", "groupby_clauses"),
                 ("HAQR{0}QueryByClauseWhereFailure".format(t),
                  "profile.Compiler.HAQR.platformCompilationStatus.{0}.clauseStatus.Where.subClauseList".format(t.title()),
                  "where_count", "unique_where_count", "where_clauses"),
                 ("HAQR{0}QueryByClauseOtherFailure".format(t),
                  "profile.Compiler.HAQR.platformCompilationStatus.{0}.clauseStatus.Other.subClauseList".format(t.title()),
                  "other_count", "unique_other_count", "other_clauses"),
                 ("HAQR{0}QueryByClauseUpdateFailure".format(t),
                  "profile.Compiler.HAQR.platformCompilationStatus.{0}.clauseStatus.Update.subClauseList".format(t.title()),
                  "update_count", "unique_update_count", "update_clauses"),
                 ("HAQR{0}QueryByClauseDeleteFailure".format(t),
                  "profile.Compiler.HAQR.platformCompilationStatus.{0}.clauseStatus.Delete.subClauseList".format(t.title()),
                  "delete_count", "unique_delete_count", "delete_clauses"),
                 ("HAQR{0}QueryByClauseColumnFailure".format(t),
                  "profile.Compiler.HAQR.platformCompilationStatus.{0}.clauseStatus.Col-List.subClauseList".format(t.title()),
                  "column_count", "unique_column_count", "column_clauses")
                ]
    query_info_dict = {}
    locations = []
    for key in key_list:
        clause_dict = redis_conn.getEntityProfile(qID, key[0])
        if clause_dict is not None and clause_dict[key[0]] is not None:
            query_info_dict[key[2]] = int(clause_dict[key[0]])

            HAQR = utils.get_dict_nested_value(query_data, key[1])
            if HAQR is None:
                logging.info("HAQR data not found")
            clause_set = set()
            failed_clauses = []
            if HAQR is not None:
                for clause in HAQR:
                    if clause["clauseStatus"] == "FAIL":
                        clause_set.add(clause["clauseHash"])
                        failed_clauses.append(clause["clauseString"])
                        if "errorDetail" in clause:
                            if "endLocator" in clause["errorDetail"] and "startLocator" in clause["errorDetail"]:
                                loc_tup = [clause["errorDetail"]["startLocator"],clause["errorDetail"]["endLocator"]]
                                locations.append(loc_tup)
            query_info_dict[key[3]] = len(clause_set)
            query_info_dict[key[4]] = failed_clauses
    query_info_dict["highLightInfo"] = locations
    status = True
    if 'profile' in query_data and 'Compiler' in query_data['profile'] and \
            target_platform in query_data['profile']['Compiler'] and \
            'ErrorSignature' in query_data['profile']['Compiler'][target_platform]:
        if len(query_data['profile']['Compiler'][target_platform]['ErrorSignature']) > 0:
            status = False

    if not status:
        if not query_info_dict:
            query_info_dict['other_count'] = 1
            query_info_dict['unique_other_count'] = 1
        query_info_dict['status'] = 'Failed'
    else:
        query_info_dict['status'] = 'Success'
    return query_info_dict


def execute(tenantid, msg_dict):
    '''
    Returns the details of the query with give entity_id.
    '''
    if msg_dict is None:
        return None

    entity_id = msg_dict['qid']
    client = getMongoServer(tenantid)

    db = client[tenantid]
    entities = db.entities
    params = {}

    redis_conn = RedisConnector(tenantid)

    query_data = entities.find_one({"eid": entity_id}, {"_id": 0, "eid": 1, "uid": 1, "name": 1, 'profile.Compiler': 1,
                  "custom_id": 1, 'profile.stats.ELAPSED_TIME': 1, 'profile.selectCount': 1, "eid": 1, 'profile.character': 1,
                 'profile.joinCount': 1, 'profile.groupbyCount': 1, 'profile.orderbyCount': 1, 'profile.whereCount': 1, 'compiler_to_use': 1,
                 'logical_name': 1})

    if query_data is None:
        return None

    compiler_to_use = query_data['compiler_to_use'] if 'compiler_to_use' in query_data else 'gsp'

    min_max = {"minComplexity": 0, "maxComplexity": sys.maxint}

    tempMin = redis_conn.getTopEtypeCounts("SQL_QUERY", 'ComplexityScore', -1, -1)

    tempMax = redis_conn.getTopEtypeCounts("SQL_QUERY", 'ComplexityScore', 0, 0)

    # this will only loop through once, but getTopEtypeCounts returns an array
    if tempMin is not None:
        for complexity in tempMin:
            min_max["minComplexity"] = complexity[1]
    if tempMax is not None:
        for complexity in tempMax:
            min_max["maxComplexity"] = complexity[1]

    if min_max["minComplexity"] == min_max["maxComplexity"]:
        if min_max["minComplexity"] != 0:
            min_max["den"] = min_max["minComplexity"]
        else:
            min_max["den"] = 1
        min_max["num_diff"] = 0
    else:
        min_max["num_diff"] = min_max["minComplexity"]
        min_max["den"] = (min_max["maxComplexity"] - min_max["minComplexity"])*1.0

    t_dict = getQueryOperatorSignature(query_data, db, redis_conn, min_max, compiler_to_use, params)

    impala_stats_dict = getCompatibilityStats(entities, redis_conn, entity_id, query_data, 'impala')
    t_dict['impala_stats'] = impala_stats_dict

    hive_stats_dict = getCompatibilityStats(entities, redis_conn, entity_id, query_data, 'hive')
    t_dict['hive_stats'] = hive_stats_dict

    vendor = utils.get_source_platform(db, query_data['uid'], {})

    iv_location = {}
    if 'logical_name' in query_data:
        iv_location = getInlineViewLocation(query_data['logical_name'], vendor)

    if 'formattedQuery' in iv_location:
        t_dict['name'] = iv_location['formattedQuery']
        del iv_location['formattedQuery']
    #t_dict['highLightInfo'] = iv_location

    tablesCopy = list(t_dict["tables"])

    for pos, table in enumerate(tablesCopy):
        table = entities.find_one({"eid": table['eid'], 'etype': "SQL_TABLE"},
                                  {"eid": 1, 'profile.table_type': 1, 'name': 1, 'description': 1, 'display_name': 1, "profile.is_inline_view": 1, "profile.is_view": 1})
        t_dict["tables"][pos]["tid"] = table['eid']
        t_dict["tables"][pos]["tableName"] = table['name']
        t_dict["tables"][pos]["tableType"] = 'Dimension'
        if 'profile' in table and 'table_type' in table['profile']:
            table_type = table['profile']['table_type']
            if table_type == "Fact":
                t_dict["tables"][pos]["type"] = "Fact"
            else:
                t_dict["tables"][pos]["type"] = "Dimension"

            t_dict["tables"][pos]['is_inline_view'] = False
            t_dict["tables"][pos]['is_view'] = False

            if 'profile' in table and 'is_inline_view' in table['profile']:
                t_dict["tables"][pos]['is_inline_view'] = table['profile']['is_inline_view']

            if 'profile' in table and 'is_view' in table['profile']:
                t_dict["tables"][pos]['is_view'] = table['profile']['is_view']

        if 'description' in table:
            t_dict['tables'][pos]['description'] = table['description']
        if 'display_name' in table:
            t_dict['tables'][pos]['display_name'] = table['display_name']
        t_dict["tables"][pos].pop("is_inline_view")
        t_dict["tables"][pos].pop("is_view")
        t_dict["tables"][pos].pop("eid")
        t_dict["tables"][pos].pop("type")
        #t_dict["tables"][pos].pop("name")

    t_dict["query"] = t_dict["name"]
    t_dict.pop("name")
    t_dict.pop("sqlSummary")
    t_dict.pop("union_query_block")
    t_dict.pop("union_all_query_block")
    t_dict.pop("unique_union_count")
    t_dict.pop("unique_union_all_count")
    t_dict.pop("complexityCharacter")
    t_dict.pop("hiveCompatible")
    t_dict["hiveCompatible"] = True
    if t_dict["hive_stats"]["status"] == 'Failed':
        t_dict["hiveCompatible"] = False
    t_dict["impalaCompatible"] = True
    if t_dict["impala_stats"]["status"] == 'Failed':
        t_dict["impalaCompatible"] = False
    t_dict.pop("hive_stats")
    t_dict.pop("impala_stats")
    return t_dict

if __name__ == '__main__':
    # print json.dumps(execute("137772ca-5025-ce93-4f34-d98e3ee92330","928801"), indent=2)
    a = json.dumps(execute("3d110d00-27e4-15a5-2b81-48ea0b6ecd7f", "31125"), indent=2)
    print a
