#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenant> <log Directory>
"""
from flightpath.parsing.hadoop.HadoopConnector import *
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.XplainBlockingConnection import *
from flightpath.services.RotatingS3FileHandler import *
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from flightpath.utils import *
from flightpath.Provenance import getMongoServer
from flightpath.services.xplain_log_handler import XplainLogstashHandler
from json import *
from baazmath.interface.BaazCSV import *
from subprocess import Popen, PIPE
import sys
import pika
import shutil
import os
import tarfile
import time
import datetime
import ConfigParser
import traceback
import logging
import importlib
import socket

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"
BAAZ_MATH_LOG_FILE = "/var/log/BaazMathService.err"

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
usingAWS = config.getboolean("mode", "usingAWS")
if usingAWS:
    from boto.s3.key import Key
    import boto

rabbitserverIP = config.get("RabbitMQ", "server")


"""
For VM there is not S3 connectivity. Save the logs with a timestamp. 
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(BAAZ_MATH_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(BAAZ_MATH_LOG_FILE, BAAZ_MATH_LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=BAAZ_MATH_LOG_FILE,level=logging.INFO,datefmt='%m/%d/%Y %I:%M:%S %p')

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(BAAZ_MATH_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))
    logging.getLogger().addHandler(XplainLogstashHandler(tags=['mathservice', 'backoffice'])

def generateBaseStats(tenant):
    """
    Create a destination/processing folder.
    """
    destination = "/tmp"
    #destination = '/mnt/volume1/base-stats-' + tenant + "/" + timestr 
    #if not os.path.exists(destination):
    #    os.makedirs(destination)

    dest_file_name = destination + "/test.csv"
    dest_file = open(dest_file_name, "w+")
    generateBaseStatsCSV(tenant, dest_file)
    dest_file.flush()
    dest_file.close()
   
    """
    Call Base stats generation.
    """ 

def storeResourceProfile(tenant):
    logging.info("Going to store resource profile\n")    
    if not os.path.isfile("/tmp/test_hadoop_job_resource_share.out"):
        return

    logging.info("Resource profile file found\n")
    mongoconn = Connector.getConnector(tenant)
    if mongoconn is None:
        mongoconn = MongoConnector({'host':getMongoServer(tenant), 'context':tenant, \
                                    'create_db_if_not_exist':True})

    with open("/tmp/test_hadoop_job_resource_share.out", "r") as resource_file:
        for line in resource_file:
            logging.info("Resource profile line :"+str(line) )
            if line.strip().startswith("Entity"):
                continue

            splits = line.strip().split()
            if not len(splits) == 2:
                continue

            entity = mongoconn.getEntity(splits[0])
            if entity is None:
                logging.error("Entity {0} not found for storing resource profile\n".format(splits[0]))    
                continue

            logging.info("Entity {0} resource profile {1}\n".format(splits[0], splits[1]))    
            resource_doc = { "Resource_share": splits[1]}
            mongoconn.updateProfile(entity, "Resource", resource_doc)
    mongoconn.close()

def end_of_phase_callback(params, current_phase):
    if current_phase > 1:
        logging.error("Attempted end of phase callback, but current phase > 1")
        return

    logging.info("Changing processing Phase")
    msg_dict = {'tenant':params['tenant'], 'opcode':"PhaseTwoAnalysis"} 
    msg_dict['uid'] = params['uid']
    message = dumps(msg_dict)
    params['connection'].publish(params['channel'],'',params['queuename'],message) 
    return

def analytics_callback(params):
    '''
    Callback method that is used to initiate the processing of a passed in opcode.
    '''
    if 'opcode' in params:
        logging.info("Calling the analytics callback for opcode %s"%(params['opcode']))
    else:
        logging.info("Calling the analytics callback with no opcode.")
    msg_dict = {'tenant':params['tenant'], 'opcode':params['opcode']}
    msg_dict['uid'] = params['uid']
    msg_dict['entityid'] = params["entityid"]
    collection = params["collection"]
    redis_conn = params["redis_conn"]
    message_id = genMessageID("Math", redis_conn, msg_dict['entityid'])
    msg_dict['message_id'] = message_id
    incrementPendingMessage(collection, redis_conn, msg_dict['uid'], message_id)

    message = dumps(msg_dict)
    params['connection'].publish(params['channel'],'',params['queuename'],message) 
    return

class analytics_context:
    pass

def callback(ch, method, properties, body):

    startTime = time.time()
    msg_dict = loads(body)

    logging.info("Analytics: Got message "+ str(msg_dict))

    """
    Validate the message.
    """ 
    if not msg_dict.has_key("tenant") or \
       not msg_dict.has_key("opcode"):
        logging.error("Invalid message received\n")

        connection1.basicAck(ch,method)
        return

    tenant = msg_dict['tenant']
    opcode = msg_dict['opcode']
    try:
        received_msgID = msg_dict['message_id']
    except:
        received_msgID = None
    uid = None
    if msg_dict.has_key('uid'):
        uid = msg_dict['uid']

        """
        Check if this is a valid UID. If it so happens that this flow has been deleted,
        then drop the message.
        """
        mongo_url = getMongoServer(tenant)
        db = MongoClient(mongo_url)[tenant]
        redis_conn = RedisConnector(tenant)
        if not checkUID(redis_conn, uid):
            """
            Just drain the queue.
            """
            connection1.basicAck(ch,method)
            return
      
        collection = db.uploadStats
        process_pref_col = db.adminSettings

            
        redis_conn.incrEntityCounter(uid, 'Math.count', incrBy = 1)
    else:
        """
        We do not expect anything without UID. Discard message if not present.
        """
        connection1.basicAck(ch,method)
        return

    callback_params = {'tenant':tenant, 'connection':connection1, 'channel':ch, 'uid':uid, 'queuename':'advanalytics'}

    mathconfig = ConfigParser.RawConfigParser()
    mathconfig.read("/etc/xplain/analytics.cfg")
    
    """
    Pull and update admin settings at upload to ensure user has prefs if admin didn't set anything
    """
    admin_pref_dict = process_pref_col.find_one({'type':'workflows'})
    if admin_pref_dict is None:
        admin_pref_dict = {}
        for section in mathconfig.sections():
            admin_pref_dict[section] = True
        admin_pref_dict["type"] = "workflows"
        process_pref_col.insert(admin_pref_dict)
    else:
        for section in mathconfig.sections():
            if section not in admin_pref_dict:
                admin_pref_dict[section] = True
        process_pref_col.update({'type': 'workflows'}, admin_pref_dict, upsert = True)
    
    for section in mathconfig.sections():
        sectionStartTime = time.time()
        
        if not admin_pref_dict[section]:
            logging.error("Section :"+ section + " Has been disabled for this workload")
            continue
               
        if not mathconfig.has_option(section, "Opcode") or\
           not mathconfig.has_option(section, "Import") or\
           not mathconfig.has_option(section, "Function"):
            logging.error("Section "+ section + " Does not have all params")
            if mathconfig.has_option(section, "BatchMode") and\
                mathconfig.get(section, "BatchMode") == "True" and\
                received_msgID is not None:
                if (int(received_msgID.split("-")[1])%40) > 0:
                    continue

            if mathconfig.has_option(section, "NotificationName"):
                notif_queue = mathconfig.get(section, "NotificationQueue")
                notif_name = mathconfig.get(section, "NotificationName")
                message = {"messageType" : notif_name, "tenantId": tenant}
                logging.info("Sending message to node!")
                connection1.publish(ch,'', notif_queue, dumps(message))
            continue
 
        if not opcode == mathconfig.get(section, "Opcode"):
            continue
        
        stats_success_key = "Math." + section + ".success"
        stats_failure_key = "Math." + section + ".failure"
        stats_time_key = "Math." + section + ".time"
        stats_phase_key = "Math." + section + ".phase"
        if mathconfig.has_option(section, "BatchMode") and\
            mathconfig.get(section, "BatchMode") == "True" and\
            received_msgID is not None:
            if (int(received_msgID.split("-")[1])%40) > 0:
                continue

        try:
            entityid = None
            if "entityid" in msg_dict:
                entityid = msg_dict["entityid"]

            mod = importlib.import_module(mathconfig.get(section, "Import"))
            methodToCall = getattr(mod, mathconfig.get(section, "Function"))
            logging.info("Executing " + section + " for " + tenant)
            ctx = analytics_context
            ctx.tenant = tenant
            ctx.entityid = entityid
            ctx.collection = collection
            ctx.redis_conn = redis_conn
            ctx.callback = analytics_callback
            if 'uid' in msg_dict:
                ctx.uid = uid
            else:
                ctx.uid = None

            if 'outmost_query' in msg_dict:
                ctx.outmost_query = msg_dict['outmost_query']

            ret = methodToCall(tenant, ctx)
            if ret is not None and ret == False:
                '''
                Attempt to requeue the message.
                If failed 10 times, will decrement pending message.
                '''
                requeue_status = connection1.requeue(ch,method, '', 'mathqueue', msg_dict)
                if not requeue_status:
                    decrementPendingMessage(collection, redis_conn, uid, received_msgID, end_of_phase_callback, callback_params)
                connection1.basicAck(ch,method)
                return

            if 'uid' in msg_dict:
                redis_conn.incrEntityCounter(uid, stats_success_key, incrBy = 1)
                redis_conn.incrEntityCounter(uid, stats_failure_key, incrBy = 0)

            if mathconfig.has_option(section, "NotificationName"):
                notif_queue = mathconfig.get(section, "NotificationQueue")
                notif_name = mathconfig.get(section, "NotificationName")
                message = {"messageType" : notif_name, "tenantId": tenant}
                logging.info("Sending message to node!")
                connection1.publish(ch,'', notif_queue, dumps(message))
        except:
            logging.exception("Section :"+section)
            if 'uid' in msg_dict:
                redis_conn.incrEntityCounter(uid, stats_success_key, incrBy = 0)
                redis_conn.incrEntityCounter(uid, stats_failure_key, incrBy = 1)
        if 'uid' in msg_dict:
            sectionEndTime = time.time()
            redis_conn.incrEntityCounter(uid, stats_time_key, incrBy = sectionEndTime-sectionStartTime)
            if opcode == "PhaseTwoAnalysis":
                stats_ip_key = "Math." + section + ".socket"
                redis_conn.setEntityProfile(uid, {stats_phase_key: 2, stats_ip_key: socket.gethostbyname(socket.gethostname())})

            else:
                redis_conn.setEntityProfile(uid, {stats_phase_key: 1})
        
    logging.info("Event Processing Complete")     
    decrementPendingMessage(collection, redis_conn, uid, received_msgID, end_of_phase_callback, callback_params)

    """
     Progress Bar update
    """
    notif_queue = "node-update-queue"
    logging.info("Going to check progress bar")     
    try:
        stats_dict = redis_conn.getEntityProfile(uid)
        if stats_dict is not None and\
            "total_queries" in stats_dict and\
            "processed_queries" in stats_dict and\
            ("query_message_id" in msg_dict or opcode == "PhaseTwoAnalysis"):
            if opcode != "PhaseTwoAnalysis":
                redis_conn.incrEntityCounter(uid, 'processed_queries', incrBy = 1)

            processed_queries = int(stats_dict["processed_queries"])
            total_queries = int(stats_dict["total_queries"])
            if (processed_queries%10 == 0 or\
               (total_queries) <= (processed_queries + 1)) and \
               int(redis_conn.numMessagesPending(uid)) != 0:
                #logging.info("Procesing progress bar event")     
                out_dict = {"messageType" : "uploadProgress", "tenantId": tenant, 
                            "completed": processed_queries + 1, "total":total_queries}
                connection1.publish(ch, 'node-update', '', dumps(out_dict))
    except:
        logging.exception("While making update to progress bar")

    """
     Progress Bar Update end
    """
    connection1.basicAck(ch,method)

    endTime = time.time()
    if msg_dict.has_key('uid'):
        #if uid has been set, the variable will be set already
        redis_conn.incrEntityCounter(uid, "Math.time", incrBy = endTime-startTime)


connection1 = RabbitConnection(callback, ['mathqueue'], [], {})

logging.info("BaazMath going to start consuming")

connection1.run()
logging.info("Closing BaazMath")
