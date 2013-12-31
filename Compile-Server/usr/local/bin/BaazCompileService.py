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


BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"

errlog = open("/var/log/BaazCompileService.err", "w+")
connection = pika.BlockingConnection(pika.ConnectionParameters(
        '172.31.10.27'))
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
    
def processTableSet(tableset, mongoconn, tenant, entity, isinput):
    if tableset is None or len(tableset) == 0:
        return

    endict = {}
    for tableentry in tableset:
        tablename = tableentry["TableName"].lower()
        table_entity = mongoconn.getEntityByName(tablename)
        if table_entity is None:
            errlog.write("Creating table entity for {0}\n".format(tablename))     
            #print "Creating table entity for {0}\n".format(tablename)    
            errlog.flush()
            eid = IdentityService.getNewIdentity(tenant, True)
            mongoconn.addEn(eid, tablename, tenant,\
                      EntityType.HADOOP_DATA, endict, None)
            table_entity = mongoconn.getEntityByName(tablename)
        
        if entity is not None:
            if isinput:
                mongoconn.formRelation(table_entity, entity, "READ", weight=1)
                errlog.write("Relation between {0} {1}\n".format(table_entity.eid, entity.eid))     
            else:
                mongoconn.formRelation(entity, table_entity, "WRITE", weight=1)
                errlog.write("Relation between {0} {1}\n".format(entity.eid, table_entity.eid))     
            errlog.flush()

def callback(ch, method, properties, body):
    msg_dict = loads(body)

    #print "Got message ", msg_dict

    """
    Validate the message.
    """ 
    if not msg_dict.has_key("tenant") or \
       not msg_dict.has_key("job_instances"):
        errlog.write("Invalid message received\n")     
        errlog.write(body)
        errlog.write("\n")
        errlog.flush()

    tenant = msg_dict["tenant"]
    instances = msg_dict["job_instances"]

    mongoconn = Connector.getConnector(tenant)
    if mongoconn is None:
        mongoconn = MongoConnector({'host':'172.31.2.42', 'context':tenant, \
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
        errlog.write("Program Entity : {0}, eid {1}\n".format(entity.name, prog_id))
        errlog.flush()

        if inst['program_type'] == "Pig":
            compile_doc = generatePigSignature(inst['pig_features'], tenant, prog_id)
            mongoconn.updateProfile(entity, "Compiler", compile_doc)
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
        errlog.write("Event received for {0}, entity {1}\n".format(tenant, prog_id))     
        errlog.flush()
        dest_file = open(dest_file_name, "w+")
        dest_file.write(query)
        dest_file.flush()
	dest_file.close()
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
                errlog.write(line)
                errlog.flush()
            compile_doc = None
            #print "Loading file : ", output_file_name
            with open(output_file_name) as data_file:    
                compile_doc = load(data_file)
            if compile_doc is not None:
                for key in compile_doc:
                    mongoconn.updateProfile(entity, "Compiler", key, compile_doc[key])
                    if compile_doc[key].has_key("InputTableList"):
                        processTableSet(compile_doc[key]["InputTableList"], mongoconn,\
                                        tenant, entity, True)
                    if compile_doc[key].has_key("OutputTableList"):
                        processTableSet(compile_doc[key]["OutputTableList"], mongoconn,\
                                        tenant, entity, False)

        except:
            errlog.write("Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))     
            errlog.flush()

        try:
            """ Call JSQL Compiler
            """ 
            output_file_name = destination + "/jsql.out"
            proc = Popen('java com.baaz.query.BaazQueryAnalyzer -input {0} -output {1} -tenant 100 -program {2} -compiler jsql'.format(dest_file_name, output_file_name, prog_id),\
                 stdout=PIPE, shell=True, env=dict(os.environ, CLASSPATH=classpath))

            wait_count = 0
            while wait_count < 25 and proc.poll() is None:
                time.sleep(.2)
                wait_count = wait_count + 1

            for line in proc.stdout:
                errlog.write(line)
                errlog.flush()
            compile_doc = None
            #print "Loading file : ", output_file_name
            with open(output_file_name) as data_file:    
                compile_doc = load(data_file)
            if compile_doc is not None:
                for key in compile_doc:
                    mongoconn.updateProfile(entity, "Compiler", key, compile_doc[key])
                    if compile_doc[key].has_key("InputTableList"):
                        processTableSet(compile_doc[key]["InputTableList"], mongoconn,\
                                        tenant, entity, True)
                    if compile_doc[key].has_key("OutputTableList"):
                        processTableSet(compile_doc[key]["OutputTableList"], mongoconn,\
                                        tenant, entity, False)
        except:
            errlog.write("Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))     
            errlog.flush()
            

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

    errlog.write("Event Processing Complete")     
    errlog.flush()
    mongoconn.close()

channel.basic_consume(callback,
                      queue='compilerqueue',
                      no_ack=True)

print "Going to sart consuming"
channel.start_consuming()
print "OOps I am done"

