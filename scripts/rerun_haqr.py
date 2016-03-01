# (c) Copyright (2015) Cloudera, Inc. All rights reserved.

"""
Script to rerun haqr on all queries in the workload.
"""

import sys
sys.path.append('/usr/local/bin/')
import logging
from flightpath.RedisConnector import RedisConnector
from pymongo import MongoClient
from flightpath.Provenance import getMongoServer
import flightpath.utils as utils
import flightpath.thriftclient.compilerthriftclient as tclient
from json import loads, dumps

def analyzeHAQR(query, platform, tenant, eid, source_platform, db, redis_conn):
    if platform not in ["impala", "hive"]:
        return #currently HAQR supported only for impala

    query = query.encode('ascii', 'ignore')
    queryFsmFile = "/etc/xplain/QueryFSM.csv";
    selectFsmFile = "/etc/xplain/SelectFSM.csv";
    whereFsmFile = "/etc/xplain/WhereFSM.csv";
    groupByFsmFile = "/etc/xplain/GroupbyFSM.csv";
    whereSubClauseFsmFile = "/etc/xplain/WhereSubclauseFSM.csv";
    fromFsmFile = "/etc/xplain/FromFSM.csv";
    selectSubClauseFsmFile = "/etc/xplain/SelectSubclauseFSM.csv";
    groupBySubClauseFsmFile = "/etc/xplain/GroupbySubclauseFSM.csv";
    fromSubClauseFsmFile = "/etc/xplain/FromSubclauseFSM.csv";

    data_dict = {
        "input_query": query,
        "EntityId": eid,
        "TenantId": tenant,
        "queryFsmFile": queryFsmFile,
        "selectFsmFile": selectFsmFile,
        "whereFsmFile": whereFsmFile,
        "groupByFsmFile": groupByFsmFile,
        "whereSubClauseFsmFile": whereSubClauseFsmFile,
        "fromFsmFile": fromFsmFile,
        "selectSubClauseFsmFile": selectSubClauseFsmFile,
        "groupBySubClauseFsmFile": groupBySubClauseFsmFile,
        "fromSubClauseFsmFile": fromSubClauseFsmFile,
        "target_platform": platform,
        "source_platform": source_platform
    }

    """
    For HAQR processing the opcode is 4.
    """
    opcode = 4
    retries = 3
    response = tclient.send_compiler_request(opcode, data_dict, retries)
    if response.isSuccess == True:
        logging.info("HAQR Got Done")
    else:
        logging.error("compiler request failed")
        return None

    data = None
    data = loads(response.result)

    logging.info(dumps(data))

    updateMongoRedisforHAQR(db,redis_conn,data,tenant,eid)

    return

def updateRedisforimpala(redis_conn, data, tenant, eid):
    if data['platformCompilationStatus']['Impala']['queryStatus']=="SUCCESS":
        redis_conn.incrEntityCounter("HAQR", "impalaSuccess", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "impalaFail", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Impala']['clauseStatus'] is not None and \
       'Select' in data['platformCompilationStatus']['Impala']['clauseStatus']:
        if data['platformCompilationStatus']['Impala']['clauseStatus']['Select']['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaSelectSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaSelectFail", sort=False, incrBy=1)
            if 'subClauseList' in data['platformCompilationStatus']['Impala']['clauseStatus']['Select']:
                for subClause in data['platformCompilationStatus']['Impala']['clauseStatus']['Select']['subClauseList']:
                    if subClause['clauseStatus']=="SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaSelectSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaSelectSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseSelectFailure", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Impala']['clauseStatus'] is not None and \
       'From' in data['platformCompilationStatus']['Impala']['clauseStatus']:
        if data['platformCompilationStatus']['Impala']['clauseStatus']['From']['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaFromSuccess", sort=False, incrBy=1)
        elif data['platformCompilationStatus']['Impala']['clauseStatus']['From']['clauseStatus']=="AUTO_SUGGEST":
            redis_conn.incrEntityCounter("HAQR", "impalaFromAutoCorrect", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaFromFailure", sort=False, incrBy=1)

        if 'subClauseList' in data['platformCompilationStatus']['Impala']['clauseStatus']["From"]:
            for subClause in data['platformCompilationStatus']['Impala']['clauseStatus']["From"]['subClauseList']:
                if subClause['clauseStatus']=="SUCCESS":
                    redis_conn.incrEntityCounter("HAQR", "impalaFromSubClauseSuccess", sort=False, incrBy=1)
                elif subClause['clauseStatus']=="AUTO_SUGGEST":
                    redis_conn.incrEntityCounter("HAQR", "impalaFromSubClauseAutoCorrect", sort=False, incrBy=1)
                else:
                    redis_conn.incrEntityCounter("HAQR", "impalaFromSubClauseFailure", sort=False, incrBy=1)
                    redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseFromFailure", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Impala']['clauseStatus'] is not None and \
       "Group By" in data['platformCompilationStatus']['Impala']['clauseStatus']:
        if data['platformCompilationStatus']['Impala']['clauseStatus']["Group By"]['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaGroupBySuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaGroupByFailure", sort=False, incrBy=1)
            if 'subClauseList' in data['platformCompilationStatus']['Impala']['clauseStatus']["Group By"]:
                for subClause in data['platformCompilationStatus']['Impala']['clauseStatus']["Group By"]['subClauseList']:
                    if subClause['clauseStatus']=="SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaGroupBySubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaGroupBySubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseGroupByFailure", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Impala']['clauseStatus'] is not None and \
       "Where" in data['platformCompilationStatus']['Impala']['clauseStatus']:
        if data['platformCompilationStatus']['Impala']['clauseStatus']["Where"]['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaWhereSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaWhereFailure", sort=False, incrBy=1)
            if 'subClauseList' in data['platformCompilationStatus']['Impala']['clauseStatus']["Where"]:
                for subClause in data['platformCompilationStatus']['Impala']['clauseStatus']["Where"]['subClauseList']:
                    if subClause['clauseStatus']=="SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaWhereSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaWhereSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseWhereFailure", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Impala']['clauseStatus'] is not None and \
        "Other" in data['platformCompilationStatus']['Impala']['clauseStatus']:
        if data['platformCompilationStatus']['Impala']['clauseStatus']["Other"]['clauseStatus']=="FAIL":
            redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseOtherFailure", sort=False, incrBy=1)
    return

def updateRedisforhive(redis_conn, data, tenant, eid):
    if data['platformCompilationStatus']['Hive']['queryStatus']=="SUCCESS":
        redis_conn.incrEntityCounter("HAQR", "hiveSuccess", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "hiveFail", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Hive']['clauseStatus'] is not None and \
       'Select' in data['platformCompilationStatus']['Hive']['clauseStatus']:
        if data['platformCompilationStatus']['Hive']['clauseStatus']['Select']['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveSelectSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveSelectFail", sort=False, incrBy=1)
            if 'subClauseList' in data['platformCompilationStatus']['Hive']['clauseStatus']['Select']:
                for subClause in data['platformCompilationStatus']['Hive']['clauseStatus']['Select']['subClauseList']:
                    if subClause['clauseStatus']=="SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "hiveSelectSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "hiveSelectSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseSelectFailure", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Hive']['clauseStatus'] is not None and \
       'From' in data['platformCompilationStatus']['Hive']['clauseStatus']:
        if data['platformCompilationStatus']['Hive']['clauseStatus']['From']['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveFromSuccess", sort=False, incrBy=1)
        elif data['platformCompilationStatus']['Hive']['clauseStatus']['From']['clauseStatus']=="AUTO_SUGGEST":
            redis_conn.incrEntityCounter("HAQR", "hiveFromAutoCorrect", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveFromFailure", sort=False, incrBy=1)

        if 'subClauseList' in data['platformCompilationStatus']['Hive']['clauseStatus']["From"]:
            for subClause in data['platformCompilationStatus']['Hive']['clauseStatus']["From"]['subClauseList']:
                if subClause['clauseStatus']=="SUCCESS":
                    redis_conn.incrEntityCounter("HAQR", "hiveFromSubClauseSuccess", sort=False, incrBy=1)
                elif subClause['clauseStatus']=="AUTO_SUGGEST":
                    redis_conn.incrEntityCounter("HAQR", "hiveFromSubClauseAutoCorrect", sort=False, incrBy=1)
                else:
                    redis_conn.incrEntityCounter("HAQR", "hiveFromSubClauseFailure", sort=False, incrBy=1)
                    redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseFromFailure", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Hive']['clauseStatus'] is not None and \
       "Group By" in data['platformCompilationStatus']['Hive']['clauseStatus']:
        if data['platformCompilationStatus']['Hive']['clauseStatus']["Group By"]['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveGroupBySuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveGroupByFailure", sort=False, incrBy=1)
            if 'subClauseList' in data['platformCompilationStatus']['Hive']['clauseStatus']["Group By"]:
                for subClause in data['platformCompilationStatus']['Hive']['clauseStatus']["Group By"]['subClauseList']:
                    if subClause['clauseStatus']=="SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "hiveGroupBySubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "hiveGroupBySubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseGroupByFailure", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Hive']['clauseStatus'] is not None and \
       "Where" in data['platformCompilationStatus']['Hive']['clauseStatus']:
        if data['platformCompilationStatus']['Hive']['clauseStatus']["Where"]['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveWhereSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveWhereFailure", sort=False, incrBy=1)
            if 'subClauseList' in data['platformCompilationStatus']['Hive']['clauseStatus']["Where"]:
                for subClause in data['platformCompilationStatus']['Hive']['clauseStatus']["Where"]['subClauseList']:
                    if subClause['clauseStatus']=="SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "hiveWhereSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "hiveWhereSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseWhereFailure", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Hive']['clauseStatus'] is not None and \
        "Other" in data['platformCompilationStatus']['Hive']['clauseStatus']:
        if data['platformCompilationStatus']['Hive']['clauseStatus']["Other"]['clauseStatus']=="FAIL":
            redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseOtherFailure", sort=False, incrBy=1)
    return

def updateMongoRedisforHAQR(db,redis_conn,data,tenant,eid):
    redis_conn.createEntityProfile("HAQR", "HAQR")

    redis_conn.incrEntityCounter("HAQR", "numInvocation", sort=False, incrBy=1)
    if data['sourceStatus']=='SUCCESS':
        redis_conn.incrEntityCounter("HAQR", "sourceSucess", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "sourceFailure", sort=False, incrBy=1)

    if 'platformCompilationStatus' in data and data['platformCompilationStatus']:
        if 'Impala' in data['platformCompilationStatus']:
            db.entities.update({'eid':eid},{"$set":{'profile.Compiler.HAQR.platformCompilationStatus':data['platformCompilationStatus']}})
        if 'Hive' in data['platformCompilationStatus']:
            db.entities.update({'eid':eid},{"$set":{'profile.Compiler.HAQR.platformCompilationStatus.Hive':data['platformCompilationStatus']['Hive']}})

    return

def process_HAQR_request(msg_dict):
    client = getMongoServer(msg_dict['tenant'])
    db = client[msg_dict['tenant']]
    redis_conn = RedisConnector(msg_dict['tenant'])
    analyzeHAQR(msg_dict['query'], msg_dict['key'], msg_dict['tenant'], \
                msg_dict['eid'], msg_dict['source_platform'], db, redis_conn)

def execute(tenantid, msg_dict={}):
    '''
    Returns the top 20 tables sorted by query count.
    '''
    client = getMongoServer(tenantid)
    db = client[tenantid]
    entities = db.entities
    dashboard_data = db.dashboard_data
    redis_conn = RedisConnector(tenantid)

    key = "impala"
    platform_map = {}

    query_cursor = db.entities.find({'etype': 'SQL_QUERY', 'profile.Compiler.gsp.ErrorSignature': ""},
                                    {'profile.Compiler': 1, 'eid': 1,
                                     'compiler_to_use': 1, 'uid': 1})
    for query in query_cursor:
        compiler_to_use = 'gsp'
        if 'compiler_to_use' in query:
            compiler_to_use = utils.get_compiler(query['compiler_to_use'])
        compile_doc = query['profile']['Compiler']
        if 'queryTemplate' not in compile_doc[compiler_to_use]:
            continue
        print query['eid']
        haqr_query = compile_doc[compiler_to_use]["queryTemplate"]
        eid = query['eid']
        source_platform = utils.get_source_platform(db, query['uid'], platform_map)
        adv_analy_dict = {'tenant': tenantid,
                          'query': haqr_query,
                          'key': key,
                          'eid' : eid,
                          'source_platform': source_platform,
                          'opcode': "HAQRPhase"}

        process_HAQR_request(adv_analy_dict)
    ret_dict = {}
    return ret_dict

if __name__ == '__main__':
    print execute(sys.argv[1], {})
