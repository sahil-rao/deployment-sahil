#!/usr/bin/python

"""
Process request for simulation on Imapla.
"""
#from flightpath.parsing.hadoop.HadoopConnector import *
from flightpath import cluster_config
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.RotatingS3FileHandler import *
from flightpath.utils import *
from flightpath.Provenance import getMongoServer
import sys
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from flightpath import FPConnector
from rlog import RedisHandler

from json import *
import shutil
import os
import ConfigParser
import datetime
import time
import logging
import socket
import importlib

LOG_FILE = "/var/log/cloudera/navopt/RuleEngineService.err"

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
                    level=logging_level,
                    datefmt='%m/%d/%Y %I:%M:%S %p')
es_logger = logging.getLogger('elasticsearch')
es_logger.propagate = False
es_logger.setLevel(logging.WARN)

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    bucket = boto_conn.get_bucket('partner-logs')
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))
    redis_host = config.get("RedisLog", "server")
    if redis_host:
        logging.getLogger().addHandler(RedisHandler('logstash', level=logging_level, host=redis_host, port=6379))

def callback(ch, method, properties, body):
    '''
    Callback method for the RuleEngineService.
    Attempts to run the workflow in rule_workflows.cfg specified by the opcode.
    Imports and runs the rules that are needed which are put in rules.cfg.
    '''
    try:
        startTime = time.time()
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
    log_dict = {'tenant':msg_dict['tenant'], 'opcode':msg_dict['opcode'], 'tag': 'ruleengine'}
    if 'uid' in msg_dict:
        log_dict['uid'] = msg_dict['uid']
    clog = LoggerCustomAdapter(logging.getLogger(__name__), log_dict)

    msg_dict["connection"] = connection1
    msg_dict["ch"] = ch
    resp_dict = None
    client = getMongoServer(tenant)
    mongoconn = Connector.getConnector(tenant)
    if mongoconn is None:
        mongoconn = MongoConnector({'client': client, 'context': tenant,
                                    'create_db_if_not_exist': False})
    msg_dict['client'] = client
    msg_dict['mongoconn'] = mongoconn
    target_platform = None
    if 'target_platform' in msg_dict:
        target_platform = target_platform

    '''
    Checks if Import, Function, RuleIds, and version are present.
    Checks to see if workflow hass been run before.
    Runs prerequisite rules for given workflow.
    '''
    section = msg_dict['opcode']
    if workflow_config.has_section(section):
        if not workflow_config.has_option(section, "Import") or\
          not workflow_config.has_option(section, "Function") or\
          not workflow_config.has_option(section, "RuleIds") or \
          not workflow_config.has_option(section, "version"):
            clog.error("rule_workflows.cfg section not defined properly for %s"%(section))
        else:
            '''
            Run rules before running the workflow.
            '''
            msg_dict['version'] = workflow_config.get(section, "version")
            rule_ids = workflow_config.get(section, "RuleIds").split(',')
            mod = importlib.import_module(workflow_config.get(section, "Import"))
            has_run = False
            if workflow_config.has_option(section, "VerifyFunction"):
                methodToCall = getattr(mod, workflow_config.get(section, "VerifyFunction"))
                try:
                    has_run = methodToCall(tenant, msg_dict)
                except:
                    clog.exception("VerifyFunction for " + msg_dict["opcode"])

            if not has_run:
                for rule_id in rule_ids:
                    rule_name = rule_config.get(rule_id, "RuleName")
                    rule_mod = importlib.import_module(rule_config.get(rule_id, "Import"))
                    rule_function = getattr(rule_mod, rule_config.get(rule_id, "Function"))
                    try:
                        msg_dict[rule_name] = rule_function(tenant, msg_dict)
                    except:
                        msg_dict[rule_name] = None
                        clog.exception("Rule Failed for " + rule_name)

                methodToCall = getattr(mod, workflow_config.get(section, "Function"))
                try:
                    resp_dict = methodToCall(tenant, msg_dict)
                except:
                    clog.exception("Proceesing request for " + msg_dict["opcode"])

    if resp_dict is None:
        resp_dict = {"status": "Failed"}

    mongoconn.close()
    connection1.basicAck(ch, method)
    #send stats to datadog
    if statsd:
        totalTime = ((time.time() - startTime) * 1000)
        statsd.timing("ruleengine.per.msg.time", totalTime, tags=["tenant:"+tenant, "uid:"+uid])

connection1 = RabbitConnection(callback, ['ruleengine'], [], {}, prefetch_count=1)

logging.info("RuleEngine going to start consuming")

try:
    connection1.run()
except:
    logging.exception("In run of RuleEngine:")

if usingAWS:
    boto_conn.close()
logging.info("Closing RuleEngineService.")
