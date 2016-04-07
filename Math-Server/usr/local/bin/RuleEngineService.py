#!/usr/bin/python

"""
Process request for simulation on Imapla.
"""
#from flightpath.parsing.hadoop.HadoopConnector import *
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.RotatingS3FileHandler import *
import flightpath.utils as utils
from flightpath.Provenance import getMongoServer
import sys
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from flightpath import FPConnector
from json import *
import shutil
import os
import ConfigParser
import datetime
import time
import logging
import socket
import importlib

LOG_FILE = "/var/log/RuleEngineService.err"

config = ConfigParser.RawConfigParser()
config.read("/var/Baaz/hosts.cfg")
usingAWS = config.getboolean("mode", "usingAWS")
if usingAWS:
    from boto.s3.key import Key
    import boto

rabbitserverIP = config.get("RabbitMQ", "server")
metrics_url = None

workflow_config = ConfigParser.RawConfigParser()
workflow_config.read("/etc/xplain/rule_workflows.cfg")

rule_config = ConfigParser.RawConfigParser()
rule_config.read("/etc/xplain/rules.cfg")

"""
For VM there is not S3 connectivity. Save the logs with a timestamp.
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(LOG_FILE, LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    filename=LOG_FILE,
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    bucket = boto_conn.get_bucket('partner-logs')
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))


def callback(ch, method, properties, body):
    '''
    Callback method for the RuleEngineService.
    Attempts to run the workflow in rule_workflows.cfg specified by the opcode.
    Imports and runs the rules that are needed which are put in rules.cfg.
    '''
    try:
        msg_dict = loads(body)
    except:
        logging.exception("Could not load the message JSON")
        return

    logging.info("RuleEngineService: Got message : " + str(msg_dict))
    if "opcode" not in msg_dict or 'tenant' not in msg_dict:
        logging.info('RuleEngineService there was no opcode or tenant in msg_dict.')
        connection1.basicAck(ch, method)
        return

    tenant = msg_dict["tenant"]
    msg_dict["connection"] = connection1
    msg_dict["ch"] = ch
    resp_dict = None

    '''
    Runs prerequisite rules for given workflow.
    Run workflows that has the given opcode.
    '''
    section = msg_dict['opcode']
    if workflow_config.has_section(section):
        if not workflow_config.has_option(section, "Import") or\
          not workflow_config.has_option(section, "Function") or\
          not workflow_config.has_option(section, "RuleIds") or \
          not workflow_config.has_option(section, "version"):
            logging.error("rule_workflows.cfg section not defined properly for %s"%(section))
        else:
            '''
            Run rules before running the workflow.
            '''
            rule_ids = workflow_config.get(section, "RuleIds").split(',')
            for rule_id in rule_ids:
                rule_name = rule_config.get(rule_id, "RuleName")
                rule_mod = importlib.import_module(rule_config.get(rule_id, "Import"))
                rule_function = getattr(rule_mod, rule_config.get(rule_id, "Function"))
                try:
                    msg_dict[rule_name] = rule_function(tenant, msg_dict)
                except:
                    msg_dict[rule_name] = None
                    logging.exception("Rule Failed for " + rule_name)
            mod = importlib.import_module(workflow_config.get(section, "Import"))
            methodToCall = getattr(mod, workflow_config.get(section, "Function"))
            msg_dict['version'] = workflow_config.get(section, "version")
            try:
                resp_dict = methodToCall(tenant, msg_dict)
            except:
                logging.exception("Proceesing request for " + msg_dict["opcode"])

    if resp_dict is None:
        resp_dict = {"status": "Failed"}

    '''
    try:
        logging.info("Responding to coorelation ID : " + properties.correlation_id)
        ch.basic_publish(exchange='',
                         routing_key=properties.reply_to,
                         properties=pika.BasicProperties(correlation_id=\
                                                         properties.correlation_id),
                         body=dumps(resp_dict))
    except:
        logging.error("Unable to send response message")
    '''

    connection1.basicAck(ch, method)

connection1 = RabbitConnection(callback, ['ruleengine'], [], {}, prefetch_count=1)

logging.info("RuleEngine going to start consuming")

try:
    connection1.run()
except:
    logging.exception("In run of RuleEngine:")

if usingAWS:
    boto_conn.close()
logging.info("Closing RuleEngineService.")
