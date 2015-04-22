#!/usr/bin/python

"""
Process request for simulation on Imapla.
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

APPSRV_LOG_FILE = "/var/log/ImpalaSimulation.err"

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
    if os.path.isfile(APPSRV_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(APPSRV_LOG_FILE, APPSRV_LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=APPSRV_LOG_FILE,level=logging.INFO,datefmt='%m/%d/%Y %I:%M:%S %p')

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    bucket = boto_conn.get_bucket('partner-logs') 
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(APPSRV_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))


def callback(ch, method, properties, body):

    starttime = time.time()
    
    try:
        msg_dict = loads(body)
    except:
        logging.exception("Could not load the message JSON")
        return

    logging.info("ApplicationService: Got message : "+ str(msg_dict))
    logging.info("Correlation ID : "+ properties.correlation_id)
    if "opcode" not in msg_dict or 'tenant' not in msg_dict:
        logging.info('ApplicationService there was no opcode or tenant in msg_dict.')
        connection1.basicAck(ch,method)
        return

    tenant = msg_dict["tenant"]
    msg_dict["connection"] = connection1
    msg_dict["ch"] = ch
    mongo_url = getMongoServer(tenant)
    resp_dict = None

    try:
        api_config= ConfigParser.RawConfigParser()
        api_config.read("/etc/xplain/ImpalaSimulation.cfg")

        section = msg_dict['opcode']
        if api_config.has_section(section):
            if not api_config.has_option(section, "Import") or\
               not api_config.has_option(section, "Function"):
                logging.error("API configuration section not defined properly")
            else:
                mod = importlib.import_module(api_config.get(section, "Import"))
                methodToCall = getattr(mod, api_config.get(section, "Function"))
                resp_dict = methodToCall(tenant, msg_dict)
    except:
        logging.exception("Proceesing request for " + msg_dict["opcode"])

    if resp_dict is None:
        resp_dict = {"status" : "Failed"}

    try:
        logging.info("Responding to coorelation ID : "+ properties.correlation_id)
        ch.basic_publish(exchange='',
                         routing_key=properties.reply_to,
                         properties=pika.BasicProperties(correlation_id = \
                                                         properties.correlation_id),
                            body=dumps(resp_dict))
    except:
        logging.error("Unable to send response message")

    connection1.basicAck(ch,method)

connection1 = RabbitConnection(callback, ['impalasimulation'], [], {}, APPSRV_LOG_FILE)


logging.info("ImpalaSimulation going to start consuming")

try:
    connection1.run()
except:
    logging.exception("In Run :")

if usingAWS:
    boto_conn.close()
logging.info("Closing ApplicationService")
