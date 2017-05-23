#!/usr/bin/python

"""
Rule Engine Service
"""
from flightpath.services.RabbitMQConnectionManager import RabbitConnection
from flightpath.services.RotatingS3FileHandler import RotatingS3FileHandler
from flightpath.utils import LoggerCustomAdapter
from flightpath.Provenance import getMongoServer
from flightpath.MongoConnector import MongoConnector, Connector
from flightpath.RedisConnector import RedisConnector
from flightpath import cluster_config
from flightpath import risk_alerts
from rlog import RedisHandler
import json
import os
import ConfigParser
import shutil
import datetime
import time
import logging

"""
Will have the following functions:

1) Inititate a new calculation for a new version of the rules.
   If rules have already been calculated, do nothing. If rules have been
   partially calculated (crash/restart), then recalculate only for missing queries (if override flag is not set).
   Calculation means sending messages to its own queue. 
   If a new calculation, all query eids that are missing the calculation will be added
   to a redis set. There should be a redis set per rule version that is under calculation. The existence of the set indicates that a calculation is ongoing

2) Calculate rule results for a particular query eid and rule version. Remove the query eid
   from the set once the calculation has finished. Persist the results into mongo.

app_get_design_bucket & app_get_slice_by_* will both call functions in risk_alerts to get the risk alerts.
If version is behind latest (in config), then this risk_alerts function will send messages to rulenegineservice. Else, do nothing. risk_alerts should handle all the different version types.
Exception if version is too old.

Phase 2 can do the same as above to initiate calculation.


Failure conditions:

1) RuleEngineService crashes during rule calculation intitiation.
   -> RabbitMQ redelivers message, service can resume where it left off by looking at redis set
2) RuleEngineService crashes during rule calculation results
   -> RabbitMQ redelivers message. Unique index of eid + version in mongo ensures no duplicate documents. Removal from a redis set is an idempotent operation

How to determine latest version completed?
Key in redis to track latest version fully calculated. 
Updated on srem = false (key no longer exists because set has been exhausted).

Create new collection, rule_workflows_v2 for version 8+.

For app calls where latest has not been calculated:

Fall back to old rule_workflows (read-only flow).
Distinct query to determine max version in collection.
If max version > 4:
That version results get returned, with flag 'updating results'
Assume that old rule version calculations are not in progress:
Make sure ruleenginequeue is idle before deploy.
If max version <= 4 or no rule versions exist:
Return nothing, with flag 'calculating results'

For app calls where nothing has been calculated:

"""

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

"""
For VM there is not S3 connectivity. Save the logs with a timestamp.
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(LOG_FILE, LOG_FILE+timestr)
    # no datadog statsd on VM
    statsd = None

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    filename=LOG_FILE,
                    level=logging_level,
                    datefmt='%m/%d/%Y %I:%M:%S %p')

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

        
def initiate_rule_calculation(tenantid, rconn, source_platform, connection, ch, override=False, uid="0"):

    if not connection or not ch:
        return

    if not override and rconn.numMessagesPending(uid, message_type='rule_workflows') > 0:
        # Rule engine has already initiated the calculation, so do nothing
        return

    q_counts = rconn.getTopEtypeCounts("SQL_QUERY", 'instance_count', 0, -1)
    all_query_eids = [x[0] for x in q_counts]
    
    for eid in all_query_eids:
        msg_dict = {
            'opcode': 'process',
            'tenant': tenantid,
            'source_platform': source_platform,
            'uid': uid,
            'eid': eid,
        }
        rconn.addMessagePending(uid, eid, message_type='rule_workflows')
        connection.publish(ch, '', 'ruleengine', json.dumps(msg_dict))

        
def process_rules_for_query(tenantid, uid, rconn, source_platform, mclient, mconn, query_eid):

    db = mclient[tenantid]
    
    for target_platform in ('hive', 'impala'):
        alert_results = []
        query_risk = risk_alerts.LOW

        for alert in risk_alerts.get_all_query_alerts():
            alert_execution_params = {
                'entityid': query_eid,
                'source_platform': source_platform,
                'target_platform': target_platform,
                'client': mclient,
                'mongoconn': mconn,
                'redis_conn': rconn,
            }
            
            # True if alert is raised
            alert_result = alert.execute_alert_for_query(tenantid, alert_execution_params)
            alert_results.append({"alert_name": alert.workflow_name, "alert_result": alert_result})
            
            # Upgrade query risk level if needed
            if query_risk == risk_alerts.LOW and alert.level == risk_alerts.MEDIUM:
                query_risk = risk_alerts.MEDIUM
            if query_risk == risk_alerts.MEDIUM and alert.level == risk_alerts.HIGH:
                query_risk = risk_alerts.HIGH
                
        # Persist results into alerts collection
        db.alerts.update({"eid": query_eid, "target_platform": target_platform, "version": risk_alerts.VERSION},
                         {"$set": {"risk": query_risk, "alerts": alert_results}}, upsert=True)

    rconn.delMessagePending(uid, query_eid, message_type='rule_workflows')


def callback(ch, method, properties, body):

    # Collect stats for datadog if enabled
    if statsd:
        start_time = time.clock()
        statsd.increment('ruleengine.msg.count', 1)

    try:
        msg_dict = json.loads(body)
    except:
        logging.exception("Could not load the message JSON")
        connection1.basicAck(ch, method)
        return

    logging.info("Got message : " + str(msg_dict))
    
    try:
        tenantid = msg_dict["tenant"]
        opcode = msg_dict["opcode"]
        source_platform = msg_dict["source_platform"]
    except KeyError:
        logging.exception("Missing parameter in message")
        connection1.basicAck(ch, method)
        return

    uid = msg_dict.get('uid', None)

    clog = LoggerCustomAdapter(logging.getLogger(__name__), {
        'tenant': tenantid,
        'opcode': opcode,
        'tag': 'ruleengine',
        'uid': msg_dict['uid'] if 'uid' in msg_dict else None
    })

    mclient = getMongoServer(tenantid)
    mongoconn = Connector.getConnector(tenantid)
    if mongoconn is None:
        mongoconn = MongoConnector({'client': mclient, 'context': tenantid,
                                    'create_db_if_not_exist': False})
    rconn = RedisConnector(tenantid)

    if opcode == 'initiate':
        initiate_rule_calculation(tenantid, uid, rconn, source_platform, connection1, ch, override=msg_dict.get('override', False))
    elif opcode == 'process':
        process_rules_for_query(tenantid, uid, rconn, source_platform, mclient, mongoconn, msg_dict['eid'])
    else:
        clog.error("Invalid opcode passed to RuleEngineService")

    mongoconn.close()
    connection1.basicAck(ch, method)

    # Send stats to datadog
    if statsd:
        total_time = (time.clock() - start_time)
        statsd.timing("ruleengine.per.msg.time", total_time, tags=["tenant:"+tenant])

connection1 = RabbitConnection(callback, ['ruleengine'], ['ruleengine'], {}, prefetch_count=1)

logging.info("RuleEngine going to start consuming")

try:
    connection1.run()
except:
    logging.exception("RuleEngine crashed: ")

if usingAWS:
    boto_conn.close()
    
logging.info("Closing RuleEngineService.")

