#!/usr/bin/python

"""
Compile Service:
"""
from flightpath.MongoConnector import *
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.RotatingS3FileHandler import *
from flightpath.utils import *
from flightpath.Provenance import getMongoServer
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

#104857600

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
    
def processColumns(columnset, mongoconn, tenant, entity):
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
            logging.info("Creating table entity for {0}\n".format(tablename))     
            eid = IdentityService.getNewIdentity(tenant, True)
            table_entity = mongoconn.addEn(eid, tablename, tenant,\
                      EntityType.SQL_TABLE, {}, None)
            tableCount = tableCount + 1

        if column_entity is None:
            logging.info("Creating Column entity for {0}\n".format(column_entity_name))     
            eid = IdentityService.getNewIdentity(tenant, True)
            column_entity = mongoconn.addEn(eid, column_entity_name, tenant,\
                            EntityType.SQL_TABLE_COLUMN, column_entry, None)

            if column_entity is not None:
                logging.info("TABLE_COLUMN Relation between {0} {1}\n".format(table_entity.eid, column_entity.eid))     
                #print "Form relation : ", join_entity.name, " ", m_query_entity.name
                mongoconn.formRelation(table_entity, column_entity, "TABLE_COLUMN", weight=1)

    """
    Create relationships.
    """
    if entity is not None and table_entity is not None:
        mongoconn.formRelation(entity, table_entity, "CREATE", weight=1)
        logging.info(" CREATE Relation between {0} {1}\n".format(entity.eid, table_entity.eid))     
    return [0, tableCount]


def addColumns(columnset, mongoconn, tenant, entity, opType, tableIdentifier, colIdentifier):
    '''
    Creating this as a separate function seperate because I don't want to create a table
    entity if it doesn't already exist.
    '''
    columnCount = 0
    table_entity = None
    for column_entry in columnset:
        if tableIdentifier not in column_entry:
            continue

        tablename = column_entry[tableIdentifier]
        columnname = column_entry[colIdentifier]
        table_entity = mongoconn.getEntityByName(tablename)

        column_entity_name = tablename.lower() + "." + columnname.lower()
        column_entity = mongoconn.getEntityByName(column_entity_name)

        if table_entity is None:
            continue

        if column_entity is None:
            logging.info("Creating Column entity for {0}\n".format(column_entity_name))     
            eid = IdentityService.getNewIdentity(tenant, True)
            column_entity = mongoconn.addEn(eid, column_entity_name, tenant,\
                            EntityType.SQL_TABLE_COLUMN, column_entry, None)

            if column_entity is not None:
                logging.info("TABLE_COLUMN Relation between {0} {1}\n".format(table_entity.eid, column_entity.eid))     
                #print "Form relation : ", join_entity.name, " ", m_query_entity.name
                mongoconn.formRelation(table_entity, column_entity, "TABLE_COLUMN", weight=1)
                columnCount += 1

        mongoconn.formRelation(entity, column_entity, "QUERY_"+opType, weight=1)
        logging.info(" {0} Relation between {1} {2}\n".format("QUERY_"+opType, entity.eid, column_entity.eid))

    return columnCount

def addJoinColumns(columnset, mongoconn, tenant, entity, opType):
    '''
    Creating this as a separate function because we want to account for both columns
    and create a join relation between them.
    '''
    columnCount = 0
    LHStable_entity = None
    RHStable_entity = None
    for column_entry in columnset:
        if ("LHSTable" not in column_entry) or ("RHSTable" not in column_entry) or \
            ("LHSColumn" not in column_entry) or ("RHSColumn" not in column_entry):
            continue

        LHStablename = column_entry["LHSTable"]
        RHStablename = column_entry["RHSTable"]
        LHSColumnName = column_entry["LHSColumn"]
        RHSColumnName = column_entry["RHSColumn"]

        LHStable_entity = mongoconn.getEntityByName(LHStablename)
        RHStable_entity = mongoconn.getEntityByName(RHStablename)

        LHScolumn_entity_name = LHStablename.lower() + "." + LHSColumnName.lower()
        LHScolumn_entity = mongoconn.getEntityByName(LHScolumn_entity_name)

        RHScolumn_entity_name = RHStablename.lower() + "." + RHSColumnName.lower()
        RHScolumn_entity = mongoconn.getEntityByName(RHScolumn_entity_name)


        if LHStable_entity is None:
            continue

        if RHStable_entity is None:
            continue

        if LHScolumn_entity is None:
            logging.info("Creating Column entity for {0}\n".format(LHScolumn_entity_name))     
            eid = IdentityService.getNewIdentity(tenant, True)
            LHScolumn_entity = mongoconn.addEn(eid, LHScolumn_entity_name, tenant,\
                            EntityType.SQL_TABLE_COLUMN, column_entry, None)

            if LHScolumn_entity is not None:
                logging.info("TABLE_COLUMN Relation between {0} {1}\n".format(LHStable_entity.eid, LHScolumn_entity.eid))     
                #print "Form relation : ", join_entity.name, " ", m_query_entity.name
                mongoconn.formRelation(LHStable_entity, LHScolumn_entity, "TABLE_COLUMN", weight=1)
                columnCount += 1

        if RHScolumn_entity is None:
            logging.info("Creating Column entity for {0}\n".format(RHScolumn_entity_name))     
            eid = IdentityService.getNewIdentity(tenant, True)
            RHScolumn_entity = mongoconn.addEn(eid, RHScolumn_entity_name, tenant,\
                            EntityType.SQL_TABLE_COLUMN, column_entry, None)

            if RHScolumn_entity is not None:
                logging.info("TABLE_COLUMN Relation between {0} {1}\n".format(RHStable_entity.eid, RHScolumn_entity.eid))     
                #print "Form relation : ", join_entity.name, " ", m_query_entity.name
                mongoconn.formRelation(RHStable_entity, RHScolumn_entity, "TABLE_COLUMN", weight=1)
                columnCount += 1

        mongoconn.formRelation(LHScolumn_entity, RHScolumn_entity, "COLUMN_"+opType, weight=1)
        mongoconn.formRelation(entity, LHScolumn_entity, "QUERY_"+opType, weight=1)
        mongoconn.formRelation(entity, RHScolumn_entity, "QUERY_"+opType, weight=1)
        logging.info(" {0} Relation between {1} {2}\n".format("QUERY_"+opType, entity.eid, LHScolumn_entity.eid))
        logging.info(" {0} Relation between {1} {2}\n".format("QUERY_"+opType, entity.eid, RHScolumn_entity.eid))
        logging.info(" {0} Relation between {1} {2}\n".format("COLUMN_"+opType, LHScolumn_entity.eid, RHScolumn_entity.eid))

    return columnCount

def processTableSet(tableset, mongoconn, tenant, entity, isinput, tableEidList=None):
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
            logging.info("Creating table entity for {0}\n".format(tablename))     
            eid = IdentityService.getNewIdentity(tenant, True)
            mongoconn.addEn(eid, tablename, tenant,\
                      EntityType.SQL_TABLE, endict, None)
            table_entity = mongoconn.getEntityByName(tablename)
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
                mongoconn.formRelation(table_entity, entity, "READ", weight=1)
                logging.info("Relation between {0} {1}\n".format(table_entity.eid, entity.eid))     
            else:
                mongoconn.formRelation(entity, table_entity, "WRITE", weight=1)
                logging.info("Relation between {0} {1}\n".format(entity.eid, table_entity.eid))     

        if database_entity is not None:
            if table_entity is not None:
                mongoconn.formRelation(database_entity, table_entity, "CONTAINS", weight=1)
                logging.info("Relation between {0} {1}\n".format(database_entity.eid, table_entity.eid))     

            """ Note this assumes that formRelations is idempotent
            """
            if entity is not None:
                mongoconn.formRelation(database_entity, entity, "CONTAINS", weight=1)
                logging.info("Relation between {0} {1}\n".format(database_entity.eid, entity.eid))     

    #mongoconn.finishBatchUpdate()
    
    return [dbCount, tableCount]

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

    compconfig = ConfigParser.RawConfigParser()
    compconfig.read("/etc/xplain/compiler.cfg")

    """
    Generate the CSV from the job instances.
    """
    counter = 0
    for inst in instances:
        compile_doc = None
        prog_id = inst["entity_id"] 
        try:
            entity = mongoconn.getEntity(prog_id)
        except:
            continue

        if entity is None:
            continue

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

        tableEidList = set()
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
                stats_newcolumns_key = "Compiler." + compilername + ".newColumns"
                stats_runsuccess_key = "Compiler." + compilername + ".run_success"
                stats_runfailure_key = "Compiler." + compilername + ".run_failure"
                stats_success_key = "Compiler." + compilername + ".success"
                stats_failure_key = "Compiler." + compilername + ".failure"

                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect(("localhost", 12121))

                data_dict = { "InputFile": dest_file_name, "OutputFile": output_file_name, 
                              "Compiler": compilername, "EntityId": prog_id, "TenantId": "100"}
                data = dumps(data_dict)
                client_socket.send("1\n");
                data = data + "\n"
                client_socket.send(data)
                rx_data = client_socket.recv(512)

                if rx_data == "Done":
                    print "Got Done"

                client_socket.close()

                compile_doc = None
                logging.info("Loading file : "+ output_file_name)
                with open(output_file_name) as data_file:    
                    compile_doc = load(data_file)

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

                if compile_doc is not None:
                    for key in compile_doc:
                        mongoconn.updateProfile(entity, "Compiler", key, compile_doc[key])
                        if compile_doc[key].has_key("InputTableList"):
                            tmpAdditions = processTableSet(compile_doc[key]["InputTableList"], 
                                                           mongoconn, tenant, entity, True,  
                                                           tableEidList)
                            if msg_dict.has_key('uid'):
                                collection.update({'uid':uid},{"$inc": {stats_newdbs_key: tmpAdditions[0], 
                                                  stats_newtables_key: tmpAdditions[1]}})

                        if compile_doc[key].has_key("OutputTableList"):
                            tmpAdditions = processTableSet(compile_doc[key]["OutputTableList"], mongoconn, tenant, entity, False, tableEidList)
                            if msg_dict.has_key('uid'):
                                collection.update({'uid':uid},{"$inc": {stats_newdbs_key: tmpAdditions[0], stats_newtables_key: tmpAdditions[1]}})

                        if compile_doc[key].has_key("ddlcolumns"):
                            tmpAdditions = processColumns(compile_doc[key]["ddlcolumns"], 
                                                           mongoconn, tenant, entity)
                            if msg_dict.has_key('uid'):
                                collection.update({'uid':uid},{"$inc": {stats_newdbs_key: tmpAdditions[0], 
                                                  stats_newtables_key: tmpAdditions[1]}})

                        if "selectColumnNames" in compile_doc[key]:
                            tmpAdditions = addColumns(compile_doc[key]["selectColumnNames"], mongoconn, tenant, entity, 
                                    "SELECT", "tableName", "columnName")

                            if msg_dict.has_key('uid'):
                                collection.update({'uid':uid},{"$inc": {stats_newcolumns_key: tmpAdditions}})

                        if "groupByColumns" in compile_doc[key]:
                            tmpAdditions = addColumns(compile_doc[key]["groupByColumns"], mongoconn, tenant, entity, 
                                    "GROUPBY", "tableName", "columnName")

                            if msg_dict.has_key('uid'):
                                collection.update({'uid':uid},{"$inc": {stats_newcolumns_key: tmpAdditions}})

                        if "whereColumns" in compile_doc[key]:
                            tmpAdditions = addColumns(compile_doc[key]["whereColumns"], mongoconn, tenant, entity, 
                                    "FILTER", "tableName", "columnName")

                            if msg_dict.has_key('uid'):
                                collection.update({'uid':uid},{"$inc": {stats_newcolumns_key: tmpAdditions}})

                        if "orderByColumns" in compile_doc[key]:
                            tmpAdditions = addColumns(compile_doc[key]["orderByColumns"], mongoconn, tenant, entity, 
                                    "ORDERBY", "tableName", "columnName")

                            if msg_dict.has_key('uid'):
                                collection.update({'uid':uid},{"$inc": {stats_newcolumns_key: tmpAdditions}})

                        if "joinPredicates" in compile_doc[key]:
                            
                            tmpAdditions = addJoinColumns(compile_doc[key]["joinPredicates"], mongoconn, tenant, entity, 
                                    "JOIN")

                            if msg_dict.has_key('uid'):
                                collection.update({'uid':uid},{"$inc": {stats_newcolumns_key: tmpAdditions}})

                if msg_dict.has_key('uid'):
                    collection.update({'uid':uid},{"$inc": {stats_runsuccess_key: 1, stats_runfailure_key: 0}})
                    if compile_doc[key].has_key("ErrorSignature") and\
                       len(compile_doc[key]["ErrorSignature"]) > 0:
                        collection.update({'uid':uid},{"$inc": {stats_success_key:0, stats_failure_key: 1}})
                    else:
                        collection.update({'uid':uid},{"$inc": {stats_success_key:1, stats_failure_key: 0}})
            except:
                logging.exception("Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))     
                if msg_dict.has_key('uid'):
                    collection.update({'uid':uid},{"$inc": {stats_runfailure_key: 1, stats_runsuccess_key: 0}})

        msg_dict = {'tenant':tenant, 'opcode':"GenerateQueryProfile", "entityid":entity.eid} 
        if uid is not None:
            msg_dict['uid'] = uid
        message_id = genMessageID("Comp", collection, entity.eid)
        msg_dict['message_id'] = message_id
        message = dumps(msg_dict)
        connection1.publish(ch,'','mathqueue',message)
        logging.info("Sent message to Math pos1:" + str(msg_dict))
         
        incrementPendingMessage(collection, uid,message_id)
        collection.update({'uid':uid},{'$inc':{"Math3MessageCount":1}})

        if not usingAWS:
            continue

        """
        Copy over any intermediate file to S3 and remove the directory.
        """
        try:
            s3_dest = tenant + "/" + myip + "/" + timestr + "/" 
            for (sourceDir, dirname, filename) in os.walk(destination):
                for f in filename:
                    src_path = os.path.join(sourceDir, f)
                    s3_obj_name = s3_dest + f
                    k = file_bucket.new_key(s3_obj_name)
                    k.set_contents_from_filename(src_path) 

            shutil.rmtree(destination)     
        except:
            logging.exception("Tenent {0} S3 upload of intermediate file failed.\n".format(tenant))    


    logging.info("Event Processing Complete")     
    
    endTime = time.time()

    if msg_dict.has_key('uid'):
        #if uid has been set, the variable will be set already
        collection.update({'uid':uid},{"$inc": {"Compiler.time":(endTime-startTime)}})
        
    mongoconn.close()
    connection1.basicAck(ch,method)
    collection.update({'uid':uid},{'$inc':{"RemoveCompilerMessageCount":1}})
    callback_params = {'tenant':tenant, 'connection':connection1, 'channel':ch, 'uid':uid, 'queuename':'mathqueue'}
    decrementPendingMessage(collection, uid, received_msgID, end_of_phase_callback, callback_params)


connection1 = RabbitConnection(callback, ['compilerqueue'],['mathqueue'], {},BAAZ_COMPILER_LOG_FILE)

logging.info("BaazCompiler going to start Consuming")

connection1.run()

logging.info("Closing BaazCompiler")
