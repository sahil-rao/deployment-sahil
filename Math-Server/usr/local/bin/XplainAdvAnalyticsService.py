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
from flightpath.clustering.querygroup import QueryGroup
from flightpath.services.xplain_log_handler import XplainLogstashHandler
import baazmath.workflows.write_upload_stats as write_upload_stats
from json import *
#from baazmath.interface.BaazCSV import *
#from subprocess import Popen, PIPE
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
XPLAIN_LOG_FILE = "/var/log/XplainAdvAnalyticsService.err"

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
    if os.path.isfile(XPLAIN_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(XPLAIN_LOG_FILE, XPLAIN_LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=XPLAIN_LOG_FILE,level=logging.INFO,datefmt='%m/%d/%Y %I:%M:%S %p')

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(XPLAIN_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))
    logging.getLogger().addHandler(XplainLogstashHandler(tags=['advanalyticsservice', 'backoffice']))

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

def analyzeHAQR(query, platform, tenant, eid, source_platform, db, redis_conn):
    if platform not in ["impala", "hive"]:
        return #currently HAQR supported only for impala

    timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    destination = BAAZ_DATA_ROOT+'haqr-' + tenant + "/" + timestr

    if not os.path.exists(destination):
        os.makedirs(destination)

    dest_file_name = destination + "/input%s.query"%(platform)
    dest_file = open(dest_file_name, "w+")
    query = query.encode('ascii', 'ignore')
    dest_file.write(query)
    dest_file.flush()
    dest_file.close()

    output_file_name = destination + "/haqr%s.out"%(platform)

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
        "InputFile": dest_file_name,
        "OutputFile": output_file_name,
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

    data = dumps(data_dict)

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

    client_socket.send("1\n");
    """
    For HAQR processing the opcode is 4.
    """
    client_socket.send("4\n");
    data = data + "\n"
    client_socket.send(data)
    rx_data = client_socket.recv(512)

    if rx_data == "Done":
        logging.info("HAQR Got Done")

    client_socket.close()
    data = None
    logging.info("Loading file : "+ output_file_name)
    with open(output_file_name) as data_file:
        data = load(data_file)

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
            db.entities.update({'eid':eid},{"$set":{'profile.Compiler.HAQR.platformCompilationStatus.Impala':data['platformCompilationStatus']['Impala']}})
            updateRedisforimpala(redis_conn, data, tenant, eid)
        if 'Hive' in data['platformCompilationStatus']:
            db.entities.update({'eid':eid},{"$set":{'profile.Compiler.HAQR.platformCompilationStatus.Hive':data['platformCompilationStatus']['Hive']}})
            updateRedisforhive(redis_conn, data, tenant, eid)

    return

def process_HAQR_request(msg_dict):
    mongo_url = getMongoServer(msg_dict['tenant'])
    db = MongoClient(mongo_url)[msg_dict['tenant']]
    redis_conn = RedisConnector(msg_dict['tenant'])
    
    analyzeHAQR(msg_dict['query'], msg_dict['key'], msg_dict['tenant'], \
                msg_dict['eid'], msg_dict['source_platform'], db, redis_conn)

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
    #check if the request is for HAQR processing
    if opcode == "HAQRPhase":
        try:
            process_HAQR_request(msg_dict)
        except:
            logging.exception('HAQR failed for tenant: %s.'%(tenant))
    

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
        
        if opcode == 'Cluster':
            try:
                logging.info("Clustering...")
                clause_combo = msg_dict['clause_combo']
                cluster_clause = msg_dict['cluster_clause']
                qgroup = QueryGroup(tenant, clause_combo)
                qgroup.cluster(cluster_clause)
                redis_conn.delMessagePending(uid, received_msgID, message_type='cluster')
                connection1.basicAck(ch, method)
                return
            except:
                logging.exception('Cluster failed for tenant: %s.' % tenant)

        
      
        collection = MongoClient(mongo_url)[tenant].uploadStats
        redis_conn.incrEntityCounter(uid, 'Math.count', incrBy = 1)
    else:
        """
        We do not expect anything without UID. Discard message if not present.
        """
    	connection1.basicAck(ch,method)
        return

    mathconfig = ConfigParser.RawConfigParser()
    mathconfig.read("/etc/xplain/adv_analytics.cfg")

    for section in mathconfig.sections():
        sectionStartTime = time.time()
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
            ctx.rabbit_conn = connection1
            ctx.rabbit_ch = ch
            if 'uid' in msg_dict:
                ctx.uid = uid
            else:
                ctx.uid = None

            if 'outmost_query' in msg_dict:
                ctx.outmost_query = msg_dict['outmost_query']

            methodToCall(tenant, ctx)

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
    if opcode == "PhaseTwoAnalysis":
        collection.update({'uid':"0"},{'$set': { "done":True}})        

    if int(redis_conn.numMessagesPending(uid)) == 0:
        #The length function in the if statement is a count of the mending messages
        timest = int(time.time() * 1000)
        redis_conn.setEntityProfile(uid, {"Phase2MessageProcessed":timest})
        write_upload_stats.run_workflow(tenant, {})

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
                connection1.publish(ch,'', notif_queue, dumps(out_dict))
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

connection1 = RabbitConnection(callback, ['advanalytics'], [], {}, prefetch_count=1)

logging.info("XplainAdvAnalytics going to start consuming")

connection1.run()
logging.info("Closing XplainAdvAnalytics")
