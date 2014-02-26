#!/usr/bin/python

"""
Compile Service:
"""
from flightpath.MongoConnector import *
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

logging.basicConfig(filename=BAAZ_COMPILER_LOG_FILE,level=logging.INFO,)

#errlog = open("/var/log/BaazCompileService.err", "w+")
connection = pika.BlockingConnection(pika.ConnectionParameters(
        rabbitserverIP))
channel = connection.channel()
channel.queue_declare(queue='compilerqueue')

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
            #print "Creating table entity for {0}\n".format(tablename)    
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
                #print "Creating table entity for {0}\n".format(tablename)    
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

    #print "compiler Got message ", msg_dict

    """
    Validate the message.
    """ 
    if not msg_dict.has_key("tenant") or \
       not msg_dict.has_key("job_instances"):
        logging.error("Invalid message received\n")     

    tenant = msg_dict["tenant"]
    instances = msg_dict["job_instances"]

    uid = None
    if msg_dict.has_key('uid'):
        uid = msg_dict['uid']
	
        collection = MongoClient(mongo_url)[tenant].uploadStats
        collection.update({'uid':uid},{'$inc':{"Compiler.count":1}})

    mongoconn = Connector.getConnector(tenant)
    if mongoconn is None:
        mongoconn = MongoConnector({'host':mongo_url, 'context':tenant, \
                                    'create_db_if_not_exist':True})
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
        logging.info("Program Entity : {0}, eid {1}\n".format(entity.name, prog_id))

        if inst['program_type'] == "Pig":
            compile_doc = generatePigSignature(inst['pig_features'], tenant, prog_id)
            mongoconn.updateProfile(entity, "Compiler", "Pig", compile_doc)
            continue

	query = inst["query"].encode('utf-8').strip()
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
	try:
            """ Call Hive Compiler
            """ 
            output_file_name = destination + "/hive.out"
            proc = Popen('java com.baaz.query.BaazQueryAnalyzer -input {0} -output {1} -tenant 100 -program {2} -compiler hive'.format(dest_file_name, output_file_name, prog_id),\
                 stdout=PIPE, shell=True, env=dict(os.environ, CLASSPATH=classpath))

            wait_count = 0
            while wait_count < 25 and proc.poll() is None:
                time.sleep(.2)
                wait_count = wait_count + 1

            for line in proc.stdout:
                logging.info(line)
            compile_doc = None
            #print "Loading file : ", output_file_name
            with open(output_file_name) as data_file:    
                compile_doc = load(data_file)
            if compile_doc is not None:
                for key in compile_doc:
                    mongoconn.updateProfile(entity, "Compiler", key, compile_doc[key])
                    if compile_doc[key].has_key("InputTableList"):
                        tmpAdditions = processTableSet(compile_doc[key]["InputTableList"], mongoconn, tenant, entity, True,  tableEidList)
			if msg_dict.has_key('uid'):
                	    collection.update({'uid':uid},{"$inc": {"Compiler.hive.newDBs": tmpAdditions[0], "Compiler.hive.newTables": tmpAdditions[1]}})
                    if compile_doc[key].has_key("OutputTableList"):
                        tmpAdditions = processTableSet(compile_doc[key]["OutputTableList"], mongoconn, tenant, entity, False, tableEidList)
			if msg_dict.has_key('uid'):
                	    collection.update({'uid':uid},{"$inc": {"Compiler.hive.newDBs": tmpAdditions[0], "Compiler.hive.newTables": tmpAdditions[1]}})
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Compiler.hive.success": 1}})

        except:
            logging.exception("Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))     
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Compiler.hive.failure": 1}})

        try:
            """ Call GSP Compiler
            """ 
            output_file_name = destination + "/gsp.out"
            proc = Popen('java com.baaz.query.BaazQueryAnalyzer -input {0} -output {1} -tenant 100 -program {2} -compiler gsp'.format(dest_file_name, output_file_name, prog_id),\
                 stdout=PIPE, shell=True, env=dict(os.environ, CLASSPATH=classpath))

            wait_count = 0
            while wait_count < 25 and proc.poll() is None:
                time.sleep(.2)
                wait_count = wait_count + 1

            for line in proc.stdout:
                logging.info(line)
            compile_doc = None
            #print "Loading file : ", output_file_name
            with open(output_file_name) as data_file:    
                compile_doc = load(data_file)
            if compile_doc is not None:
                for key in compile_doc:
                    mongoconn.updateProfile(entity, "Compiler", key, compile_doc[key])
                    if compile_doc[key].has_key("InputTableList"):
                        tmpAdditions = processTableSet(compile_doc[key]["InputTableList"], mongoconn, tenant, entity, True, tableEidList)
			if msg_dict.has_key('uid'):
                	    collection.update({'uid':uid},{"$inc": {"Compiler.gsp.newDBs": tmpAdditions[0], "Compiler.gsp.newTables": tmpAdditions[1]}})
                    if compile_doc[key].has_key("OutputTableList"):
                        tmpAdditions = processTableSet(compile_doc[key]["OutputTableList"], mongoconn, tenant, entity, False, tableEidList)
			if msg_dict.has_key('uid'):
                	    collection.update({'uid':uid},{"$inc": {"Compiler.gsp.newDBs": tmpAdditions[0], "Compiler.gsp.newTables": tmpAdditions[1]}})
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Compiler.gsp.success": 1}})
        except:
            logging.exception("Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))     
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Compiler.gsp.failure": 1}})

        #Inject event for profile updation for query
        
        msg_dict = {'tenant':tenant, 'opcode':"GenerateQueryProfile", "entityid":entity.eid} 
        if uid is not None:
            msg_dict['uid'] = uid
        message = dumps(msg_dict)
        channel.basic_publish(exchange='',
                          routing_key='mathqueue',
                          body=message)
       
        #Inject event for table profile.
        msg_dict = {'tenant':tenant, 'opcode':"GenerateTableProfile"}
        if uid is not None:
            msg_dict['uid'] = uid

        for eid in list(tableEidList):
            #Inject event for profile updation for query
            msg_dict["entityid"] = eid
            message = dumps(msg_dict)
            channel.basic_publish(exchange='',
                              routing_key='mathqueue',
                              body=message)

    #errlog.write("Event received for {0}, {1} total runs with {1} unique jobs \n".format\
    #                (tenant, len(prog_collector.keys()), counter))     

    #for prog_id in prog_collector:
    #    dest_file = open(dest_file_name, "w+")
    #    generateCSV1Header(prog_id, dest_file)
    #    for inst in prog_collector[prog_id]:
    #        generateCSV1Header(prog_id, inst, dest_file)
        
    #    """
    #    Now start the analytics module.
    #    """
    #    dest_file.close()

    logging.info("Event Processing Complete")     
    
    endTime = time.time()

    if msg_dict.has_key('uid'):
	#if uid has been set, the variable will be set already
        collection.update({'uid':uid},{"$inc": {"Compiler.time":(endTime-startTime)}})
	
    mongoconn.close()
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(callback,
                      queue='compilerqueue')

print "Going to start consuming"
channel.start_consuming()
print "OOps I am done"

