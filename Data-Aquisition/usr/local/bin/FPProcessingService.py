#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenant> <log Directory>
"""
#from flightpath.parsing.hadoop.HadoopConnector import *
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.utils import *
from flightpath.parsing.ParseDemux import *
import sys
from flightpath.MongoConnector import *
from json import *
import pika
import shutil
import os
import tarfile
import ConfigParser
import datetime
import time
import logging

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"
BAAZ_FP_LOG_FILE = "/var/log/FPProcessing.err"

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
usingAWS = config.getboolean("mode", "usingAWS")
if usingAWS:
    from boto.s3.key import Key
    import boto

rabbitserverIP = config.get("RabbitMQ", "server")
mongoserverIP = config.get("MongoDB", "server")
metrics_url = None
try:
    replicationGroup = config.get("MongoDB", "replicationGroup")
except:
    replicationGroup = None

mongo_url = "mongodb://" + mongoserverIP + "/"
if replicationGroup is not None:
    mongo_url = mongo_url + "?replicaset=" + replicationGroup

if os.path.isfile(BAAZ_FP_LOG_FILE):
    timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    shutil.copy(BAAZ_FP_LOG_FILE, BAAZ_FP_LOG_FILE+timestr)

logging.basicConfig(filename=BAAZ_FP_LOG_FILE,level=logging.INFO,)

if usingAWS:
    boto_conn = boto.connect_s3()
    bucket = boto_conn.get_bucket('partner-logs') 

def performTenantCleanup(tenant):
    print "Cleaning Tenant ", tenant
    destination = BAAZ_DATA_ROOT + tenant     
    if os.path.exists(destination):
        shutil.rmtree(destination)
    destination = '/mnt/volume1/compile-' + tenant 
    if os.path.exists(destination):
        shutil.rmtree(destination)

def callback(ch, method, properties, body):
    starttime = time.time()
    
    try:
        msg_dict = loads(body)
    except:
        logging.exception("Could not load the message JSON")

    print "FPPS Got message ", msg_dict
    """
    Validate the message.
    """ 
    if not msg_dict.has_key("tenent") or \
       (not msg_dict.has_key("filename") and 
        not msg_dict.has_key("opcode")):
        logging.error("Invalid message received\n")     
        logging.error(body)
        connection1.basicAck(ch,method)
        return

    try:
        tenant = msg_dict["tenent"]
        filename = None
        opcode = None
        if msg_dict.has_key("opcode") and msg_dict["opcode"] == "DeleteTenant":
            performTenantCleanup(tenant)
            return
    except:
        logging.exception("Testing Cleanup")

    r_collection = None
    try:
        filename = msg_dict["filename"]

        uid = None
        if msg_dict.has_key('uid'):
            uid = msg_dict['uid']

            collection = MongoClient(mongo_url)[tenant].uploadStats
            collection.update({'uid':uid},{'$inc':{"FPProcessing.count":1}})
            if metrics_url is not None:
                try:
                    r_collection = MongoClient(metrics_url)["remote_"+tenant].uploadStats
                    r_collection.insert({'uid':uid, "FPProcessing": {"count":1}})
                except:
                    logging.exception("Remote collection:")
                    r_collection = None

        source = tenant + "/" + filename

        if usingAWS:
            """
            Check if the file exists in S3. 
            """ 
            file_key = bucket.get_key(source)
            if file_key is None:
                logging.error("NOT FOUND: {0} not in S3\n".format(source))     
                connection1.basicAck(ch,method)
                
                return

            """
            Check if the file has already been processed. TODO:
            """
            checkpoint = source + ".processed"
            #chkpoint_key = bucket.get_key(checkpoint)
            #if chkpoint_key is not None:
            #    errlog.write("ALREADY PROCESSED: {0} \n".format(source))     
            #    errlog.flush()
            #    return
        else:
            print "Downloading and extracting file"

        """
        Download the file and extract:
        """ 
        dest_file = BAAZ_DATA_ROOT + tenant + "/" + filename
        destination = os.path.dirname(dest_file)
        print destination
        if not os.path.exists(destination):
            os.makedirs(destination)

        if usingAWS:
            d_file = open(dest_file, "w+")
            file_key.get_contents_to_file(d_file)
            d_file.close()

        logpath = destination + "/" + BAAZ_PROCESSING_DIRECTORY
        if os.path.exists(logpath):
            shutil.rmtree(logpath)
        os.makedirs(logpath)
        tar = None
        if dest_file.endswith(".gz"):
            tar = tarfile.open(dest_file, mode="r:gz")
            tar.extractall(path=logpath)
            tar.close()
        elif dest_file.endswith(".tar"):
            tar = tarfile.open(dest_file)
            tar.extractall(path=logpath)
            tar.close()
        else:
            shutil.copy(dest_file, logpath) 
    except:
        logging.exception("Downloading file")

    logging.info("Extracted file : {0} \n".format(dest_file))     
    if not usingAWS:
        print "Extracted file to /mnt/volume1/[tenent]/processing"
   
    try:
        """
        Parse the data.
        """
        context = tenant
        mongoconn = Connector.getConnector(context)
        if mongoconn is None:
            mongoconn = MongoConnector({'host':mongo_url, 'context':context, \
                                    'create_db_if_not_exist':True})

        parseDir(tenant, logpath, mongoconn)

        if usingAWS:
            """
            Checkpoint the file processing.
            """
            chkpoint_key = Key(bucket)
            chkpoint_key.key = checkpoint
            chkpoint_key.set_contents_from_string("Processed")
            logging.info("Processed file : {0} \n".format(dest_file))     

        for en in mongoconn.entities:
            entity = mongoconn.getEntity(en)
            if not entity.etype == 'HADOOP_JOB': 
                continue

            jinst_dict = {'entity_id':entity.eid} 
            prog_type = ""
            if entity.instances[0].config_data.has_key("hive.query.string"):
                jinst_dict['program_type'] = "Hive"
                jinst_dict['query'] = entity.name
            elif entity.instances[0].config_data.has_key("pig.script.features"):
                jinst_dict['program_type'] = "Pig"
                jinst_dict['pig_features'] = int(entity.instances[0].config_data['pig.script.features'])
            else:
                logging.info("Progname found {0}\n".format(entity.name))
                continue

            compiler_msg = {'tenant':tenant, 'job_instances':[jinst_dict]}
            if uid is not None:
                compiler_msg['uid'] = uid
            message = dumps(compiler_msg)
            connection1.publish(ch,'','compilerqueue',message)
            incrementPendingMessage(collection, uid)
            logging.info("Published Compiler Message {0}\n".format(message))

        for en in mongoconn.entities:
            entity = mongoconn.getEntity(en)
            if not entity.etype == 'SQL_QUERY': 
                continue

            jinst_dict = {'entity_id':entity.eid} 
            jinst_dict['program_type'] = "SQL"
            jinst_dict['query'] = entity.name
            compiler_msg = {'tenant':tenant, 'job_instances':[jinst_dict]}
            if uid is not None:
                compiler_msg['uid'] = uid
            message = dumps(compiler_msg)
            connection1.publish(ch,'','compilerqueue',message)
            incrementPendingMessage(collection, uid)
            logging.info("Published Compiler Message {0}\n".format(message))
    except:
        logging.exception("Parsing the input and Compiler Message")

    try:
        math_msg = {'tenant':tenant, 'opcode':"Frequency-Estimation"}
        if uid is not None:
            math_msg['uid'] = uid
        job_insts = {}
        for en in mongoconn.entities:
            entity = mongoconn.getEntity(en)
            if not entity.etype == 'HADOOP_JOB':
                continue
            job_insts[entity.eid] = {'program_id':entity.eid}
        math_msg['job_instances'] = job_insts.values()
        message = dumps(math_msg)
        connection1.publish(ch,'','mathqueue',message)
        incrementPendingMessage(collection, uid)

        logging.info("Published Message {0}\n".format(message))

        math_msg = {'tenant':tenant, 'opcode':"BaseStats"}
        if uid is not None:
            math_msg['uid'] = uid
        message = dumps(math_msg)
        connection1.publish(ch,'','mathqueue',message)
        incrementPendingMessage(collection, uid)
        logging.info("Published Message {0}\n".format(message))
    except:
        logging.exception("Publishing Math Message")

    try:
        mongoconn.close()
        if msg_dict.has_key('uid'):
            #if uid has been set, the variable will be set already
            collection.update({'uid':uid},{"$set": {"FPProcessing.time":(time.time()-starttime)}})
            if r_collection is not None:
                r_collection.update({'uid':uid},{"$set": {"FPProcessing.time":(time.time()-starttime)}})
    except:
        logging.logfile("While closing mongo")

    connection1.basicAck(ch,method)

connection1 = RabbitConnection(callback, ['ftpupload'],['compilerqueue','mathqueue'], {"Fanout": {'type':"fanout"}},BAAZ_FP_LOG_FILE)

print "FPProcessingService going to start consuming"

connection1.run()


print "Oops I'm done"

