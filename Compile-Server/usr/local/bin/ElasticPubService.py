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
from flightpath.FPConnector import *
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
import elasticsearch

LOG_FILE = "/var/log/ElasticPubService.err"

config = ConfigParser.RawConfigParser()
config.read("/var/Baaz/hosts.cfg")
usingAWS = config.getboolean("mode", "usingAWS")
if usingAWS:
    from boto.s3.key import Key
    import boto

mode = cluster_config.get_cluster_mode()
logging_level = logging.INFO
if mode == "development":
    logging_level = logging.INFO

rabbitserverIP = config.get("RabbitMQ", "server")
metrics_url = None

"""
For VM there is not S3 connectivity. Save the logs with a timestamp.
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(LOG_FILE, LOG_FILE+timestr)
    #db silo list
    dbsilo_list = ['Silo1']
else:
    dbsilo_list = ['dbsilo1', 'dbsilo2']

def setup_es_conn():
    #find all dbsilo's specific elastic host
    prefix = 'dbsilo:'
    es_hosts_silo = {}
    es_conn_silo = {}
    for dbsilo in dbsilo_list:
        key = prefix + dbsilo + ":info"
        info = r.hgetall(key)
        es_hosts_silo[dbsilo] = info['elastic'].split(',')

    for key in es_hosts_silo:    
        #setup connection to ES host
        es_conn_silo[key] = elasticsearch.Elasticsearch(hosts=[{'host': es_host, 'port': 9200} for es_host in es_hosts_silo[key]])
    return es_conn_silo

es_conn_silo = setup_es_conn()

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
        msg_dict = loads(body)
    except:
        logging.exception("Could not load the message JSON")
        return

    logging.info("ElasticPubService: Got message : " + str(msg_dict))
    if "opcode" not in msg_dict or 'tenant' not in msg_dict:
        logging.info('ElasticPub there was no opcode or tenant in msg_dict.')
        connection1.basicAck(ch, method)
        return

    tenant = msg_dict["tenant"]
    log_dict = {'tenant':msg_dict['tenant'], 'opcode':msg_dict['opcode'], 'tag': 'elasticpub'}
    if 'uid' in msg_dict:
        log_dict['uid'] = msg_dict['uid']
    clog = LoggerCustomAdapter(logging.getLogger(__name__), log_dict)

    #check if index needs to be update in ES
    if 'update' in msg_dict:
        #get silo for tenant
        dbsilo = get_silo(tenant)
        es_conn_silo[dbsilo].update(index=msg_dict['tenant'], id=msg_dict['eid'], doc_type="entity",
                                    body={"doc": msg_dict['update_dict']})
        connection1.basicAck(ch, method)
        return

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

    es_cfg = {}

    if mongoconn.es is not None:
        es_cfg['eid'] = msg_dict['eid']
        es_cfg['name'] = msg_dict['name']
        es_cfg['etype'] = msg_dict['etype']
        mongoconn._cleanup_es_dict(es_cfg)
        try:
            #get silo for tenant
            dbsilo = get_silo(tenant)
            es_conn_silo[dbsilo].create(index=tenant, id=msg_dict['eid'], doc_type="entity", body=es_cfg)
        except elasticsearch.TransportError, e:
            logging.error("Could not connect to ElasticSearch %s", e.args)
            
    if resp_dict is None:
        resp_dict = {"status": "Failed"}

    mongoconn.close()
    connection1.basicAck(ch, method)

connection1 = RabbitConnection(callback, ['elasticpub'], [], {}, prefetch_count=50)
logging.info("ElasticPub going to start consuming")

try:
    connection1.run()
except:
    logging.exception("In run of ElasticPub:")

if usingAWS:
    boto_conn.close()
logging.info("Closing ElasticPub.")
