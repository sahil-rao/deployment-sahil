#!/usr/bin/python

"""
Compile Service:
"""
from flightpath.MongoConnector import *
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.utils import *
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

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"
BAAZ_COMPILER_LOG_FILE = "/var/log/BaazCompileService.err"

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
rabbitserverIP = config.get("RabbitMQ", "server")
mongoserverIP = config.get("MongoDB", "server")
try:
   replicationGroup = config.get("MongoDB", "replicationGroup")
except:
   replicationGroup = None

mongo_url = "mongodb://" + mongoserverIP + "/"
if replicationGroup is not None:
    mongo_url = mongo_url + "?replicaset=" + replicationGroup

if os.path.isfile(BAAZ_COMPILER_LOG_FILE):
    timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    shutil.copy(BAAZ_COMPILER_LOG_FILE, BAAZ_COMPILER_LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=BAAZ_COMPILER_LOG_FILE,level=logging.INFO,datefmt='%m/%d/%Y %I:%M:%S %p')

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
    
def processTableSet(tableset, mongoconn, tenant, entity, isinput, tableEidList=None):
    dbCount = 0
    tableCount = 0
    if tableset is None or len(tableset) == 0:
        return [dbCount, tableCount]

    endict = {}
    mongoconn.startBatchUpdate()
    for tableentry in tableset:
        database_name = None
        entryname = tableentry["TableName"].lower()
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

    mongoconn.finishBatchUpdate()
    
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
                """ Call the Compiler
                """ 
                output_file_name = destination + "/" + compilername + ".out"
                stats_newdbs_key = "Compiler." + compilername + ".newDBs"
                stats_newtables_key = "Compiler." + compilername + ".newTables"
                stats_runsuccess_key = "Compiler." + compilername + ".run_success"
                stats_runfailure_key = "Compiler." + compilername + ".run_failure"
                stats_success_key = "Compiler." + compilername + ".success"
                stats_failure_key = "Compiler." + compilername + ".failure"

                proc = Popen('java com.baaz.query.BaazQueryAnalyzer -input {0} -output {1} '\
                                '-tenant 100 -program {2} '\
                                '-compiler {3}'.format(dest_file_name, output_file_name,\
                                                       prog_id, compilername),\
                               stdout=PIPE, shell=True, env=dict(os.environ, CLASSPATH=classpath))

                wait_count = 0
                while wait_count < 25 and proc.poll() is None:
                    time.sleep(.2)
                    wait_count = wait_count + 1

                for line in proc.stdout:
                    logging.info(str(line))
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
        message_id = genMessageID(received_msgID, entity.eid)
        msg_dict['message_id'] = message_id
        message = dumps(msg_dict)
        connection1.publish(ch,'','mathqueue',message)
        logging.info("Sent message to Math pos1:" + str(msg_dict))
         
        incrementPendingMessage(collection, uid,message_id)
        collection.update({'uid':uid},{'$inc':{"Math3MessageCount":1}})
        #Inject event for table profile.
        msg_dict = {'tenant':tenant, 'opcode':"GenerateTableProfile"}
        if uid is not None:
            msg_dict['uid'] = uid

        for eid in list(tableEidList):
            #Inject event for profile updation for query
            msg_dict["entityid"] = eid
            message_id = genMessageID(received_msgID, eid)
            msg_dict['message_id'] = message_id
            message = dumps(msg_dict)
            connection1.publish(ch,'','mathqueue',message)
            logging.info("Sending message to Math pos2:" + str(msg_dict))
            incrementPendingMessage(collection, uid,message_id)
            collection.update({'uid':uid},{'$inc':{"Math4MessageCount":1}})


    logging.info("Event Processing Complete")     
    
    endTime = time.time()

    if msg_dict.has_key('uid'):
        #if uid has been set, the variable will be set already
        collection.update({'uid':uid},{"$inc": {"Compiler.time":(endTime-startTime)}})
        
    mongoconn.close()
    connection1.basicAck(ch,method)
    collection.update({'uid':uid},{'$inc':{"RemoveCompilerMessageCount":1}})
    decrementPendingMessage(collection, uid, received_msgID)


connection1 = RabbitConnection(callback, ['compilerqueue'],['mathqueue'], {},BAAZ_COMPILER_LOG_FILE)

logging.info("BaazCompiler going to start Consuming")

connection1.run()

logging.info("Closing BaazCompiler")
