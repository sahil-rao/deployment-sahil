#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenant> <log Directory>
"""
#from flightpath.parsing.hadoop.HadoopConnector import *
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.RotatingS3FileHandler import *
from flightpath.utils import *
from flightpath.parsing.ParseDemux import *
from flightpath.Provenance import getMongoServer
import sys
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from json import *
import pika
import shutil
import os
import tarfile
import ConfigParser
import datetime
import time
import logging
import socket
import urllib

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
metrics_url = None


"""
For VM there is not S3 connectivity. Save the logs with a timestamp. 
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(BAAZ_FP_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(BAAZ_FP_LOG_FILE, BAAZ_FP_LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=BAAZ_FP_LOG_FILE,level=logging.INFO,datefmt='%m/%d/%Y %I:%M:%S %p')

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    bucket = boto_conn.get_bucket('partner-logs') 
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(BAAZ_FP_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))

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

def performTenantCleanup(tenant):
    logging.info("Cleaning Tenant "+ tenant) 
    destination = BAAZ_DATA_ROOT + tenant     
    if os.path.exists(destination):
        shutil.rmtree(destination)
    destination = '/mnt/volume1/compile-' + tenant 
    if os.path.exists(destination):
        shutil.rmtree(destination)

def updateRelationCounter(redis_conn, eid):

    relationshipTypes = ['QUERY_SELECT', 'QUERY_JOIN', 'QUERY_FILTER', "READ", "WRITE",
                         'QUERY_GROUPBY', 'QUERY_ORDERBY', "COOCCURRENCE_GROUP"]

    relations_to = redis_conn.getRelationships(eid, None, None)
    for rel in relations_to:
        if rel['rtype'] in relationshipTypes:
            redis_conn.incrRelationshipCounter(eid, rel['end_en'], rel['rtype'], "instance_count", incrBy=1)

    relations_from = redis_conn.getRelationships(None, eid, None)
    for rel in relations_to:
        if rel['rtype'] in relationshipTypes:
            redis_conn.incrRelationshipCounter(rel['start_en'], eid, rel['rtype'], "instance_count", incrBy=1)

def sendToCompiler(tenant, eid, uid, ch, mongoconn, redis_conn, collection, update=False, name=None, etype=None, data=None):

    if eid is None:
        if not etype == 'SQL_QUERY': 
            return

        """
        For SQL query, send any new query to compiler first.
        If this is an update to existing query, send a message to math,
        for update analysis.
        """
        if update == False:
            jinst_dict = {} 
            jinst_dict['program_type'] = "SQL"
            jinst_dict['query'] = name
            if data is not None:
                jinst_dict['data'] = data
            compiler_msg = {'tenant':tenant, 'job_instances':[jinst_dict]}

            if uid is not None:
                compiler_msg['uid'] = uid
            message_id = genMessageID("FP", collection)
            compiler_msg['message_id'] = message_id
            message = dumps(compiler_msg)
            connection1.publish(ch,'','compilerqueue',message)
            incrementPendingMessage(collection, redis_conn, uid, message_id)
            logging.info("Published Compiler Message {0}\n".format(message))
        else:
            redis_conn.incrEntityCounter(eid, "instance_count", incrBy=1)

            mongoconn.db.dashboard_data.update({'tenant':tenant}, \
                {'$inc' : {"TotalQueries": 1, "unique_count": 1}})

            """
            Get relationships for the given entity.
            """
            updateRelationCounter(redis_conn, eid)

        return

    entity = mongoconn.getEntity(eid)
    if entity.etype == 'HADOOP_JOB':

        pub = True
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
            pub = False
        if pub == True:
            compiler_msg = {'tenant':tenant, 'job_instances':[jinst_dict]}
            if data is not None:
                compiler_msg['data'] = data
            if uid is not None:
                compiler_msg['uid'] = uid
            message_id = genMessageID("FP", collection)
            compiler_msg['message_id'] = message_id
            message = dumps(compiler_msg)
            connection1.publish(ch,'','compilerqueue',message)
            incrementPendingMessage(collection, redis_conn, uid, message_id)
            logging.info("Published Compiler Message {0}\n".format(message))
    
def callback(ch, method, properties, body):
    starttime = time.time()
    
    try:
        msg_dict = loads(body)
    except:
        logging.exception("Could not load the message JSON")

    logging.info("FPPS Got message "+ str( msg_dict))
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

    mongo_url = getMongoServer(tenant)
    r_collection = None
    dest_file = None
    try:
        filename = msg_dict["filename"]
        filename = urllib.unquote(filename)

        uid = None
        if msg_dict.has_key('uid'):
            uid = msg_dict['uid']

            collection = MongoClient(mongo_url)[tenant].uploadStats
            collection.update({'uid':uid},{'$inc':{"FPProcessing.count":1}, '$set':{"FPProcessing.socket":socket.gethostbyname(socket.gethostname())}})
            startProcessingPhase(collection, uid)
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
            logging.info("Downloading and extracting file")

        """
        Download the file and extract:
        """ 
        dest_file = BAAZ_DATA_ROOT + tenant + "/" + filename
        destination = os.path.dirname(dest_file)
        logging.info("Destination: "+str(destination))
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
        logging.info("Extracted file to /mnt/volume1/[tenent]/processing")
   
    try:
        """
        Parse the data.
        """
        context = tenant
        mongoconn = Connector.getConnector(context)
        if mongoconn is None:
            mongoconn = MongoConnector({'host':mongo_url, 'context':context, \
                                    'create_db_if_not_exist':True})

        redis_conn = RedisConnector(tenant)
        '''
        Incrmements an Pre-Processing count, sends to compiler, then decrements the count
        '''
        message_id = genMessageID("Pre", collection)
        incrementPendingMessage(collection, redis_conn, uid, message_id)
        logging.info("Incremementing message count: " + message_id)

        parseDir(tenant, logpath, mongoconn, redis_conn, sendToCompiler, uid, ch, collection)

        callback_params = {'tenant':tenant, 'connection':connection1, 'channel':ch, 'uid':uid, 'queuename':'mathqueue'}
        decrementPendingMessage(collection, redis_conn, uid, message_id, end_of_phase_callback, callback_params)
        logging.info("Decrementing message count: " + message_id)

        if usingAWS:
            """
            Checkpoint the file processing.
            """
            chkpoint_key = Key(bucket)
            chkpoint_key.key = checkpoint
            chkpoint_key.set_contents_from_string("Processed")
            logging.info("Processed file : {0} \n".format(dest_file))     

    except:
        logging.exception("Parsing the input and Compiler Message")

    try:

        math_msg = {'tenant':tenant, 'opcode':"BaseStats"}
        if uid is not None:
            math_msg['uid'] = uid
        message_id = genMessageID("FP", collection)
        math_msg['message_id'] = message_id
        message = dumps(math_msg)
        connection1.publish(ch,'','mathqueue',message)
        collection.update({'uid':uid},{'$inc':{"Math2MessageCount":1}})
        incrementPendingMessage(collection, redis_conn, uid,message_id)
        logging.info("Published Message {0}\n".format(message))
    except:
        logging.exception("Publishing Math Message")

    try:
        if uid is not None:
            #This query finds the latest upload and stores that timestamp in the timestamp variable
            timestamp = int(list(collection.find({},{"_id":0, "timestamp":1}).sort([("timestamp",-1)]).limit(1))[0]["timestamp"])
            MongoClient(mongo_url)["xplainIO"].organizations.update({"guid":tenant},{"$set":{"uploads":collection.count(), \
                "queries":MongoClient(mongo_url)[tenant].entities.find({"etype":"SQL_QUERY"}).count(), \
                "lastTimeStamp": timestamp}})
    except:
        if uid is not None:
            MongoClient(mongo_url)["xplainIO"].organizations.update({"guid":tenant},{"$set":{"uploads":collection.count(), \
                "queries":MongoClient(mongo_url)[tenant].entities.find({"etype":"SQL_QUERY"}).count(), \
                "lastTimeStamp": 0}})  

    try:
        mongoconn.close()
        if msg_dict.has_key('uid'):
            #if uid has been set, the variable will be set already
            collection.update({'uid':uid},{"$set": {"FPProcessing.time":(time.time()-starttime)}})
            if r_collection is not None:
                r_collection.update({'uid':uid},{"$set": {"FPProcessing.time":(time.time()-starttime)}})
    except:
        logging.exception("While closing mongo")

    connection1.basicAck(ch,method)

connection1 = RabbitConnection(callback, ['ftpupload'],['compilerqueue','mathqueue'], {"Fanout": {'type':"fanout"}},BAAZ_FP_LOG_FILE)


logging.info("FPProcessingService going to start consuming")

connection1.run()

if usingAWS:
    boto_conn.close()
logging.info("Closing FPProcessingService")
