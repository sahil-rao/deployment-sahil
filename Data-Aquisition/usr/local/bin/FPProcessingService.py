#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenant> <log Directory>
"""
from flightpath import cluster_config
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.RotatingS3FileHandler import *
from flightpath.utils import *
from flightpath.parsing.ParseDemux import *
from flightpath.Provenance import getMongoServer
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *

from json import *
import elasticsearch
import shutil
import os
import sys
import tarfile
import ConfigParser
import datetime
import time
import logging
import socket
import urllib
import re
from rlog import RedisHandler

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"
BAAZ_FP_LOG_FILE = "/var/log/cloudera/navopt/FPProcessing.err"

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
usingAWS = config.getboolean("mode", "usingAWS")

bucket_location = "partner-logs"
log_bucket_location = "xplain-servicelogs"

CLUSTER_MODE = config.get("ApplicationConfig", "mode")
CLUSTER_NAME = config.get("ApplicationConfig", "clusterName")

if CLUSTER_MODE is None:
    CLUSTER_MODE = 'production'


if CLUSTER_NAME is not None:
    bucket_location = CLUSTER_NAME

DEFAULT_QUERY_LIMIT = 50000

if usingAWS:
    from boto.s3.key import Key
    import boto
    from datadog import initialize, statsd

rabbitserverIP = config.get("RabbitMQ", "server")
metrics_url = None

mode = cluster_config.get_cluster_mode()
logging_level = logging.INFO
if mode == "development":
    logging_level = logging.INFO

"""
For VM there is not S3 connectivity. Save the logs with a timestamp.
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(BAAZ_FP_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(BAAZ_FP_LOG_FILE, BAAZ_FP_LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=BAAZ_FP_LOG_FILE,level=logging_level,datefmt='%m/%d/%Y %I:%M:%S %p')
es_logger = logging.getLogger('elasticsearch')
es_logger.propagate = False
es_logger.setLevel(logging.WARN)


"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    bucket = boto_conn.get_bucket(bucket_location)
    log_bucket = boto_conn.get_bucket(log_bucket_location)
    logging.getLogger().addHandler(RotatingS3FileHandler(BAAZ_FP_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))
    redis_host = config.get("RedisLog", "server")
    if redis_host:
        logging.getLogger().addHandler(RedisHandler('logstash', level=logging_level, host=redis_host, port=6379))
    initialize(statsd_host='localhost', statsd_port=8125)

def generateTagArray(header_info):
    tagArray = []
    for header in header_info:
        if('tag' in header and header['tag'] is True):
            tagArray.append(header['type'].upper())
    return tagArray

def generateCountArray(header_info):
    countArray = []
    for header in header_info:
        if('count' in header and header['count'] is True):
            countArray.append(header['type'].upper())
    return countArray


def clean_header(header_info):
    if not header_info:
        return header_info
    for i, tag_info in enumerate(header_info):
        header_info[i]['type'] = "".join(re.findall("[a-zA-Z-_]+", tag_info['type'].upper()))
    return header_info

def end_of_phase_callback(params, current_phase):
    if current_phase > 1:
        logging.error("Attempted end of phase callback, but current phase > 1")
        return

    logging.debug("Changing processing Phase")
    msg_dict = {'tenant':params['tenant'], 'opcode':"PhaseTwoAnalysis"}
    msg_dict['uid'] = params['uid']
    message = dumps(msg_dict)
    params['connection'].publish(params['channel'],'',params['queuename'],message)
    return

def performTenantCleanup(tenant, clog):
    clog.info("Cleaning Tenant "+ tenant)
    destination = BAAZ_DATA_ROOT + tenant
    if os.path.exists(destination):
        shutil.rmtree(destination)
    destination = '/mnt/volume1/compile-' + tenant
    if os.path.exists(destination):
        shutil.rmtree(destination)

def updateRelationCounter(redis_conn, eid):

    relationshipTypes = ['QUERY_SELECT', 'QUERY_JOIN', 'QUERY_FILTER', "READ", "WRITE", "COOCCURRENCE_TABLE",
                         'QUERY_GROUPBY', 'QUERY_ORDERBY', "COOCCURRENCE_GROUP", "COOCCURRENCE_QUERY"]

    relations_to = redis_conn.getRelationships(eid, None, None)
    for rel in relations_to:
        if rel['rtype'] in relationshipTypes:
            redis_conn.incrRelationshipCounter(eid, rel['end_en'], rel['rtype'], "instance_count", incrBy=1)

    relations_from = redis_conn.getRelationships(None, eid, None)
    for rel in relations_from:
        if rel['rtype'] in relationshipTypes:
            redis_conn.incrRelationshipCounter(rel['start_en'], eid, rel['rtype'], "instance_count", incrBy=1)

def elasticConnect(tenantID, clog):

    elastichosts = getElasticServer(tenantID)
    if not elastichosts:
        return

    es = elasticsearch.Elasticsearch(hosts=[{'host' : es_host, 'port' : 9200} for es_host in elastichosts])
    if es is None:
        return
    try:
        if not es.indices.exists(index=tenantID):
            mapping = { "entity" : {
                            "properties" : {
                                "name":{
                                    "type":"completion",
                                    "context" : {
                                        "etype" : {
                                            "type" : "category",
                                            "default" : ["SQL_QUERY","SQL_TABLE"],
                                            "path" : "etype"
                                        }
                                    },
                                    "fields" : {
                                        "untouched" : { "type":"string", "index":"not_analyzed" }
                                    }
                                },
                            "eid" : { "type" : "completion" }
                        }
                    }
                }

            settings = { "index" : {
                            "number_of_shards" : 3,
                            "number_of_replicas": 0
                            }
                        }
            es.indices.create(index=tenantID, body=settings, ignore=[400,409])
            es.indices.put_mapping(index=tenantID, doc_type='entity', body=mapping, ignore=[400,409])
    except:
        clog.exception("Elastic Search : ")

class callback_context():

    class QueryLimitReachedException(Exception):
        pass

    def __init__(Self, tenant, uid, ch, mongoconn, redis_conn, collection, scale_mode=False, skipLimit=False, testMode=False, sourcePlatform=None, header_info = None, delimiter = None):
        Self.tenant = tenant
        Self.uid = uid
        Self.ch = ch
        Self.mongoconn = mongoconn
        Self.redis_conn = redis_conn
        Self.collection = collection
        Self.CLUSTER_MODE = CLUSTER_MODE
        Self.uploadLimit = Self.__getUploadLimit()
        Self.skipLimit = skipLimit
        Self.sourcePlatform = sourcePlatform
        Self.scale_mode = scale_mode
        Self.testMode = testMode
        Self.queryNumThreshold = 50000
        Self.header_info = clean_header(header_info)
        Self.delimiter = delimiter
        Self.col_stat_table_name_list = []
        Self.table_stat_table_name_list = []
        Self.compiler_to_use = get_compiler(Self.sourcePlatform)
        Self.clog = LoggerCustomAdapter(logging.getLogger(__name__), {'tag': 'dataacquisitionservice', 'tenant': tenant, 'uid':uid})

    def get_source_platform(Self):
        return Self.sourcePlatform

    def get_header_info(Self):
        return Self.header_info

    def get_delimiter_info(Self):
        return Self.delimiter

    def query_count(Self, total_queries_found):
        """
        Report total number of queries found.

        Store the total count in the upload stats.
        """
        Self.clog.info("Total Queries found " + str(total_queries_found))
        overall_stats = Self.collection.find_one({'uid':'0'})
        queries_left = total_queries_found
        if 'query_processed' in overall_stats and Self.uploadLimit !=0 and not Self.skipLimit:
            queries_left = int(Self.uploadLimit) - int( overall_stats['query_processed'])

        Self.redis_conn.setScaleModeTotalQueryCount( min(queries_left, int(total_queries_found)), Self.uid )
        Self.redis_conn.setEntityProfile(Self.uid, {"total_queries": min(queries_left, total_queries_found), "processed_queries":0})
        if total_queries_found > Self.queryNumThreshold and Self.__getScaleMode():
            Self.scale_mode = True

    def __getUploadLimit(Self):
        userdb = getMongoServer("xplainIO")["xplainIO"]
        org = userdb.organizations.find_one({"guid":Self.tenant}, {"upLimit":1})

        if "upLimit" not in org:
            upLimit = DEFAULT_QUERY_LIMIT
            userdb.organizations.update({"guid":Self.tenant}, {"$set": {"upLimit":upLimit}})
        else:
            upLimit = org["upLimit"]

        return upLimit

    def __getScaleMode(Self):
        #if Self.CLUSTER_MODE == "development":
        #    return True

        userdb = getMongoServer("xplainIO")["xplainIO"]
        org = userdb.organizations.find_one({"guid":Self.tenant}, {"scaleMode":1})

        if "scaleMode" in org:
            return org["scaleMode"]

        return False

    def __checkQueryLimit(Self):
        upStats = Self.collection.find_one({'uid':"0"})
        if upStats is None:
            return True

        if "query_processed" not in upStats:
            Self.collection.update({'uid':"0"},{'$set':{"query_processed":0}})
            return True

        if Self.uploadLimit == 0:
            return True

        if int(upStats["query_processed"]) >= int(Self.uploadLimit):
            Self.collection.update({'uid':"0"},{'$set':{"limit_reached":"True"}})
            return False

        return True

    def __incrementProcessedQueryCount(Self):
        Self.collection.update({'uid':"0"},{'$inc':{"query_processed": 1}})

    def query_stats_callback(Self, query_stats):
        if Self.mongoconn.db.entities.find({"custom_id": query_stats['custom_id']}):
            #check if this are table or column stats
            Self.mongoconn.db.entities.update({"custom_id": query_stats['custom_id']},{'$set':{'profile.stats': query_stats}})

    def stats_callback(Self, stats):
        #mark upload stats with stats file
        Self.redis_conn.setEntityProfile(Self.uid, { "StatsFileProcessed":1})
        #check if this are table or column stats
        if 'column_name' in stats:
            column_entry = {}
            table_name = stats['table_name'].lower()
            column_name = stats['column_name'].lower()
            table_entity = Self.mongoconn.getEntityByName(table_name)
            if table_entity is None:
                #this means table doesnt not exsist create it
                eid = IdentityService.getNewIdentity(Self.tenant, True)
                table_entry = {"uid" : Self.uid}
                table_entity = Self.mongoconn.addEn(eid, table_name, Self.tenant,\
                                EntityType.SQL_TABLE, table_entry, None)
                #create Elastic search index
                sendToElastic(connection1, Self.redis_conn, Self.tenant, Self.uid,
                              table_entity, table_name, EntityType.SQL_TABLE)
                Self.redis_conn.createEntityProfile(table_entity.eid, "SQL_TABLE")
                Self.redis_conn.incrEntityCounterWithSecKey(table_entity.eid,
                                                            "instance_count",
                                                            sec_key=table_entity.name,
                                                            sort=True, incrBy=0)
                #updated the upload stats for table
                Self.redis_conn.incrEntityCounter(Self.uid, "Compiler.%s.newTables"%(Self.compiler_to_use), incrBy=1)
            else:
                if table_name not in Self.col_stat_table_name_list:
                    #updated the upload stats for table
                    Self.redis_conn.incrEntityCounter(Self.uid, "Compiler.%s.totalTables"%(Self.compiler_to_use), incrBy=1)
                    Self.col_stat_table_name_list.append(table_name)

            #check if column is already present or not
            column_entity_name = table_name + "." + column_name
            column_entity = Self.mongoconn.getEntityByName(column_entity_name)

            if column_entity is None:
                eid = IdentityService.getNewIdentity(Self.tenant, True)
                column_entry['tableEid'] = table_entity.eid
                column_entry["uid"] = Self.uid
                column_entry["stats"] = stats
                column_entry['columnName'] = column_name
                column_entry['tableName'] = table_name
                column_entity = Self.mongoconn.addEn(eid, column_entity_name, Self.tenant,\
                                                EntityType.SQL_TABLE_COLUMN, column_entry, None)
                #create Elastic search index
                sendToElastic(connection1, Self.redis_conn, Self.tenant, Self.uid,
                              column_entity, column_entity_name, EntityType.SQL_TABLE_COLUMN)
                #updated the upload stats for column
                Self.redis_conn.incrEntityCounter(Self.uid, "Compiler.%s.newColumns"%(Self.compiler_to_use), incrBy=1)
                '''
                Table --> Column relationship.
                '''
                if column_entity.eid == eid:
                    Self.redis_conn.createEntityProfile(column_entity.eid, "SQL_TABLE_COLUMN")
                    Self.redis_conn.createRelationship(table_entity.eid, column_entity.eid, "TABLE_COLUMN")
                    Self.redis_conn.createEntityProfile(column_entity.eid, "SQL_TABLE_COLUMN")
                    Self.redis_conn.setRelationship(table_entity.eid, column_entity.eid,
                                           "TABLE_COLUMN", {'weight':1, "columnName":column_entity.columnName})
            else:
                #update table entity with stats info in it
                Self.mongoconn.db.entities.update({"eid": column_entity.eid},{'$set':{'stats': stats}})
                #updated the upload stats for column
                Self.redis_conn.incrEntityCounter(Self.uid, "Compiler.%s.totalColumns"%(Self.compiler_to_use), incrBy=1)
        else:
            #Query mongo based to table name in order to update table stats
            table_name = stats['TABLE_NAME'].lower()
            table_entity = Self.mongoconn.getEntityByName(table_name)

            if table_entity is None:
                #create table entity with stats info in it
                eid = IdentityService.getNewIdentity(Self.tenant, True)
                table_entry = {"uid" : Self.uid, "stats":stats}
                table_entity = Self.mongoconn.addEn(eid, table_name, Self.tenant,\
                                EntityType.SQL_TABLE, table_entry, None)
                #create Elastic search index
                sendToElastic(connection1, Self.redis_conn, Self.tenant, Self.uid,
                              table_entity, table_name, EntityType.SQL_TABLE)
                Self.redis_conn.createEntityProfile(table_entity.eid, "SQL_TABLE")
                Self.redis_conn.incrEntityCounterWithSecKey(table_entity.eid,
                                                            "instance_count",
                                                            sec_key=table_entity.name,
                                                            sort=True, incrBy=0)
                if table_entity.eid != eid:
                    Self.mongoconn.db.entitieys.update({"eid": table_entity.eid},{'$set':{'stats': stats}})
                #updated the upload stats for table
                Self.redis_conn.incrEntityCounter(Self.uid, "Compiler.%s.newTables"%(Self.compiler_to_use), incrBy=1)
            else:
                #update table entity with stats info in it
                Self.mongoconn.db.entities.update({"eid": table_entity.eid},{'$set':{'stats': stats}})
                if table_name not in Self.table_stat_table_name_list:
                    #updated the upload stats for table
                    Self.redis_conn.incrEntityCounter(Self.uid, "Compiler.%s.totalTables"%(Self.compiler_to_use), incrBy=1)
                    Self.table_stat_table_name_list.append(table_name)

    def callback(Self, eid, update=False, name=None, etype=None, data=None, header_info=None):

        if eid is None:
            if not etype == 'SQL_QUERY':
                return

            if not Self.skipLimit and not Self.__checkQueryLimit():
                raise callback_context.QueryLimitReachedException("Tenant " + Self.tenant + " has exceeded query limit of " +
                                                                  str(Self.__getUploadLimit()) + " queries")

            Self.redis_conn.incrEntityCounter("dashboard_data", "TotalQueries", sort=False, incrBy=1)
            if update == False:
                jinst_dict = {}
                jinst_dict['program_type'] = "SQL"
                jinst_dict['query'] = name
                if data is not None:
                    jinst_dict['data'] = data

                tagArray = []
                countArray = []
                jinst_dict['tagArray'] = []
                jinst_dict['countArray'] = []
                if header_info is not None:
                    tagArray = generateTagArray(header_info)
                    countArray = generateCountArray(header_info)

                    user_obj = Self.mongoconn.db.userPrefs.find_one({"userPrefs": "userPrefs"}, {"tagArray": 1, "countArray": 1})

                    if user_obj:
                        if "tagArray" in user_obj:
                            tagArray += user_obj["tagArray"]
                        if "countArray" in user_obj:
                            countArray += user_obj["countArray"]

                    jinst_dict['tagArray'] = list(set(tagArray))
                    jinst_dict['countArray'] = list(set(countArray))
                    tag_list = jinst_dict['tagArray']
                    count_list = jinst_dict['countArray']
                    Self.mongoconn.db.userPrefs.update_one({"userPrefs": "userPrefs"},
                                                           {'$set': {'tagArray': tag_list,
                                                                     'countArray': count_list}}, upsert=True)
                compiler_msg = {'tenant': Self.tenant, 'job_instances': [jinst_dict]}
                if Self.sourcePlatform is not None:
                    compiler_msg['source_platform'] = Self.sourcePlatform
                else:
                    compiler_msg['source_platform'] = "teradata"

                if Self.uid is not None:
                    compiler_msg['uid'] = Self.uid
                message_id = genMessageID("FP", Self.redis_conn)
                compiler_msg['message_id'] = message_id
                """
                Send scale_mode opcode to compiler if scale_mode is set to true by either SQLScriptConnector trigger
                OR short circuit opcode from ftpqueue
                """
                if Self.scale_mode:
                    compiler_msg['opcode'] = "scale_mode"
                if Self.testMode:
                    compiler_msg['test_mode'] = 1

                message = dumps(compiler_msg)
                connection1.publish(Self.ch,'','compilerqueue',message)
                incrementPendingMessage(Self.collection, Self.redis_conn, Self.uid, message_id)
                Self.clog.debug("Published Compiler Message {0}\n".format(message))

            else:
                Self.redis_conn.incrEntityCounter(eid, "instance_count", incrBy=1)

                queryEntity = Self.mongoconn.db.entities.find_one({eid:"eid"},{'profile.Compiler.%s.ErrorSignature'%(Self.compiler_to_use):1})

                if "profile" not in queryEntity:
                    Self.clog.error("Failed in FP sendToCompiler 1")
                elif "Compiler" not in queryEntity["profile"]:
                    Self.clog.error("Failed in FP sendToCompiler 2")
                elif Self.compiler_to_use not in queryEntity["profile"]["Compiler"]:
                    Self.clog.error("Failed in FP sendToCompiler 3")
                elif "OperatorList" not in queryEntity["profile"]["Compiler"][Self.compiler_to_use]:
                    Self.clog.error("Failed in FP sendToCompiler 4")

                elif len(queryEntity["profile"]["Compiler"][Self.compiler_to_use]["OperatorList"]) > 1:
                    unique_queries = Self.mongoconn.db.entities.find({'profile.Compiler.%s.OperatorList'%(Self.compiler_to_use):{"$exists":1},
                        "$where":'this.profile.Compiler.%s.OperatorList.length > 1'%(Self.compiler_to_use)},{"eid":1,"_id":0})
                    uniqueEids = [x['eid'] for x in unique_queries]
                    unique_count = Self.mongoconn.db.entity_instances.find({"eid":{'$in':uniqueEids}}).count()
                    Self.redis_conn.setEntityProfile('dashboard_data', { "unique_count": unique_count})
                    Self.redis_conn.incrEntityCounter('dashboard_data', 'TotalQueries', incrBy=1)

                """
                Get relationships for the given entity.
                """
                updateRelationCounter(Self.redis_conn, eid)

            if not Self.skipLimit:
                Self.__incrementProcessedQueryCount()
            return

        entity = Self.mongoconn.getEntity(eid)
        if entity.etype == 'HADOOP_JOB':

            pub = True
            jinst_dict = {'entity_id':entity.eid}
            prog_type = ""
            if entity.instances[0].config_data.has_key("hive.query.string"):
                jinst_dict['program_type'] = "Hive"
                jinst_dict['query'] = entity.name
            elif entity.instances[0].config_data.has_key("pig.script.features"):
                jinst_dict['program_type'] = "Pig"
                jinst_dict['pig_features'] = int(entity.instances[0].config_data['pig.script.features'])
            else:
                Self.clog.debug("Progname found {0}\n".format(entity.name))
                pub = False
            if pub == True:
                compiler_msg = {'tenant':Self.tenant, 'job_instances':[jinst_dict]}
                if data is not None:
                    compiler_msg['data'] = data
                if Self.uid is not None:
                    compiler_msg['uid'] = Self.uid
                message_id = genMessageID("FP", Self.redis_conn)
                compiler_msg['message_id'] = message_id
                message = dumps(compiler_msg)
                connection1.publish(Self.ch,'','compilerqueue',message)
                incrementPendingMessage(Self.collection, Self.redis_conn, Self.uid, message_id)
                Self.clog.debug("Published Compiler Message {0}\n".format(message))

def callback(ch, method, properties, body):
    starttime = time.time()
    curr_socket = socket.gethostbyname(socket.gethostname())

    try:
        msg_dict = loads(body)
    except:
        logging.exception("Could not load the message JSON")

    logging.info("FPPS Got message "+ str( msg_dict))
    """
    Validate the message.
    """
    if not msg_dict.has_key("tenent") or \
       (not msg_dict.has_key("filename") and
        not msg_dict.has_key("opcode")):
        logging.error("Invalid message received\n")
        logging.error(body)
        connection1.basicAck(ch,method)
        return

    tenant = msg_dict["tenent"]
    client = getMongoServer(tenant)
    xplain_client = getMongoServer("xplainIO")
    redis_conn = RedisConnector(tenant)

    log_dict = {'tenant': tenant, 'tag': 'dataacquisitionservice'}
    if 'opcode' in msg_dict:
        log_dict['opcode'] = msg_dict['opcode']
    if 'uid' in msg_dict:
        log_dict['uid'] = msg_dict['uid']
    clog = LoggerCustomAdapter(logging.getLogger(__name__), log_dict)
    uid = None
    try:
        filename = None
        opcode = None

        if msg_dict.has_key("opcode") and msg_dict["opcode"] == "DeleteTenant":
            performTenantCleanup(tenant, clog)

            xplain_client["xplainIO"].organizations.update({"guid":tenant},\
            {"$set":{"uploads":0, "queries":0, "lastTimeStamp": 0}})
            return
    except:
        clog.exception("Testing Cleanup")

    """
    Scale mode should be triggered by a query number threshold.
    But scale_mode_enabled opcode provides short circuit capability to directly access scale mode.
    """
    scale_mode = False
    if "opcode" in msg_dict and msg_dict["opcode"] == "scale_mode":
        scale_mode = True

    elasticConnect(tenant, clog)
    r_collection = None
    dest_file = None

    """
    Check if this upload has vendor pre-selected.
    """
    source_platform = None
    if "source_platform" in msg_dict:
        source_platform = msg_dict["source_platform"]
    else:
        source_platform = "teradata"

    try:
        filename = msg_dict["filename"]
        filename = urllib.unquote(filename)

        header_info = None
        if 'header_info' in msg_dict:
            header_info = msg_dict['header_info']
        delimiter = {'col_delim': None, 'row_delim': None, 'elapsed_time_unit': None}
        if 'col_delim' in msg_dict and msg_dict['col_delim']:
            delimiter['col_delim'] = msg_dict['col_delim']
        if 'row_delim' in msg_dict and msg_dict['row_delim']:
            delimiter['row_delim'] = msg_dict['row_delim']
        if 'elapsed_time_unit' in msg_dict:
            delimiter['elapsed_time_unit'] = msg_dict['elapsed_time_unit']

        if msg_dict.has_key('uid'):
            uid = msg_dict['uid']

            collection = client[tenant].uploadStats
            startProcessingPhase(collection, redis_conn, uid)
            redis_conn.incrEntityCounter(uid, "FPProcessing.count", sort = False, incrBy= 1)
            redis_conn.setEntityProfile(uid, {"FPProcessing.socket":curr_socket})
            if metrics_url is not None:
                try:
                    r_collection = MongoClient(metrics_url)["remote_"+tenant].uploadStats
                    r_collection.insert({'uid':uid, "FPProcessing": {"count":1}})
                except:
                    clog.exception("Remote collection:")
                    r_collection = None

        source = tenant + "/" + filename

        if usingAWS:
            """
            Check if the file exists in S3.
            """
            if CLUSTER_NAME is not None:
                source = "partner-logs/" + source
            file_key = bucket.get_key(source)
            if file_key is None:
                clog.error("NOT FOUND: {0} not in S3\n".format(source))
                connection1.basicAck(ch,method)

                return

            """
            Check if the file has already been processed. TODO:
            """
            checkpoint = source + ".processed"
            #chkpoint_key = bucket.get_key(checkpoint)
            #if chkpoint_key is not None:
            #    errlog.write("ALREADY PROCESSED: {0} \n".format(source))
            #    errlog.flush()
            #    return
        else:
            clog.debug("Downloading and extracting file")

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
        tar = None
        if dest_file.endswith(".gz"):
            tar = tarfile.open(dest_file, mode="r:gz")
            tar.extractall(path=logpath)
            tar.close()
        elif dest_file.endswith(".tar"):
            tar = tarfile.open(dest_file)
            tar.extractall(path=logpath)
            tar.close()
        else:
            shutil.copy(dest_file, logpath)
    except:
        clog.exception("Downloading file")

    clog.debug("Extracted file : {0} \n".format(dest_file))
    if not usingAWS:
        clog.debug("Extracted file to /mnt/volume1/[tenent]/processing")

    """
    Check if this upload has requested to skip the limit check.
    """
    skipLimit = False
    if "skip_limit" in msg_dict and msg_dict["skip_limit"] == 1:
        skipLimit = True

    testMode = False
    if "test_mode" in msg_dict and msg_dict["test_mode"] == 1:
        testMode = True

    try:
        """
        Parse the data.
        """
        context = tenant
        mongoconn = Connector.getConnector(context)
        if mongoconn is None:
            mongoconn = MongoConnector({'client':client, 'context':context, \
                                    'create_db_if_not_exist':True})

        if redis_conn.getEntityProfile("dashboard_data") == {}:
            redis_conn.createEntityProfile("dashboard_data", "dashboard_data")
        '''
        Incremements a Pre-Processing count, sends to compiler, then decrements the count
        '''
        message_id = genMessageID("Pre", redis_conn)
        incrementPendingMessage(collection, redis_conn, uid, message_id)
        clog.debug("Incremementing message count: " + message_id)

        cb_ctx = callback_context(tenant, uid, ch, mongoconn, redis_conn, collection,
                                  scale_mode, skipLimit, testMode, source_platform, header_info, delimiter)

        parseDir(tenant, logpath, cb_ctx)

        callback_params = {'tenant':tenant, 'connection':connection1, 'channel':ch, 'uid':uid, 'queuename':'advanalytics'}
        decrementPendingMessage(collection, redis_conn, uid, message_id, end_of_phase_callback, callback_params)
        clog.debug("Decrementing message count: " + message_id)

        if usingAWS:
            """
            Checkpoint the file processing.
            """
            chkpoint_key = Key(bucket)
            chkpoint_key.key = checkpoint
            chkpoint_key.set_contents_from_string("Processed")
            clog.debug("Processed file : {0} \n".format(dest_file))

        """
        If we are in scale mode, close mongo, ack, and exit.
        Do not send messages to Math or update mongo collections.
        """
        if cb_ctx.scale_mode:
            mongoconn.close()
            connection1.basicAck(ch, method)
            return

    except:
        clog.exception("Parsing the input and Compiler Message")

    try:
        if uid is not None:

            #gets most recent upload timestamp.
            lastUploadTime = collection.find({'active': True},
                                             {'_id': 0, "timestamp": 1}).sort([("timestamp", -1)]).limit(1)
            if lastUploadTime is not None:
                lastUploadTime = list(lastUploadTime)
                if len(lastUploadTime) > 0:
                    lastUploadTime = lastUploadTime[0]
                    if lastUploadTime is not None:
                        if "timestamp" in lastUploadTime:
                            lastUploadTime = lastUploadTime["timestamp"]
                        else:
                            lastUploadTime = None
                    else:
                        lastUploadTime = None
                else:
                    lastUploadTime = None
            else:
                lastUploadTime = None

            #This query finds the latest upload and stores that timestamp in the timestamp variable
            if lastUploadTime is not None:
                timestamp = int(float(lastUploadTime))
            else:
                timestamp = 0

            xplain_client["xplainIO"].organizations.update({"guid": tenant},
                                                           {"$set": {"uploads": (collection.count()-1),
                                                            "lastTimeStamp": timestamp}})

            clog.debug("Updated the overall stats values.")
    except:
        clog.exception("Error while updating the overall stats values.")

    try:
        mongoconn.close()
        if msg_dict.has_key('uid'):
            #if uid has been set, the variable will be set already
            redis_conn.setEntityProfile(uid, {"FPProcessing.time":(time.time()-starttime)})
            if r_collection is not None:
                r_collection.update({'uid':uid},{"$set": {"FPProcessing.time":(time.time()-starttime)}})
    except:
        clog.exception("While closing mongo")

    #send stats to datadog
    if statsd:
        totalTime = ((time.time() - startTime) * 1000)
        statsd.timing("fpservice.per.msg.time", totalTime, tags=[tenant+":"+uid])
    connection1.basicAck(ch,method)

connection1 = RabbitConnection(callback, ['ftpupload'], ['compilerqueue','mathqueue','elasticpub'], {"Fanout": {'type':"fanout"}}, prefetch_count=1)


logging.info("FPProcessingService going to start consuming")

connection1.run()

if usingAWS:
    boto_conn.close()
logging.info("Closing FPProcessingService")
