#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenant> <log Directory>
"""
from flightpath import cluster_config
from flightpath.parsing.hadoop.HadoopConnector import *
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.XplainBlockingConnection import *
from flightpath.services.RotatingS3FileHandler import *
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from flightpath.utils import *
from flightpath.Provenance import getMongoServer
from flightpath.clustering.querygroup import QueryGroup
import flightpath.thriftclient.compilerthriftclient as tclient

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
from rlog import RedisHandler

BAAZ_DATA_ROOT="/mnt/volume1/"
XPLAIN_LOG_FILE = "/var/log/cloudera/navopt/XplainAdvAnalyticsService.err"

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
usingAWS = config.getboolean("mode", "usingAWS")
if usingAWS:
    from boto.s3.key import Key
    import boto
    from datadog import initialize, statsd

mode = cluster_config.get_cluster_mode()
logging_level = logging.INFO
if mode == "development":
    logging_level = logging.INFO

rabbitserverIP = config.get("RabbitMQ", "server")

"""
For VM there is not S3 connectivity. Save the logs with a timestamp.
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(XPLAIN_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(XPLAIN_LOG_FILE, XPLAIN_LOG_FILE+timestr)
    #no datadog statsd on VM
    statsd = None

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=XPLAIN_LOG_FILE,level=logging_level,datefmt='%m/%d/%Y %I:%M:%S %p')
es_logger = logging.getLogger('elasticsearch')
es_logger.propagate = False
es_logger.setLevel(logging.WARN)

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(XPLAIN_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))
    redis_host = config.get("RedisLog", "server")
    if redis_host:
        logging.getLogger().addHandler(RedisHandler('logstash', level=logging_level, host=redis_host, port=6379))

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
    clog = params['clog']
    if 'opcode' in params:
        clog.info("Calling the analytics callback for opcode %s"%(params['opcode']))
    else:
        clog.info("Calling the analytics callback with no opcode.")
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


def analyzeHAQR(query, platform, tenant, eid, source_platform, db, redis_conn, clog):
    if platform not in ["impala", "hive"]:
        return  # currently HAQR supported only for impala

    query = query.encode('ascii', 'ignore')
    queryFsmFile = "/etc/xplain/QueryFSM.csv"
    selectFsmFile = "/etc/xplain/SelectFSM.csv"
    whereFsmFile = "/etc/xplain/WhereFSM.csv"
    groupByFsmFile = "/etc/xplain/GroupbyFSM.csv"
    whereSubClauseFsmFile = "/etc/xplain/WhereSubclauseFSM.csv"
    fromFsmFile = "/etc/xplain/FromFSM.csv"
    selectSubClauseFsmFile = "/etc/xplain/SelectSubclauseFSM.csv"
    groupBySubClauseFsmFile = "/etc/xplain/GroupbySubclauseFSM.csv"
    fromSubClauseFsmFile = "/etc/xplain/FromSubclauseFSM.csv"
    colFsmFile = "/etc/xplain/colFSM.csv"
    colListFsmFile = "/etc/xplain/colListFSM.csv"
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
        "colFsmFile": colFsmFile,
        "colListFsmFile": colListFsmFile,
        "target_platform": platform,
        "source_platform": source_platform
    }

    """
    For HAQR processing the opcode is 4.
    """
    opcode = 4
    retries = 3
    response = tclient.send_compiler_request(opcode, data_dict, retries)
    if response.isSuccess:
        clog.info("HAQR Got Done")
    else:
        clog.error("compiler request failed")
        return None

    data = None
    data = loads(response.result)

    clog.info(dumps(data))

    updateMongoRedisforHAQR(db, redis_conn, data, tenant, eid)

    return


def updateRedisforimpala(redis_conn, data, tenant, eid):
    if data['platformCompilationStatus']['Impala']['queryStatus'] == "SUCCESS":
        redis_conn.incrEntityCounter("HAQR", "impalaSuccess", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "impalaFail", sort=False, incrBy=1)

    clauseStatusData = data['platformCompilationStatus']['Impala']['clauseStatus']

    if clauseStatusData is None:
        return
    if 'Select' in clauseStatusData:
        if clauseStatusData['Select']['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaSelectSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaSelectFail", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData['Select']:
                for subClause in clauseStatusData['Select']['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaSelectSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaSelectSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseSelectFailure", sort=False, incrBy=1)

    if 'From' in clauseStatusData:
        if clauseStatusData['From']['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaFromSuccess", sort=False, incrBy=1)
        elif clauseStatusData['From']['clauseStatus'] == "AUTO_SUGGEST":
            redis_conn.incrEntityCounter("HAQR", "impalaFromAutoCorrect", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaFromFailure", sort=False, incrBy=1)

        if 'subClauseList' in clauseStatusData["From"]:
            for subClause in clauseStatusData["From"]['subClauseList']:
                if subClause['clauseStatus'] == "SUCCESS":
                    redis_conn.incrEntityCounter("HAQR", "impalaFromSubClauseSuccess", sort=False, incrBy=1)
                elif subClause['clauseStatus'] == "AUTO_SUGGEST":
                    redis_conn.incrEntityCounter("HAQR", "impalaFromSubClauseAutoCorrect", sort=False, incrBy=1)
                else:
                    redis_conn.incrEntityCounter("HAQR", "impalaFromSubClauseFailure", sort=False, incrBy=1)
                    redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseFromFailure", sort=False, incrBy=1)

    if "Group By" in clauseStatusData:
        if clauseStatusData["Group By"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaGroupBySuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaGroupByFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Group By"]:
                for subClause in clauseStatusData["Group By"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaGroupBySubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaGroupBySubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseGroupByFailure", sort=False, incrBy=1)

    if "Where" in clauseStatusData:
        if clauseStatusData["Where"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaWhereSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaWhereFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Where"]:
                for subClause in clauseStatusData["Where"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaWhereSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaWhereSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseWhereFailure", sort=False, incrBy=1)

    if "Update" in clauseStatusData:
        if clauseStatusData["Update"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaUpdateSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaUpdateFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Update"]:
                for subClause in clauseStatusData["Update"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaUpdateSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaUpdateSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseUpdateFailure", sort=False, incrBy=1)

    if "Delete" in clauseStatusData:
        if clauseStatusData["Delete"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaDeleteSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaDeleteFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Delete"]:
                for subClause in clauseStatusData["Delete"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaDeleteSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaDeleteSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseDeleteFailure", sort=False, incrBy=1)

    if "Col-List" in clauseStatusData:
        if clauseStatusData["Col-List"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaColumnSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaColumnFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Col-List"]:
                for subClause in clauseStatusData["Col-List"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaColumnSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaColumnSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseColumnFailure", sort=False, incrBy=1)

    if "Other" in clauseStatusData:
        if clauseStatusData["Other"]['clauseStatus'] == "FAIL":
            redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseOtherFailure", sort=False, incrBy=1)
    return


def updateRedisforhive(redis_conn, data, tenant, eid):
    if data['platformCompilationStatus']['Hive']['queryStatus'] == "SUCCESS":
        redis_conn.incrEntityCounter("HAQR", "hiveSuccess", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "hiveFail", sort=False, incrBy=1)

    clauseStatusData = data['platformCompilationStatus']['Hive']['clauseStatus']

    if clauseStatusData is None:
        return

    if 'Select' in clauseStatusData:
        if clauseStatusData['Select']['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveSelectSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveSelectFail", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData['Select']:
                for subClause in clauseStatusData['Select']['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "hiveSelectSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "hiveSelectSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseSelectFailure", sort=False, incrBy=1)

    if 'From' in clauseStatusData:
        if clauseStatusData['From']['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveFromSuccess", sort=False, incrBy=1)
        elif clauseStatusData['From']['clauseStatus'] == "AUTO_SUGGEST":
            redis_conn.incrEntityCounter("HAQR", "hiveFromAutoCorrect", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveFromFailure", sort=False, incrBy=1)

        if 'subClauseList' in clauseStatusData["From"]:
            for subClause in clauseStatusData["From"]['subClauseList']:
                if subClause['clauseStatus'] == "SUCCESS":
                    redis_conn.incrEntityCounter("HAQR", "hiveFromSubClauseSuccess", sort=False, incrBy=1)
                elif subClause['clauseStatus'] == "AUTO_SUGGEST":
                    redis_conn.incrEntityCounter("HAQR", "hiveFromSubClauseAutoCorrect", sort=False, incrBy=1)
                else:
                    redis_conn.incrEntityCounter("HAQR", "hiveFromSubClauseFailure", sort=False, incrBy=1)
                    redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseFromFailure", sort=False, incrBy=1)

    if "Group By" in clauseStatusData:
        if clauseStatusData["Group By"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveGroupBySuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveGroupByFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Group By"]:
                for subClause in clauseStatusData["Group By"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "hiveGroupBySubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "hiveGroupBySubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseGroupByFailure", sort=False, incrBy=1)

    if "Where" in clauseStatusData:
        if clauseStatusData["Where"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveWhereSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveWhereFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Where"]:
                for subClause in clauseStatusData["Where"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "hiveWhereSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "hiveWhereSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseWhereFailure", sort=False, incrBy=1)

    if "Update" in clauseStatusData:
        if clauseStatusData["Update"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveUpdateSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveUpdateFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Update"]:
                for subClause in clauseStatusData["Update"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "hiveUpdateSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "hiveUpdateSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseUpdateFailure", sort=False, incrBy=1)

    if "Delete" in clauseStatusData:
        if clauseStatusData["Delete"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveDeleteSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveDeleteFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Delete"]:
                for subClause in clauseStatusData["Delete"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "hiveDeleteSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "hiveDeleteSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseDeleteFailure", sort=False, incrBy=1)

    if "Col-List" in clauseStatusData:
        if clauseStatusData["Col-List"]['clauseStatus'] == "SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "hiveColumnSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "hiveColumnFailure", sort=False, incrBy=1)
            if 'subClauseList' in clauseStatusData["Col-List"]:
                for subClause in clauseStatusData["Col-List"]['subClauseList']:
                    if subClause['clauseStatus'] == "SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "hiveColumnSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "hiveColumnSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseColumnFailure", sort=False, incrBy=1)

    if "Other" in clauseStatusData:
        if clauseStatusData["Other"]['clauseStatus'] == "FAIL":
            redis_conn.incrEntityCounter(eid, "HAQRhiveQueryByClauseOtherFailure", sort=False, incrBy=1)
    return


def updateMongoRedisforHAQR(db, redis_conn, data, tenant, eid):
    redis_conn.createEntityProfile("HAQR", "HAQR")

    redis_conn.incrEntityCounter("HAQR", "numInvocation", sort=False, incrBy=1)
    if data['sourceStatus'] == 'SUCCESS':
        redis_conn.incrEntityCounter("HAQR", "sourceSucess", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "sourceFailure", sort=False, incrBy=1)

    if 'platformCompilationStatus' in data and data['platformCompilationStatus']:
        if 'Impala' in data['platformCompilationStatus']:
            db.entities.update({'eid': eid}, {"$set": {'profile.Compiler.HAQR.platformCompilationStatus.Impala': data['platformCompilationStatus']['Impala']}})
            updateRedisforimpala(redis_conn, data, tenant, eid)
        if 'Hive' in data['platformCompilationStatus']:
            db.entities.update({'eid': eid}, {"$set": {'profile.Compiler.HAQR.platformCompilationStatus.Hive': data['platformCompilationStatus']['Hive']}})
            updateRedisforhive(redis_conn, data, tenant, eid)

    return

def process_HAQR_request(msg_dict, clog):
    client = getMongoServer(msg_dict['tenant'])
    db = client[msg_dict['tenant']]
    redis_conn = RedisConnector(msg_dict['tenant'])

    analyzeHAQR(msg_dict['query'], msg_dict['key'], msg_dict['tenant'], \
                msg_dict['eid'], msg_dict['source_platform'], db, redis_conn, clog)

def callback(ch, method, properties, body):

    startTime = time.time()
    msg_dict = loads(body)

    logging.debug("Analytics: Got message "+ str(msg_dict))

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
    log_dict = {'tag':'advanalytics', 'tenant':msg_dict['tenant'], 'opcode':msg_dict['opcode']}
    if 'uid' in msg_dict:
        log_dict['uid'] = msg_dict['uid']
    clog = LoggerCustomAdapter(logging.getLogger(__name__), log_dict)
    clog.info("Logging the message")
    #check if the request is for HAQR processing
    if opcode == "HAQRPhase":
        try:
            process_HAQR_request(msg_dict, clog)
        except:
            clog.exception('HAQR failed for tenant: %s.'%(tenant))


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
        client = getMongoServer(tenant)
        db = client[tenant]
        redis_conn = RedisConnector(tenant)
        if not checkUID(redis_conn, uid):
            """
            Just drain the queue.
            """
            connection1.basicAck(ch,method)
            return

        collection = client[tenant].uploadStats
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
            clog.error("Section "+ section + " Does not have all params")
            if mathconfig.has_option(section, "BatchMode") and\
                mathconfig.get(section, "BatchMode") == "True" and\
                received_msgID is not None:
                if (int(received_msgID.split("-")[1])%40) > 0:
                    continue

            if mathconfig.has_option(section, "NotificationName"):
                notif_queue = mathconfig.get(section, "NotificationQueue")
                notif_name = mathconfig.get(section, "NotificationName")
                message = {"messageType" : notif_name, "tenantId": tenant}
                clog.info("Sending message to node!")
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
            clog.info("Executing " + section + " for " + tenant)
            ctx = analytics_context
            ctx.tenant = tenant
            ctx.entityid = entityid
            ctx.collection = collection
            ctx.redis_conn = redis_conn
            ctx.callback = analytics_callback
            ctx.rabbit_conn = connection1
            ctx.rabbit_ch = ch
            ctx.clog = clog
            ctx.msg_dict = msg_dict

            if 'uid' in msg_dict:
                ctx.uid = uid
            else:
                ctx.uid = None

            if 'outmost_query' in msg_dict:
                ctx.outmost_query = msg_dict['outmost_query']

            opcode_startTime = time.time()
            methodToCall(tenant, ctx)
            #send stats to datadog
            if statsd:
                totalTime = ((time.time() - opcode_startTime) * 1000)
                statsd.timing("advanalytics.per.opcode.time", totalTime, tags=["tenant:"+tenant, "uid:"+uid, "opcode:"+opcode])

            if 'uid' in msg_dict:
                redis_conn.incrEntityCounter(uid, stats_success_key, incrBy = 1)
                redis_conn.incrEntityCounter(uid, stats_failure_key, incrBy = 0)

            if mathconfig.has_option(section, "NotificationName"):
                notif_queue = mathconfig.get(section, "NotificationQueue")
                notif_name = mathconfig.get(section, "NotificationName")
                message = {"messageType" : notif_name, "tenantId": tenant}
                clog.info("Sending message to node!")
                connection1.publish(ch,'', notif_queue, dumps(message))
        except:
            clog.exception("Section :"+section)
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

    clog.info("Event Processing Complete")
    if opcode == "PhaseTwoAnalysis":
        collection.update({'uid':"0"},{'$set': { "done":True}})

    if int(redis_conn.numMessagesPending(uid)) == 0:
        #The length function in the if statement is a count of the mending messages
        timest = int(time.time() * 1000)
        redis_conn.setEntityProfile(uid, {"Phase2MessageProcessed":timest})
        try:
            write_upload_stats.run_workflow(tenant, {'uid':uid})
        except:
            clog.exception("Could not write upload stats dict to MongoDB: ")

    connection1.basicAck(ch, method)

    endTime = time.time()
    if 'uid' in msg_dict:
        #if uid has been set, the variable will be set already
        redis_conn.incrEntityCounter(uid, "Math.time", incrBy=(endTime - startTime))
    #send stats to datadog
    if statsd:
        totalTime = ((time.time() - startTime) * 1000)
        statsd.timing("advanalytics.per.msg.time", totalTime, tags=["tenant:"+tenant, "uid:"+uid])

connection1 = RabbitConnection(callback, ['advanalytics'], ['elasticpub'], {}, prefetch_count=1)

logging.info("XplainAdvAnalytics going to start consuming")

connection1.run()
logging.info("Closing XplainAdvAnalytics")
