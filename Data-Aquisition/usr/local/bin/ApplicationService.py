#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenant> <log Directory>
"""
#from flightpath.parsing.hadoop.HadoopConnector import *
from flightpath import cluster_config
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.RotatingS3FileHandler import *
from flightpath.utils import *
from flightpath.parsing.ParseDemux import *
from flightpath.Provenance import getMongoServer
import flightpath.thriftclient.compilerthriftclient as tclient

import sys
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from flightpath.ScaleModeConnector import *
import flightpath.services.app_get_table_detail as table_details
import flightpath.services.app_get_query_detail as query_details
import flightpath.services.app_get_upload_detail as upload_details
import flightpath.services.app_get_top_dim as top_dim
import flightpath.services.app_get_top_table_by_patterns as top_tables_by_pattern
import flightpath.services.app_get_top_tables as top_tables
import flightpath.services.app_get_tail_tables as tail_tables
import flightpath.services.app_get_columns_by_operator as columns_by_operator
import flightpath.services.app_get_simple_queries as simple_queries
import flightpath.services.app_get_table_stats as table_stats
import flightpath.services.app_get_table_transform_stats as table_transform_stats
import flightpath.services.app_get_query_transform_stats as query_transform_stats
import flightpath.services.app_get_column_stats as column_stats
import flightpath.services.app_get_workload_assessment as workload_assessment
import flightpath.services.app_get_access_patterns as access_patterns
import flightpath.services.app_cleanup_user as cleanup_user
import flightpath.services.app_add_table_volume as add_table_volume
import flightpath.services.app_get_impala_import as get_impala_import
from flightpath import FPConnector
from json import *
import elasticsearch
import shutil
import os
import tarfile
import ConfigParser
import datetime
import time
import logging
import socket
import importlib
import urllib
import traceback
from rlog import RedisHandler

APPSRV_LOG_FILE = "/var/log/cloudera/navopt/applicationserice.err"

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"

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
metrics_url = None

bucket_location = "partner-logs"
log_bucket_location = "xplain-servicelogs"

CLUSTER_MODE = config.get("ApplicationConfig", "mode")
CLUSTER_NAME = config.get("ApplicationConfig", "clusterName")

if CLUSTER_MODE is None:
    CLUSTER_MODE = 'production'


if CLUSTER_NAME is not None:
    bucket_location = CLUSTER_NAME

"""
For VM there is not S3 connectivity. Save the logs with a timestamp.
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(APPSRV_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(APPSRV_LOG_FILE, APPSRV_LOG_FILE+timestr)
    #no datadog statsd on VM
    statsd = None

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=APPSRV_LOG_FILE,level=logging_level,datefmt='%m/%d/%Y %I:%M:%S %p')
es_logger = logging.getLogger('elasticsearch')
es_logger.propagate = False
es_logger.setLevel(logging.WARN)

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    bucket = boto_conn.get_bucket(bucket_location)
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(APPSRV_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))
    redis_host = config.get("RedisLog", "server")
    if redis_host:
        logging.getLogger().addHandler(RedisHandler('logstash', level=logging_level, host=redis_host, port=6379))

def process_mongo_rewrite_request(ch, properties, tenant, instances, clog):

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

        sql_query = inst["query"]
        if len(sql_query.strip()) == 0:
            continue
        data_dict = { "input_query": sql_query}

        """
            3. Invoke compiler to generate Xplain RA.
        """
        try:
            """
                For Mongo rewrite the opcode is 3.
            """
            opcode = 3
            retries = 3
            response = tclient.send_compiler_request(opcode, data_dict, retries)

            if response.isSuccess == True:
                status = "SUCCESS"
            else:
                status = "FAILED"

            compile_doc = None
            """
                4. Read the output as a JSON.
            """
            if not result.isSuccess:
                resp_dict["status"] = "Failed"
                clog.error("compiler request failed")
            else:
                """
                    Read the output and send the RPC response.
                """
                compile_doc = None
                compile_doc = loads(response.result)

                """
                    5. Invoke mongo converter template engine to convert.
                """
                mongo_query = convert_to_mongo(compile_doc["QueryBlock"])
                resp_dict['mongo_queries'].append(mongo_query)

            resp_dict["status"] = "Success"
        except:
            clog.exception("Tenent {0}, {1}\n".format(tenant, traceback.format_exc()))
            resp_dict["status"] = "Failed"

    """
        6. Send the RPC response.
    """
    return resp_dict
    #ch.basic_publish(exchange='',
    #                 routing_key=properties.reply_to,
    #                 properties=pika.BasicProperties(correlation_id = \
    #                                                 properties.correlation_id),
    #                 body=dumps(resp_dict))


def callback(ch, method, properties, body):

    startTime = time.time()

    #send stats to datadog
    if statsd:
        statsd.increment('appservice.msg.count', 1)

    try:
        msg_dict = loads(body)
    except:
        logging.exception("Could not load the message JSON")
        return

    logging.debug("ApplicationService: Got message : "+ str(msg_dict))
    logging.debug("Correlation ID : "+ properties.correlation_id)
    if "opcode" not in msg_dict or 'tenant' not in msg_dict:
        logging.error('ApplicationService there was no opcode or tenant in msg_dict.')
        connection1.basicAck(ch,method)
        return

    tenant = msg_dict["tenant"]
    msg_dict["connection"] = connection1
    msg_dict["ch"] = ch
    client = getMongoServer(tenant)
    resp_dict = None

    log_dict = {'tenant':msg_dict['tenant'], 'opcode':msg_dict['opcode'], 'tag':'applicationservice'}
    if 'uid' in msg_dict:
        log_dict['uid'] = msg_dict['uid']
    clog = LoggerCustomAdapter(logging.getLogger(__name__), log_dict)
    try:
        """
         This needs to be dynamic in nature.
        """
        opcode_startTime = time.clock()
        if msg_dict["opcode"] == "ImpalaImport":

            clog.debug("Got the opcode of Impala import")
            filename = msg_dict["filename"]
            filename = urllib.unquote(filename)
            source = tenant + "/" + filename
            if usingAWS:
                if CLUSTER_NAME is not None:
                    source = "partner-logs/" + source
                """
                Check if the file exists in S3.
                """
                file_key = bucket.get_key(source)
                if file_key is None:
                    clog.error("NOT FOUND: {0} not in S3\n".format(source))
                    connection1.basicAck(ch,method)
                    return
            """
            Download the file and extract:
            """
            dest_file = BAAZ_DATA_ROOT + tenant + "/" + filename
            destination = os.path.dirname(dest_file)
            clog.debug("Destination: "+str(destination))
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

            shutil.copy(dest_file, logpath)
            resp_dict = get_impala_import.execute(tenant, {'file':dest_file, 'stats':msg_dict['stats']})
        elif msg_dict["opcode"] == "MongoTransform":

            clog.debug("Got the opcode For Mongo Translation")
            instances = msg_dict["job_instances"]
            resp_dict = process_mongo_rewrite_request(ch, properties, tenant, instances, clog)
        elif msg_dict['opcode'] == "TableTransformStats":
            #get list of patterns that are being transformed
            instances = msg_dict["job_instances"]
            resp_dict = table_transform_stats.execute(tenant, instances)
        elif msg_dict['opcode'] == "QueryTransformStats":
            #get list of patterns that are being transformed
            resp_dict = query_transform_stats.execute(tenant, msg_dict)
        elif msg_dict["opcode"] == "TableDetails":
            entity_id = msg_dict["entity_id"]
            resp_dict = table_details.execute(tenant, entity_id)
        elif msg_dict["opcode"] == "QueryDetails":
            entity_id = msg_dict["entity_id"]
            resp_dict = query_details.execute(tenant, entity_id)
        elif msg_dict["opcode"] == "UploadDetails":
            resp_dict = upload_details.execute(tenant)
        elif msg_dict["opcode"] == "ScaleModeInfo":
            smc = ScaleModeConnector(tenant)
            rc = RedisConnector(tenant)
            resp_dict = smc.generate_json()
            if "uid" in msg_dict:
                uid = msg_dict["uid"]
                resp_dict["totalQueries"] = rc.getScaleModeTotalQueryCount(uid)
                resp_dict["progress"] = rc.getProgress(uid)
        elif msg_dict['opcode'] == "TopDim":
            resp_dict = top_dim.execute(tenant)
        elif msg_dict['opcode'] == "TopTablesByPattern":
            resp_dict = top_tables_by_pattern.execute(tenant)
        elif msg_dict['opcode'] == "TopTables":
            resp_dict = top_tables.execute(tenant)
        elif msg_dict['opcode'] == "TailTables":
            resp_dict = tail_tables.execute(tenant)
        elif msg_dict['opcode'] == "ColumnByOperator":
            if 'operator' in msg_dict:
                resp_dict = columns_by_operator.execute(tenant, msg_dict['operator'])
        elif msg_dict['opcode'] == "TableStats":
            resp_dict = table_stats.execute(tenant)
        elif msg_dict['opcode'] == "ColumnStats":
            resp_dict = column_stats.execute(tenant)
        elif msg_dict['opcode'] == "SimpleQueries":
            resp_dict = simple_queries.execute(tenant)
        elif msg_dict['opcode'] == "WorkloadAssessment":
            resp_dict = workload_assessment.execute(tenant)
        elif msg_dict['opcode'] == "AccessPatterns":
            resp_dict = access_patterns.execute(tenant, msg_dict["accessPatternIds"])
        elif msg_dict['opcode'] == "MongoUrlForTenant":
            resp_dict = {'mongo_url': FPConnector.get_mongo_url(tenant)}
        elif msg_dict['opcode'] == "RedisMasterNameForTenant":
            resp_dict = {'redis_master_name': FPConnector.get_redis_master_name(tenant)}
        elif msg_dict['opcode'] == "GetRedisForTenant":
            resp_dict = {'redis_master_name': FPConnector.get_redis_master_name(tenant),
                         'redis_hosts': FPConnector.get_redis_hosts(tenant)}
        elif msg_dict['opcode'] == "ElasticNodesForTenant":
            resp_dict = {'elastic_nodes': FPConnector.get_elastic_nodes(tenant)}
        else:
            api_config= ConfigParser.RawConfigParser()
            api_config.read("/etc/xplain/application-api.cfg")

            section = msg_dict['opcode']
            if api_config.has_section(section):
                if not api_config.has_option(section, "Import") or\
                   not api_config.has_option(section, "Function"):
                    clog.error("API configuration section not defined properly")
                else:
                    mod = importlib.import_module(api_config.get(section, "Import"))
                    methodToCall = getattr(mod, api_config.get(section, "Function"))
                    resp_dict = methodToCall(tenant, msg_dict)
        #send stats to datadog
        if statsd:
            uid = None
            totalTime = (time.clock() - opcode_startTime)
            if "uid" in msg_dict:
                uid = msg_dict["uid"]
                statsd.timing("appservice."+msg_dict['opcode'], totalTime, tags=["tenant:"+tenant, "uid:"+uid])
            else:
                statsd.timing("appservice."+msg_dict['opcode'], totalTime, tags=["tenant:"+tenant])
    except:
        clog.exception("Proceesing request for " + msg_dict["opcode"])

    if resp_dict is None:
        resp_dict = {"status" : "Failed"}

    try:
        clog.debug("Responding to coorelation ID : "+ properties.correlation_id)
        ch.basic_publish(exchange='',
                         routing_key=properties.reply_to,
                         properties=pika.BasicProperties(correlation_id = \
                                                         properties.correlation_id),
                            body=dumps(resp_dict))
    except:
        clog.error("Unable to send response message")

    connection1.basicAck(ch,method)
    #send stats to datadog
    if statsd:
        totalTime = (time.clock() - startTime)
        statsd.timing("appservice.per.msg.time", totalTime, tags=["tenant:"+tenant])

connection1 = RabbitConnection(callback, ['appservicequeue'], [], {}, prefetch_count=1)


logging.info("ApplicationService going to start consuming")

try:
    connection1.run()
except:
    logging.exception("In Run :")

if usingAWS:
    boto_conn.close()
logging.info("Closing ApplicationService")
