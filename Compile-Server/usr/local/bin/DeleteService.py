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

DELSRV_LOG_FILE = "/var/log/cloudera/navopt/deleteservice.err"

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
    if os.path.isfile(DELSRV_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(DELSRV_LOG_FILE, DELSRV_LOG_FILE+timestr)
    #no datadog statsd on VM
    statsd = None

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=DELSRV_LOG_FILE,level=logging_level,datefmt='%m/%d/%Y %I:%M:%S %p')
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
    logging.getLogger().addHandler(RotatingS3FileHandler(DELSRV_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))
    redis_host = config.get("RedisLog", "server")
    if redis_host:
        logging.getLogger().addHandler(RedisHandler('logstash', level=logging_level, host=redis_host, port=6379))

def callback(ch, method, properties, body):

    starttime = time.time()

    try:
        msg_dict = loads(body)
    except:
        logging.exception("Could not load the message JSON")
        return

    logging.info("DeleteService: Got message : "+ str(msg_dict))
    if "opcode" not in msg_dict or ('tenant' not in msg_dict and 'email' not in msg_dict):
        logging.error('DeleteService there was no opcode or tenant in msg_dict.')
        connection1.basicAck(ch,method)
        return

    tenant = None
    if "tenant" in msg_dict:
        tenant = msg_dict["tenant"]
    email = None
    if "eid" in msg_dict:
        eid = msg_dict["eid"]
    msg_dict["connection"] = connection1
    msg_dict["ch"] = ch
    client = getMongoServer(tenant)
    resp_dict = None

    log_dict = {'tenant':tenant, 'opcode':msg_dict['opcode'], 'tag':'deleteservice'}
    if 'uid' in msg_dict:
        log_dict['uid'] = msg_dict['uid']
    clog = LoggerCustomAdapter(logging.getLogger(__name__), log_dict)
    try:
        """
         This needs to be dynamic in nature.
        """
        opcode_startTime = time.time()
        delete_config= ConfigParser.RawConfigParser()
        delete_config.read("/etc/xplain/deleteservice.cfg")

        section = msg_dict['opcode']
        if delete_config.has_section(section):
            if not delete_config.has_option(section, "Import") or\
               not delete_config.has_option(section, "Function"):
                clog.error("Delete service configuration section not defined properly")
            else:
                mod = importlib.import_module(delete_config.get(section, "Import"))
                methodToCall = getattr(mod, delete_config.get(section, "Function"))
                logging.info("DeleteService: calling opcode : "+ str(section))
                if tenant:
                    resp_dict = methodToCall(tenant, msg_dict)
                elif email:
                    resp_dict = methodToCall(email, msg_dict)
        #send stats to datadog
        if statsd:
            uid = None
            totalTime = ((time.time() - opcode_startTime) * 1000)
            if "uid" in msg_dict:
                uid = msg_dict["uid"]
                statsd.timing("deleteservice."+msg_dict['opcode'], totalTime, tags=["tenant:"+tenant, "uid:"+uid])
            else:
                statsd.timing("deleteservice."+msg_dict['opcode'], totalTime, tags=["tenant:"+tenant])
    except:
        clog.exception("Proceesing request for " + msg_dict["opcode"])

    if resp_dict is None:
        resp_dict = {"status" : "Failed"}

    try:
        ch.basic_publish(exchange='',
                         routing_key=properties.reply_to,
                         properties=pika.BasicProperties(correlation_id = \
                                                         properties.correlation_id),
                            body=dumps(resp_dict))
    except:
        clog.error("Unable to send response message")

    connection1.basicAck(ch,method)

connection1 = RabbitConnection(callback, ['deleteservicequeue'], [], {}, prefetch_count=1)


logging.info("DeleteService going to start consuming")

try:
    connection1.run()
except:
    logging.exception("In Run :")

if usingAWS:
    boto_conn.close()
logging.info("Closing DeleteService")
