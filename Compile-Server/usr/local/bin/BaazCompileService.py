#!/usr/bin/python

"""
Compile Service:
"""
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from flightpath.ScaleModeConnector import *
from flightpath.FilterModeConnector import *
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.RotatingS3FileHandler import *
from baazmath.workflows.hbase_analytics import *
from flightpath.utils import *
from flightpath.Provenance import getMongoServer
from flightpath.services.mq_template import *
from subprocess import Popen, PIPE
from json import *
import sys
import pika
import shutil
import os
import time
import datetime
import traceback
import re
import ConfigParser
import logging
import socket
import pprint

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"
BAAZ_COMPILER_LOG_FILE = "/var/log/BaazCompileService.err"

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
rabbitserverIP = config.get("RabbitMQ", "server")

usingAWS = config.getboolean("mode", "usingAWS")
if usingAWS:
    from boto.s3.key import Key
    import boto

CLUSTER_NAME = config.get("ApplicationConfig", "clusterName")

if CLUSTER_NAME is not None:
    bucket_location = CLUSTER_NAME

"""
For VM there is not S3 connectivity. Save the logs with a timestamp. 
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(BAAZ_COMPILER_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(BAAZ_COMPILER_LOG_FILE, BAAZ_COMPILER_LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=BAAZ_COMPILER_LOG_FILE,level=logging.INFO,datefmt='%m/%d/%Y %I:%M:%S %p')

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    file_bucket = boto_conn.get_bucket('xplain-compile')
    logging.getLogger().addHandler(RotatingS3FileHandler(BAAZ_COMPILER_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))

COMPILER_MODULES='/usr/lib/baaz_compiler'

dirList=os.listdir(COMPILER_MODULES)
classpath = ""
for fname in dirList:
    fullpath = os.path.join(COMPILER_MODULES, fname)
    if not os.path.isfile(fullpath):
        continue
    if not fullpath.lower().endswith(".jar"):
        continue
    classpath = classpath + fullpath + ":"

HIVE_MODULES='/usr/lib/hive/lib'
dirList=os.listdir(HIVE_MODULES)
for fname in dirList:
    fullpath = os.path.join(HIVE_MODULES, fname)
    if not os.path.isfile(fullpath):
        continue
    if not fullpath.lower().endswith(".jar"):
        continue
    classpath = classpath + fullpath + ":"

PIG_FEATURE = ['UNKNOWN', 'MERGE_JOIN', 'REPLICATED_JOIN', 'SKEWED_JOIN', 'HASH_JOIN',\
     'COLLECTED_GROUP', 'MERGE_COGROUP', 'COGROUP', 'GROUP_BY', 'ORDER_BY', 'DISTINCT', \
     'STREAMING', 'SAMPLING', 'MULTI_QUERY', 'FILTER', 'MAP_ONLY', 'CROSS', 'LIMIT', 'UNION',\
     'COMBINER']

table_regex = re.compile("([\w]*)\.([\w]*)")
myip = socket.gethostbyname(socket.gethostname())

def generatePigSignature(pig_data, tenant, entity_id):
    operations = []
    for i in range(0, len(PIG_FEATURE)):
        if (((pig_data >> i) & 0x00000001) != 0):
            operations.append(PIG_FEATURE[i])
    ret_dict = { 'EntityId':entity_id, 'TenentId': tenant, \
                 'ComplexityScore': len(operations),\
                 'InputTableList': [], 'OutputTableList': [],\
                 'Operations': operations}
    return ret_dict

def end_of_phase_callback(params, current_phase):
    if current_phase > 1:
        logging.info("Attempted end of phase callback, but current phase > 1")
        return

    logging.info("Changing processing Phase")
    msg_dict = {'tenant':params['tenant'], 'opcode':"PhaseTwoAnalysis"} 
    msg_dict['uid'] = params['uid']
    message = dumps(msg_dict)
    params['connection'].publish(params['channel'],'',params['queuename'],message)
    return
    
def processColumns(columnset, mongoconn, redis_conn, tenant, entity):
    tableCount = 0
    table_entity = None
    for column_entry in columnset:
        if "tableName" not in column_entry:
            continue

        tablename = column_entry["tableName"]
        columnname = column_entry["columnName"]
        table_entity = mongoconn.getEntityByName(tablename)

        column_entity_name = tablename.lower() + "." + columnname.lower()
        column_entity = mongoconn.getEntityByName(column_entity_name)

        if table_entity is None:
            logging.info("Creating table entity for {0} position 6\n".format(tablename))
            eid = IdentityService.getNewIdentity(tenant, True)
            table_entity = mongoconn.addEn(eid, tablename, tenant,\
                      EntityType.SQL_TABLE, {}, None)
            if eid == table_entity.eid:
                redis_conn.createEntityProfile(table_entity.eid, "SQL_TABLE")
                redis_conn.incrEntityCounter(table_entity.eid, "instance_count", sort=True, incrBy=0)
                tableCount = tableCount + 1

        if column_entity is None:
            logging.info("Creating Column entity for {0}\n".format(column_entity_name))
            eid = IdentityService.getNewIdentity(tenant, True)
            column_entry['tableEid'] = table_entity.eid
            column_entity = mongoconn.addEn(eid, column_entity_name, tenant,\
                            EntityType.SQL_TABLE_COLUMN, column_entry, None)

            if column_entity.eid == eid:
                logging.info("TABLE_COLUMN Relation between {0} {1}\n".format(table_entity.eid, column_entity.eid))
                redis_conn.setRelationship(table_entity.eid, column_entity.eid,
                                           "TABLE_COLUMN", {'weight':1, "columnName":column_entity.columnName})
                #redis_conn.createRelationship(table_entity.eid, column_entity.eid, "TABLE_COLUMN")

    """
    Create relationships.
    """
    if entity is not None and table_entity is not None:
        redis_conn.createRelationship(entity.eid, table_entity.eid, "CREATE")
        logging.info(" CREATE Relation between {0} {1}\n".format(entity.eid, table_entity.eid))
        redis_conn.incrEntityCounter(table_entity.eid, "instance_count", sort=True, incrBy=1)
    return [0, tableCount]

def processTableSet(tableset, mongoconn, redis_conn, tenant, entity, isinput, tableEidList=None, hive_success=0):
    dbCount = 0
    tableCount = 0
    if tableset is None or len(tableset) == 0:
        return [dbCount, tableCount]

    endict = {}
    #mongoconn.startBatchUpdate()
    for tableentry in tableset:
        database_name = None
        entryname = tableentry["TableName"].lower()
        entryname = entryname.replace('"', '')
        matches = table_regex.search(entryname)
        if matches is not None:
            database_name = matches.group(1)
            tablename = matches.group(2)
        else:
            tablename = entryname

        """
        Create the Table Entity first if it does not already exist.
        """
        table_entity = mongoconn.getEntityByName(tablename)
        if table_entity is None:
            logging.info("Creating table entity for {0} position 5\n".format(tablename))     
            eid = IdentityService.getNewIdentity(tenant, True)
            table_entity = mongoconn.addEn(eid, tablename, tenant,\
                      EntityType.SQL_TABLE, endict, None)

            if eid == table_entity.eid:
                redis_conn.createEntityProfile(table_entity.eid, "SQL_TABLE")
                redis_conn.incrEntityCounter(table_entity.eid, "instance_count", sort=True, incrBy=0)
                tableCount = tableCount + 1

        tableEidList.add(table_entity.eid)

        """
        If the database is found then create database Entity if it does not already exist.
        """
        database_entity = None
        if database_name is not None:
            database_entity = mongoconn.getEntityByName(database_name)
            if database_entity is None:
                logging.info("Creating database entity for {0}\n".format(database_name))     
                eid = IdentityService.getNewIdentity(tenant, True)
                mongoconn.addEn(eid, database_name, tenant,\
                          EntityType.SQL_DATABASE, endict, None)
                database_entity = mongoconn.getEntityByName(database_name)
                dbCount = dbCount + 1

        """
        Create relations, first between tables and query             
            Then between query and database, table and database
        """
        if entity is not None and table_entity is not None:
            if isinput:
                redis_conn.createRelationship(table_entity.eid, entity.eid, "READ")
                redis_conn.setRelationship(table_entity.eid, entity.eid, "READ", {"hive_success":hive_success})
                redis_conn.incrRelationshipCounter(table_entity.eid, entity.eid, "READ", "instance_count", incrBy=1)
                logging.info("Relation between {0} {1} position 1\n".format(table_entity.eid, entity.eid))     
            else:
                redis_conn.createRelationship(entity.eid, table_entity.eid, "WRITE")
                redis_conn.setRelationship(entity.eid, table_entity.eid, "WRITE", {"hive_success":hive_success})
                redis_conn.incrRelationshipCounter(entity.eid, table_entity.eid, "WRITE", "instance_count", incrBy=1)
                logging.info("Relation between {0} {1} position 2\n".format(entity.eid, table_entity.eid))     

        if database_entity is not None:
            if table_entity is not None:
                redis_conn.createRelationship(database_entity.eid, table_entity.eid, "CONTAINS")
                logging.info("Relation between {0} {1} position 3\n".format(database_entity.eid, table_entity.eid))     

            """ Note this assumes that formRelations is idempotent
            """
            if entity is not None:
                redis_conn.createRelationship(database_entity.eid, entity.eid, "CONTAINS")
                logging.info("Relation between {0} {1} position 4\n".format(database_entity.eid, entity.eid))     

    #mongoconn.finishBatchUpdate()
    
    return [dbCount, tableCount]

def process_mongo_rewrite_request(ch, properties, tenant, instances):

    """
        Steps to rewrite SQL queries to mongo are as following:
        1. For each query in the request.
            2. Save the query to a local file.
            3. Invoke compiler to generate Xplain RA.
            4. Read the output file as a JSON.
            5. Invoke mongo converter template engine to convert.
        6. Send the RPC response. 
    """
    in_file = "/tmp/mongo-RA-input"
    out_file = "/tmp/mongo-RA-output"
    resp_dict = {"mongo_queries" : []}

    for inst in instances:

        if os.path.isfile(in_file):
            os.remove(in_file)

        if os.path.isfile(out_file):
            os.remove(out_file)

        sql_query = inst["query"]
        if len(sql_query.strip()) == 0:
            continue

        data_dict = { "InputFile": in_file, "OutputFile": out_file}

        """
            2. Save the query to a local file.
        """
        infile = open(in_file, "w")
        infile.write(sql_query)
        infile.flush()
        infile.close()

        """
            3. Invoke compiler to generate Xplain RA.
        """
        try:
            output_file_name = "/tmp/hbase_ddl.out"

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("localhost", 12121))

            data = dumps(data_dict)
            client_socket.send("1\n");

            """
                For Mongo rewrite the opcode is 3.
            """
            client_socket.send("3\n");
            data = data + "\n"
            client_socket.send(data)
            rx_data = client_socket.recv(512)

            if rx_data == "Done":
                status = "SUCCESS"
            else:
                status = "FAILED"

            client_socket.close()

            compile_doc = None
            """
                4. Read the output file as a JSON.
            """
            if not os.path.isfile(out_file):
                resp_dict["status"] = "Failed"
            else:
                """ 
                    Read the output file and send the RPC response.
                """
                compile_doc = None
                with open(out_file) as data_file:    
                    compile_doc = load(data_file)

                """
                    5. Invoke mongo converter template engine to convert.
                """
                mongo_query = convert_to_mongo(compile_doc["QueryBlock"])
                resp_dict['mongo_queries'].append(mongo_query)

            resp_dict["status"] = "Success"
        except:
            logging.exception("Tenent {0}, {1}\n".format(tenant, traceback.format_exc()))     
            resp_dict["status"] = "Failed"

    """
        6. Send the RPC response. 
    """
    logging.info("Sending compiler response")
    ch.basic_publish(exchange='',
                     routing_key=properties.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                     properties.correlation_id),
                     body=dumps(resp_dict))

def process_hbase_ddl_request(ch, properties, tenant, instances, db, redis_conn):

    """
        Steps to generate Hbase DDL are as following:
        1. Gets the pattern ID of the pattern. Finds the tables and 
           queries involved in the pattern.
        2. Invoke analytics workflow to generate Hbase analytics.
        3. Save the analytics results to a local file.
        4. Send request to DDL generator.
        5. Check the output file.
        6. Read output file and send the RPC response. 
    """
    compile_doc = None
    prog_id = None
    queryList = None
    transformType = ""
    for inst in instances:
        if 'entity_id' in inst:
            prog_id = inst['entity_id']
            transformType = 'SingleTable'
        elif "patID" in inst:
            prog_id = inst["patID"]
            transformType = 'SinglePattern'

    if prog_id is None:
        logging.info("No program ID found for hbase_ddl_request")
        return

    if transformType == "SingleTable":
        logging.info('Received SingleTable hbase transformation request.')
        tableList = [prog_id]
    elif transformType == "SinglePattern":
        logging.info('Received SinglePattern hbase transformation request.')
        join_group = db.entities.find_one({'profile.PatternID':prog_id}, {'eid':1, 'profile.FullQueryList':1})

        if join_group is None:
            return

        tableList = []
        queryList = []

        relations_to = redis_conn.getRelationships(join_group['eid'], None, "COOCCURRENCE_TABLE")
        for rel in relations_to:
            tableList.append(rel['end_en'])

        if "profile" in join_group:
            if "FullQueryList" in join_group['profile']:
                queryList = join_group['profile']['FullQueryList']

    """
        Invoke analytics workflow to generate Hbase analytics.
    """
    result = run_workflow(tenant, tableList, queryList)

    """
        Save the analytics results to a local file.
    """
    oFile_path = "/tmp/hbase_analytics.out"
    oFile = open(oFile_path, "w")
    oFile.write(dumps(result))
    oFile.flush()
    oFile.close()

    resp_dict = {}
    status = "FAILED"
    """
        Send request to DDL generator.
    """
    try:
        output_file_name = "/tmp/hbase_ddl.out"

        if os.path.isfile(output_file_name):
            os.remove(output_file_name)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", 12121))

        data_dict = {"InputFile": oFile_path, "OutputFile": output_file_name, 
                     "EntityId": prog_id, "TenantId": "100"}
        data = dumps(data_dict)
        client_socket.send("1\n");

        """
            For DDL generation the opcode is 2.
        """
        client_socket.send("2\n");
        data = data + "\n"
        client_socket.send(data)
        rx_data = client_socket.recv(512)

        if rx_data == "Done":
            status = "SUCCESS"
        else:
            status = "FAILED"

        client_socket.close()

        """
            Upon response, check the output file.
        """
        if not os.path.isfile(output_file_name):
            resp_dict["status"] = "Failed"
        else:
            """ 
                Read the output file and send the RPC response.
            """
            compile_coc = None
            with open(output_file_name) as data_file:    
                compile_doc = load(data_file)
            resp_dict = compile_doc
            resp_dict["status"] = "Success"
    except:
        logging.exception("Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))     
        resp_dict["status"] = "Failed"

    """
        Publish the response to the requestor.
    """
    logging.info("Sending compiler response")
    ch.basic_publish(exchange='',
                     routing_key=properties.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                     properties.correlation_id),
                     body=dumps(resp_dict))

def process_scale_mode(tenant, uid, instances, smc):
    
    for inst in instances:
        """
        Create input and output folders for compiler
        """
        if 'query' in inst:
            query = inst["query"].strip()
        else:
            logging.error("Could not find query")
            continue
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        destination = '/mnt/volume1/compile-' + tenant + "/" + timestr 
        if not os.path.exists(destination):
            os.makedirs(destination)
        dest_file_name = destination + "/input.query"
        dest_file = open(dest_file_name, "w+")
        dest_file.write(query)
        dest_file.flush()
        dest_file.close()
        output_file_name = destination + "/gsp.out"


        data_dict = { "InputFile": dest_file_name,
                      "OutputFile": output_file_name,
                      "Compiler": "gsp",
                      "EntityId": "",
                      "TenantId": "100" }


        data = dumps(data_dict)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", 12121))
        client_socket.send("1\n");

        """
        For regular compilation the opcode is 1.
        """
        client_socket.send("1\n");
        data = data + "\n"
        client_socket.send(data)
        rx_data = client_socket.recv(512)

        if rx_data == "Done":
            logging.info("Got Done")

        client_socket.close()

        compile_doc = None
        logging.info("Loading file : "+ output_file_name)
        with open(output_file_name) as data_file:    
            compile_doc = load(data_file)["gsp"]

        compile_doc_fields = ["ErrorSignature", 
                              "SignatureKeywords",
                              "OperatorList",
                              "selectColumnNames",
                              "groupByColumns",
                              "orderByColumns",
                              "whereColumns",
                              "joinPredicates",
                              "queryHash",
                              "queryNameHash",
                              "InputTableList",
                              "OutputTableList",
                              "ComplexityScore"]

        for field in compile_doc_fields:
            if field in compile_doc and compile_doc[field] is not None:
                try:
                    smc.process(field, compile_doc[field])
                except:
                    logging.exception("Error in Scale Mode Connector")
                #Break if query was not parsed
                if field == "ErrorSignature" and compile_doc[field]:
                    break

        if compile_doc["ErrorSignature"] == "":
            filter_compile_doc = compile_doc.copy()
            fmc = FilterModeConnector(tenant)
            fmc.process_query(filter_compile_doc)
        
        
            
def updateRelationCounter(redis_conn, eid):

    relationshipTypes = ['QUERY_SELECT', 'QUERY_JOIN', 'QUERY_FILTER', "READ", "WRITE", "COOCCURRENCE_TABLE",
                         'QUERY_GROUPBY', 'QUERY_ORDERBY', "COOCCURRENCE_GROUP", "COOCCURRENCE_QUERY"]

    relations_to = redis_conn.getRelationships(eid, None, None)
    for rel in relations_to:
        if rel['rtype'] in relationshipTypes:
            redis_conn.incrRelationshipCounter(eid, rel['end_en'], rel['rtype'], "instance_count", incrBy=1)

    relations_from = redis_conn.getRelationships(None, eid, None)
    for rel in relations_from:
        if rel['rtype'] in relationshipTypes:
            redis_conn.incrRelationshipCounter(rel['start_en'], eid, rel['rtype'], "instance_count", incrBy=1)

def sendAnalyticsMessage(mongoconn, redis_conn, ch, collection, tenant, uid, entity, opcode):
    if entity is not None:
        if opcode is not None:
            msg_dict = {'tenant':tenant, 'opcode':opcode, "entityid":entity.eid} 
            if uid is not None:
                msg_dict['uid'] = uid
            message_id = genMessageID("Comp", collection, entity.eid)
            msg_dict['message_id'] = message_id
            message = dumps(msg_dict)
            connection1.publish(ch,'','mathqueue',message)
            logging.info("Sent message to Math pos1:" + str(msg_dict))
             
            incrementPendingMessage(collection, redis_conn, uid,message_id)
            collection.update({'uid':uid},{'$inc':{"Math3MessageCount":1}})

def processCompilerOutputs(mongoconn, redis_conn, ch, collection, tenant, uid, query, data, compile_doc, source_platform):
    """
        Takes a list of compiler output files and performs following:
            1. If the compiler is unsuccessful in parsing the query:
                  Build the profile info
            2. If the compiler is successful in parsing the query:
                - Check if the entity with MD5 hash already exists.
                    o If the query entity exists, then add the instance and return
                      No further processing is necessary.
                    o If the query entity does not exist, then add the profile, record the hash.
            3. After all the compiler outputs have been processed, create the query entity.
    """
    entity = None
    tableEidList = set()
    if compile_doc is None:
        logging.info("No compile_doc found")
        return None, None

    profile_dict = { "profile": { "Compiler" : {}}}
    comp_profile = profile_dict["profile"]["Compiler"]

    q_hash = None
    for key in compile_doc:
        comp_profile[key] = compile_doc[key]
        if key == "gsp":
            if "queryHash" in compile_doc[key]:
                q_hash =  compile_doc[key]["queryHash"]
                profile_dict["md5"] = q_hash
                logging.info("Compiler {0} Program {1}  md5 {2}".format(key, query, q_hash))
            if "queryTemplate" in compile_doc[key]:
                profile_dict["logical_name"] = compile_doc[key]["queryTemplate"]

    custom_id = None
    if data is not None and "custom_id" in data:
        custom_id = data['custom_id']

    """
        get Entity
        if no entity then create entity
    """
    entity = None
    if q_hash is not None:
        entity = mongoconn.searchEntity({"md5":q_hash})

    update = False

    if entity is None:
        logging.info("Going to create the entity")
        profile_dict["instance_count"] = 1
        if custom_id is not None:
            profile_dict['custom_id'] = custom_id
        try:
            eid = IdentityService.getNewIdentity(tenant, True)
            entity = mongoconn.addEn(eid, query, tenant,\
                       EntityType.SQL_QUERY, profile_dict, None) 
            if entity is None:
                logging.info("No Entity found")
                return None, None
            if eid == entity.eid:

                redis_conn.createEntityProfile(entity.eid, "SQL_QUERY")
                redis_conn.incrEntityCounter(entity.eid, "instance_count", sort = True,incrBy=1)
                
                inst_dict = None
                if custom_id is not None:
                    inst_dict = {'custom_id':custom_id}
                mongoconn.updateInstance(entity, query, None, inst_dict)

                entityProfile = entity.profile

                if "Compiler" in entityProfile\
                        and "gsp" in entityProfile['Compiler']\
                        and "ErrorSignature" in entityProfile['Compiler']['gsp']\
                        and entityProfile['Compiler']['gsp']["ErrorSignature"] == "":
                    unique_queries = mongoconn.db.entities.find({'profile.Compiler.gsp.ErrorSignature':""},
                                                                {"eid":1,"_id":0})
                    uniqueEids = [x['eid'] for x in unique_queries]
                    unique_count = mongoconn.db.entity_instances.find({"eid":{'$in':uniqueEids}}).count()
                    mongoconn.db.dashboard_data.update({'tenant':tenant},\
                        {'$inc' : {"TotalQueries": 1, "semantically_unique_count": 1 }, 
                        '$set': { "unique_count": unique_count}}, \
                            upsert = True)
                else:
                    logging.info("No ErrorSignature found.")

                if "Compiler" in entityProfile\
                        and "gsp" in entityProfile['Compiler']\
                        and "ComplexityScore" in entityProfile['Compiler']['gsp']:
                    redis_conn.incrEntityCounter(entity.eid, "ComplexityScore", sort = True,
                        incrBy= entityProfile["Compiler"]["gsp"]["ComplexityScore"])
                else:
                    logging.info("No ComplexityScore found.")
            else:
                update = True

        except DuplicateKeyError:
            inst_dict = {}
            
            if custom_id is not None:
                inst_dict = {'custom_id':custom_id}
            entity = mongoconn.searchEntity({"md5":q_hash})
            if entity is None:
                logging.info("Entity not found for hash - {0}".format(q_hash))
                return None, None
    else:
        update = True

    if update == True:
        """
        Update instance count, store the instance and update the instance counts in 
        relationships.
        """

        redis_conn.incrEntityCounter(entity.eid, "instance_count", sort = True, incrBy=1)

        entityProfile = entity.profile
        if "Compiler" in entityProfile\
                and "gsp" in entityProfile['Compiler']\
                and "ErrorSignature" in entityProfile['Compiler']['gsp']\
                and entityProfile['Compiler']['gsp']["ErrorSignature"] == "":

            unique_queries = mongoconn.db.entities.find({'profile.Compiler.gsp.ErrorSignature':""},
                                                        {"eid":1,"_id":0})
            uniqueEids = [x['eid'] for x in unique_queries]
            unique_count = mongoconn.db.entity_instances.find({"eid":{'$in':uniqueEids}}).count()
            mongoconn.db.dashboard_data.update({'tenant':tenant},\
                {'$inc' : {"TotalQueries": 1},'$set': { "unique_count": unique_count}}, upsert = True)
        else:
            logging.info("No ErrorSignature found in update.")

        updateRelationCounter(redis_conn, entity.eid)

        inst_dict = None
        if custom_id is not None:
            inst_dict = {'custom_id':custom_id}
        mongoconn.updateInstance(entity, query, None, inst_dict)
        
        try:
            for key in compile_doc:
                stats_runsuccess_key = "Compiler." + key + ".run_success"
                stats_runfailure_key = "Compiler." + key + ".run_failure"
                stats_success_key = "Compiler." + key + ".success"
                stats_failure_key = "Compiler." + key + ".failure"
            
                if compile_doc[key].has_key("ErrorSignature") and\
                    len(compile_doc[key]["ErrorSignature"]) > 0:
                    collection.update({'uid':uid},{"$inc": {stats_success_key:0, stats_failure_key: 1, stats_runsuccess_key:1}})
                else:
                    collection.update({'uid':uid},{"$inc": {stats_success_key:1, stats_failure_key: 0, stats_runsuccess_key:1}})


            return entity, "UpdateQueryProfile"
        except:
            logging.exception("Tenent {0}, {1}\n".format(tenant, traceback.format_exc()))
            collection.update({'uid':uid},{"$inc": {stats_runfailure_key: 1, stats_runsuccess_key: 0}})
            return None, None

    for key in compile_doc:
        try:
            stats_newdbs_key = "Compiler." + key + ".newDBs"
            stats_newtables_key = "Compiler." + key + ".newTables"
            stats_runsuccess_key = "Compiler." + key + ".run_success"
            stats_runfailure_key = "Compiler." + key + ".run_failure"
            stats_success_key = "Compiler." + key + ".success"
            stats_failure_key = "Compiler." + key + ".failure"

            hive_success = 0
            if key == "hive" and 'ErrorSignature' in compile_doc:
                if len(compile_doc['ErrorSignature']) == 0:
                    hive_success = 1

            mongoconn.updateProfile(entity, "Compiler", key, compile_doc[key])

            if compile_doc[key].has_key("InputTableList"):
                tmpAdditions = processTableSet(compile_doc[key]["InputTableList"], 
                                               mongoconn, redis_conn, tenant, entity, True,  
                                               tableEidList)
                if uid is not None:
                    collection.update({'uid':uid},{"$inc": {stats_newdbs_key: tmpAdditions[0], 
                                      stats_newtables_key: tmpAdditions[1]}})
                    mongoconn.db.dashboard_data.update({'tenant':tenant}, {'$inc' : {"TableCount":tmpAdditions[1]}}, upsert = True)
    
            if compile_doc[key].has_key("OutputTableList"):
                tmpAdditions = processTableSet(compile_doc[key]["OutputTableList"], mongoconn, redis_conn, 
                                               tenant, entity, False, tableEidList)
                if uid is not None:
                    collection.update({'uid':uid},{"$inc": {stats_newdbs_key: tmpAdditions[0], stats_newtables_key: tmpAdditions[1]}})
                    mongoconn.db.dashboard_data.update({'tenant':tenant}, {'$inc' : {"TableCount":tmpAdditions[1]}}, upsert = True) 

            if compile_doc[key].has_key("ddlcolumns"):
                tmpAdditions = processColumns(compile_doc[key]["ddlcolumns"], 
                                                           mongoconn, redis_conn, tenant, entity)
                if uid is not None:
                    collection.update({'uid':uid},{"$inc": {stats_newdbs_key: tmpAdditions[0], 
                                      stats_newtables_key: tmpAdditions[1]}})
                    mongoconn.db.dashboard_data.update({'tenant':tenant}, {'$inc' : {"TableCount":tmpAdditions[1]}}, upsert = True) 

            if compile_doc[key].has_key("ErrorSignature") and\
                len(compile_doc[key]["ErrorSignature"]) > 0:
                collection.update({'uid':uid},{"$inc": {stats_success_key:0, stats_failure_key: 1, stats_runsuccess_key:1}})
            else:
                collection.update({'uid':uid},{"$inc": {stats_success_key:1, stats_failure_key: 0, stats_runsuccess_key:1}})

            if compile_doc[key].has_key("subQueries") and\
                len(compile_doc[key]["subQueries"]) > 0:
                logging.info("Processing Sub queries")
                for sub_q_dict in compile_doc[key]["subQueries"]:
                    if "origQuery" not in sub_q_dict["gsp"]:
                        logging.info("Original query not found in sub query dictionary")
                        continue
                    sub_q = sub_q_dict["gsp"]["origQuery"]
                    logging.info("Processing Sub queries " + sub_q)
                    sub_entity, sub_opcode = processCompilerOutputs(mongoconn, redis_conn, ch, collection, 
                                                    tenant, uid, sub_q, data, sub_q_dict, source_platform)
                    sendAnalyticsMessage(mongoconn, redis_conn, ch, collection, tenant, uid, sub_entity, sub_opcode)
        except:
            logging.exception("Tenent {0}, {1}\n".format(tenant, traceback.format_exc()))     
            if uid is not None:
                collection.update({'uid':uid},{"$inc": {stats_runfailure_key: 1, stats_runsuccess_key: 0}})
            return None, None

    return entity, "GenerateQueryProfile"

def callback(ch, method, properties, body):
    startTime = time.time()
    dbAdditions = [0,0]
    tmpAdditions = [0,0]
    msg_dict = loads(body)

    logging.info("compiler Got message "+ str(msg_dict))
     

    """
    Validate the message.
    """ 
    if not msg_dict.has_key("tenant") or \
       not msg_dict.has_key("job_instances"):
        logging.error("Invalid message received\n")     

    tenant = msg_dict["tenant"]
    instances = msg_dict["job_instances"]
    try:
        received_msgID = msg_dict["message_id"]
    except:
        received_msgID = None
    uid = None
    db = None

    mongo_url = getMongoServer(tenant)


    if "opcode" in msg_dict and msg_dict["opcode"] == "HbaseDDL":
        logging.info("Got the opcode of Hbase")
        db = MongoClient(mongo_url)[tenant]
        redis_conn = RedisConnector(tenant)
        process_hbase_ddl_request(ch, properties, tenant, instances, db, redis_conn)
        """
        Read the input and respond.
        """
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if "opcode" in msg_dict and msg_dict["opcode"] == "MongoTransform":
        logging.info("Got the opcode For Mongo Translation")
        process_mongo_rewrite_request(ch, properties, tenant, instances)

        """
        Read the input and respond.
        """
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if "opcode" in msg_dict and msg_dict["opcode"] == "scale_mode":
        logging.info("Got the opcode for scale mode analysis")
        if 'uid' in msg_dict:
            uid = msg_dict['uid']
        else:
            logging.error("No uid, dropping scale mode message")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        redis_conn = RedisConnector(tenant)
        collection = MongoClient(mongo_url)[tenant].uploadStats
        smc = ScaleModeConnector(tenant)
        process_scale_mode(tenant, uid, instances, smc)
        decrementPendingMessage(collection, redis_conn, uid, received_msgID)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    
    if msg_dict.has_key('uid'):
        uid = msg_dict['uid']

        """
        Check if this is a valid UID. If it so happens that this flow has been deleted,
        then drop the message.
        """
        db = MongoClient(mongo_url)[tenant]
        if not checkUID(db, uid):
            """
            Just drain the queue.
            """
            #connection1.basicAck(ch,method)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
      
        collection = MongoClient(mongo_url)[tenant].uploadStats
        dashboard_data = MongoClient(mongo_url)[tenant].dashboard_data
        collection.update({'uid':uid},{'$inc':{"Compiler.count":1}})
    else:
        """
        We do not expect anything without UID. Discard message if not present.
        """
        #connection1.basicAck(ch,method)
        ch.basic_ack(delivery_tag=method.delivery_tag)
           
        return

    mongoconn = Connector.getConnector(tenant)
    if mongoconn is None:
        mongoconn = MongoConnector({'host':mongo_url, 'context':tenant, \
                                    'create_db_if_not_exist':True})

    redis_conn = RedisConnector(tenant)

    compconfig = ConfigParser.RawConfigParser()
    compconfig.read("/etc/xplain/compiler.cfg")

    source_platform = None
    if "source_platform" in msg_dict:
        source_platform = msg_dict["source_platform"]

    """
    Generate the CSV from the job instances.
    """
    msg_data = None
    counter = 0
    for inst in instances:
        compile_doc = None
        prog_id = ""
        if "entity_id" in inst:
            prog_id = inst["entity_id"] 
            try:
                entity = mongoconn.getEntity(prog_id)
            except:
                continue

        if "data" in inst:
            msg_data = inst["data"]

        if inst['program_type'] == "Pig":
            compile_doc = generatePigSignature(inst['pig_features'], tenant, prog_id)
            mongoconn.updateProfile(entity, "Compiler", "Pig", compile_doc)
            continue

        query = inst["query"].encode('utf-8').strip()
        logging.info("Program Entity : {0}, eid {1}\n".format(query, prog_id))
        """
        Create a destination/processing folder.
        """
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        destination = '/mnt/volume1/compile-' + tenant + "/" + timestr 
        if not os.path.exists(destination):
            os.makedirs(destination)

        dest_file_name = destination + "/input.query"

        #inst_id = inst["inst_id"] 
        #if prog_collector.has_key(prog_id):
        #    prog_collector[prog_id].append(inst_id)
        #else:
        #    prog_collector[prog_id] = [inst_id]
        #counter = counter + 1
        logging.info("Event received for {0}, entity {1}\n".format(tenant, prog_id))     
        dest_file = open(dest_file_name, "w+")
        dest_file.write(query)
        dest_file.flush()
        dest_file.close()

        """
          Parameters required to create a query entity in the system.
          entity_id, query, tenant, profile documents, source_platform.
        """
        comp_outs = {}

        """
          Get the list of compilers we need to run. 
          Run each valid compiler we find.
        """
        for section in compconfig.sections():
            compilername = ""
            additonalparams = ""
            if not compconfig.has_option(section, "CompilerType"):
                continue

            compilername = compconfig.get(section, "CompilerType")
            if compconfig.has_option(section, "AdditionalParameter") and\
                len(compconfig.get(section, "AdditionalParameter")) > 0:
                additonalparmas = compconfig.get(section, "AdditionalParameter")

            try:
                output_file_name = destination + "/" + compilername + ".out"
                stats_newdbs_key = "Compiler." + compilername + ".newDBs"
                stats_newtables_key = "Compiler." + compilername + ".newTables"
                stats_runsuccess_key = "Compiler." + compilername + ".run_success"
                stats_runfailure_key = "Compiler." + compilername + ".run_failure"
                stats_success_key = "Compiler." + compilername + ".success"
                stats_failure_key = "Compiler." + compilername + ".failure"

                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                retry_count = 0
                socket_connected = False
                while (socket_connected == False) and (retry_count < 2):
                    retry_count += 1
                    try:
                        client_socket.connect(("localhost", 12121))
                        socket_connected = True
                    except:
                        logging.error("Unable to connect to JVM socket on try #%s." %retry_count)
                        time.sleep(1)
                if socket_connected == False:
                    raise Exception("Unable to connect to JVM socket.")

                data_dict = { "InputFile": dest_file_name, "OutputFile": output_file_name, 
                              "Compiler": compilername, "EntityId": prog_id, "TenantId": "100"}
                if source_platform is not None:
                    data_dict["source_platform"] = source_platform
                data = dumps(data_dict)
                client_socket.send("1\n");

                """
                For regular compilation the opcode is 1.
                """
                client_socket.send("1\n");
                data = data + "\n"
                client_socket.send(data)
                rx_data = client_socket.recv(512)

                if rx_data == "Done":
                    logging.info("Got Done")

                client_socket.close()

                """
                It is possible the tenant has been cleared. If this is the case then do not add an new entities.
                """
                if not checkUID(db, uid):
                    """
                    Just drain the queue.
                    """
                    mongoconn.close()
                    #connection1.basicAck(ch,method)
                    ch.basic_ack(delivery_tag=method.delivery_tag)   
                    return

                compile_doc = None
                logging.info("Loading file : "+ output_file_name)
                with open(output_file_name) as data_file:    
                    compile_doc = load(data_file)

                if "gsp" in compile_doc:

                    compile_doc_fields = ["ErrorSignature", 
                                  "SignatureKeywords",
                                  "OperatorList",
                                  "selectColumnNames",
                                  "groupByColumns",
                                  "orderByColumns",
                                  "whereColumns",
                                  "joinPredicates",
                                  "queryHash",
                                  "queryNameHash",
                                  "InputTableList",
                                  "OutputTableList",
                                  "ComplexityScore"]

                    smc = ScaleModeConnector(tenant)
                    for field in compile_doc_fields:
                        if field in compile_doc["gsp"] and compile_doc["gsp"][field] is not None:
                            try:
                                smc.process(field, compile_doc["gsp"][field])
                            except:
                                logging.exception("Error in Scale Mode Connector")
                                #Break if query was not parsed
                            if field == "ErrorSignature" and compile_doc["gsp"][field]:
                                break

                if compile_doc is not None:
                    for key in compile_doc:
                        comp_outs[key] = compile_doc[key]

            except:
                logging.exception("Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))     
                if msg_dict.has_key('uid'):
                    collection.update({'uid':uid},{"$inc": {stats_runfailure_key: 1, stats_runsuccess_key: 0}})
                #mongoconn.updateProfile(entity, "Compiler", section, {"Error":traceback.format_exc()})

        entity, opcode = processCompilerOutputs(mongoconn, redis_conn, ch, collection, tenant, uid, query, msg_data, comp_outs, source_platform)

        sendAnalyticsMessage(mongoconn, redis_conn, ch, collection, tenant, uid, entity, opcode)

        if not usingAWS:
            continue

        """
        Copy over any intermediate file to S3 and remove the directory.
        """
        try:
            shutil.rmtree(destination)     
        except:
            logging.exception("Tenent {0} removing intermediate file failed.\n".format(tenant))    


    logging.info("Event Processing Complete")     
    
    endTime = time.time()

    if msg_dict.has_key('uid'):
        #if uid has been set, the variable will be set already
        collection.update({'uid':uid},{"$inc": {"Compiler.time":(endTime-startTime)}})
        
    mongoconn.close()
    connection1.basicAck(ch,method)
    collection.update({'uid':uid},{'$inc':{"RemoveCompilerMessageCount":1}})
    callback_params = {'tenant':tenant, 'connection':connection1, 'channel':ch, 'uid':uid, 'queuename':'mathqueue'}
    decrementPendingMessage(collection, redis_conn, uid, received_msgID, end_of_phase_callback, callback_params)


connection1 = RabbitConnection(callback, ['compilerqueue'],['mathqueue'], {},BAAZ_COMPILER_LOG_FILE)

logging.info("BaazCompiler going to start Consuming")

connection1.run()

logging.info("Closing BaazCompiler")
