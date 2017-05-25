# (c) Copyright 2016 Cloudera, Inc. All rights reserved.

"""
Template Python Service File for Navigator Optimizer.
"""
import json
import shutil
import os
import ConfigParser
import datetime
import time
import logging
import importlib
from rlog import RedisHandler
from flightpath.utils import *
from flightpath import cluster_config
from flightpath.services.RotatingS3FileHandler import *
from flightpath.services.RabbitMQConnectionManager import *

'''
TODO:
CHANGE SERVICE_NAME for your service.
'''
SERVICE_NAME = "navopt_templateservice"


SERVICE_QUEUE_NAME = SERVICE_NAME + "queue"
SERVICE_CFG_LOCATION = "/etc/xplain/%s.cfg" % (SERVICE_NAME)
APPSRV_LOG_FILE = "/var/log/cloudera/navopt/%s.err" % (SERVICE_NAME)
BAAZ_DATA_ROOT = "/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY = "processing"

config = ConfigParser.RawConfigParser()
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

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=APPSRV_LOG_FILE, level=logging_level, datefmt='%m/%d/%Y %I:%M:%S %p')
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


def callback(ch, method, properties, body):
    startTime = time.time()

    #send stats to datadog
    if statsd:
        statsd.increment(SERVICE_NAME + '.msg.count', 1)

    try:
        msg_dict = json.loads(body)
    except:
        logging.exception("Could not load the message JSON")
        return

    logging.debug(SERVICE_NAME + ": Got message : " + str(msg_dict))
    logging.debug("Correlation ID : " + properties.correlation_id)
    if "opcode" not in msg_dict or 'tenant' not in msg_dict:
        logging.error(SERVICE_NAME + ' there was no opcode or tenant in msg_dict.')
        connection1.basicAck(ch, method)
        return

    tenant = msg_dict["tenant"]
    msg_dict["connection"] = connection1
    msg_dict["ch"] = ch
    resp_dict = None

    log_dict = {'tenant': msg_dict['tenant'],
                'opcode': msg_dict['opcode'],
                'tag': SERVICE_NAME}

    if 'uid' in msg_dict:
        log_dict['uid'] = msg_dict['uid']
    clog = LoggerCustomAdapter(logging.getLogger(__name__), log_dict)
    try:
        """
         This needs to be dynamic in nature.
        """
        opcode_startTime = time.clock()
        api_config = ConfigParser.RawConfigParser()
        api_config.read(SERVICE_CFG_LOCATION)

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
                statsd.timing(SERVICE_NAME + "."+msg_dict['opcode'], totalTime, tags=["tenant:"+tenant, "uid:"+uid])
            else:
                statsd.timing(SERVICE_NAME + "."+msg_dict['opcode'], totalTime, tags=["tenant:"+tenant])
    except:
        clog.exception("Proceesing request for " + msg_dict["opcode"])

    if resp_dict is None:
        resp_dict = {"status": "Failed"}

    try:
        clog.debug("Responding to coorelation ID : " + properties.correlation_id)
        ch.basic_publish(exchange='',
                         routing_key=properties.reply_to,
                         properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                         body=json.dumps(resp_dict))
    except:
        clog.error("Unable to send response message")

    connection1.basicAck(ch, method)
    #send stats to datadog
    if statsd:
        totalTime = (time.clock() - startTime)
        statsd.timing(SERVICE_NAME + ".per.msg.time", totalTime, tags=["tenant:"+tenant])

connection1 = RabbitConnection(callback, [SERVICE_QUEUE_NAME], [], {}, prefetch_count=1)


logging.info(SERVICE_NAME + " going to start consuming")

try:
    connection1.run()
except:
    logging.exception("In Run :")

if usingAWS:
    boto_conn.close()
logging.info("Closing %s" % (SERVICE_NAME))
