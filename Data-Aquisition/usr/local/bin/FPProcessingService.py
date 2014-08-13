#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenant> <log Directory>
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
import urllib

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"
BAAZ_FP_LOG_FILE = "/var/log/FPProcessing.err"

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
    if os.path.isfile(BAAZ_FP_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(BAAZ_FP_LOG_FILE, BAAZ_FP_LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=BAAZ_FP_LOG_FILE,level=logging.INFO,datefmt='%m/%d/%Y %I:%M:%S %p')

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    bucket = boto_conn.get_bucket('partner-logs') 
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(BAAZ_FP_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))

def end_of_phase_callback(params, current_phase):
    if current_phase > 1:
        logging.info("Attempted end of phase callback, but current phase > 1")
        return

    logging.info("Changing processing Phase")
    msg_dict = {'tenant':params['tenant'], 'opcode':"PhaseTwoAnalysis"} 
    msg_dict['uid'] = params['uid']
    message = dumps(msg_dict)
    params['connection'].publish(params['channel'],'',params['queuename'],message) 
    return

def performTenantCleanup(tenant):
    logging.info("Cleaning Tenant "+ tenant) 
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

def elasticConnect(tenantID):

    elastichost = getElasticServer(tenantID)
    if elastichost is None:
        return
    mongoserver = getMongoServer(tenantID)
    mongoserver = mongoserver.replace('/', '')
    mongoserver = mongoserver.replace('mongodb:', '')

    es = elasticsearch.Elasticsearch(hosts=[{'host' : elastichost, 'port' : 9200}])
    if es is None:
        return
    try:
        mapping = loads('{\
            "entity" : {\
                "properties" : {\
                "name":{\
                    "type":"completion",\
                    "context" : {\
                        "etype" : {\
                            "type" : "category",\
                            "default" : ["SQL_QUERY","SQL_TABLE"],\
                            "path" : "etype"\
                        }\
                    },\
                    "fields" : {\
                        "untouched" : {\
                            "type":"string",\
                            "index":"not_analyzed"\
                        }\
                    }\
                },\
                "eid" : {\
                    "type" : "completion"\
                }\
            }\
            }\
        }')
        settings = loads('{\
            "index" : {\
                "number_of_shards" : 3,\
                "number_of_replicas": 0\
            }\
        }')
        es.indices.create(index=tenantID, body=settings, ignore=[400,409])
        es.indices.put_mapping(index=tenantID, doc_type='entity', body=mapping, ignore=[400,409])

        doc = '{\
              "type": "mongodb",\
              "mongodb": {\
                "servers": [\
              { "host": "' + mongoserver + '", "port": 27017 }\
            ],\
            "options": {\
                "secondary_read_preference": true,\
                "exclude_fields" : ["logical_name", "md5"]\
            },\
            "db": "' + tenantID + '",\
            "collection": "entities"\
          },\
          "index": {\
            "name": "' + tenantID + '",\
            "type": "entity"\
          }\
        }'
        jsondoc = loads(doc)
        es.create(index='_river', doc_type=tenantID, id='_meta', body=jsondoc, ignore=[400,409])
    except:
        pass

class callback_context():

    def __init__(Self, tenant, uid, ch, mongoconn, redis_conn, collection, 
                 skipLimit=False, sourcePlatform=None):
        Self.tenant = tenant
        Self.uid = uid
        Self.ch = ch
        Self.mongoconn = mongoconn
        Self.redis_conn = redis_conn
        Self.collection = collection
        Self.uploadLimit = Self.__getUploadLimit()
        Self.skipLimit = skipLimit
        Self.sourcePlatform = sourcePlatform

    def query_count(Self, total_queries_found):
        """
        Report total number of queries found.

        Store the total count in the upload stats.
        """
        logging.info("Total Queries found " + str(total_queries_found))
        if not Self.skipLimit and total_queries_found > Self.uploadLimit:
            Self.collection.update({'uid':Self.uid},{'$set':{"total_queries":str(Self.uploadLimit), "processed_queries":0}}) 
            return

        Self.collection.update({'uid':Self.uid},{'$set':{"total_queries":str(total_queries_found), "processed_queries":0}}) 

    def __getUploadLimit(Self):
        """
        This should be fetched from a db.
        """
        return 1000

    def __checkQueryLimit(Self):
        upStats = Self.collection.find_one({'uid':"0"})
        if upStats is None:
            return True

        if "query_processed" not in upStats:
            Self.collection.update({'uid':Self.uid},{'$set':{"query_processed":0}}) 
            return True
         
        """
        TODO Get the limit from the user database
        """
        if Self.uploadLimit == 0:
            return True

        if upStats["query_processed"] >= Self.uploadLimit:
            return False

        return True

    def __incrementProcessedQueryCount(Self):
        Self.collection.update({'uid':"0"},{'$inc':{"query_processed": 1}}) 

    def callback(Self, eid, update=False, name=None, etype=None, data=None):

        if eid is None:
            if not etype == 'SQL_QUERY': 
                return

            if not Self.skipLimit and not Self.__checkQueryLimit():
                return

            """
            For SQL query, send any new query to compiler first.
            If this is an update to existing query,
            updates the appropriate relationships that will be used by math.
            """
            Self.redis_conn.incrEntityCounter("dashboard_data", "TotalQueries", sort=False, incrBy=1)
            logging.info(Self.redis_conn.getEntityProfile('dashboard_data'))
            if update == False:
                jinst_dict = {} 
                jinst_dict['program_type'] = "SQL"
                jinst_dict['query'] = name
                if data is not None:
                    jinst_dict['data'] = data
                compiler_msg = {'tenant':Self.tenant, 'job_instances':[jinst_dict]}
                if Self.sourcePlatform is not None:
                    compiler_msg['source_platform'] = Self.sourcePlatform

                if Self.uid is not None:
                    compiler_msg['uid'] = Self.uid
                message_id = genMessageID("FP", Self.collection)
                compiler_msg['message_id'] = message_id
                message = dumps(compiler_msg)
                connection1.publish(Self.ch,'','compilerqueue',message)
                incrementPendingMessage(Self.collection, Self.redis_conn, Self.uid, message_id)
                logging.info("Published Compiler Message {0}\n".format(message))
            else:
                Self.redis_conn.incrEntityCounter(eid, "instance_count", incrBy=1)

                queryEntity = Self.mongoconn.db.entities.find_one({eid:"eid"},{'profile.Compiler.gsp.ErrorSignature':1})

                if "profile" not in queryEntity:
                    logging.info("Failed in FP sendToCompiler 1")
                elif "Compiler" not in queryEntity["profile"]:
                    logging.info("Failed in FP sendToCompiler 2")
                elif "gsp" not in queryEntity["profile"]["Compiler"]:
                    logging.info("Failed in FP sendToCompiler 3")
                elif "OperatorList" not in queryEntity["profile"]["Compiler"]["gsp"]:
                    logging.info("Failed in FP sendToCompiler 4")

                elif len(queryEntity["profile"]["Compiler"]["gsp"]["OperatorList"]) > 1:
    
                    Self.mongoconn.db.dashboard_data.update({'tenant':Self.tenant},\
                            {'$inc' : {"TotalQueries": 1, "unique_count": 1}})

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
                logging.info("Progname found {0}\n".format(entity.name))
                pub = False
            if pub == True:
                compiler_msg = {'tenant':Self.tenant, 'job_instances':[jinst_dict]}
                if data is not None:
                    compiler_msg['data'] = data
                if Self.uid is not None:
                    compiler_msg['uid'] = Self.uid
                message_id = genMessageID("FP", Self.collection)
                compiler_msg['message_id'] = message_id
                message = dumps(compiler_msg)
                connection1.publish(Self.ch,'','compilerqueue',message)
                incrementPendingMessage(Self.collection, Self.redis_conn, Self.uid, message_id)
                logging.info("Published Compiler Message {0}\n".format(message))
    
def callback(ch, method, properties, body):
    starttime = time.time()
    
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
    mongo_url = getMongoServer(tenant)

    uid = None
    try:
        filename = None
        opcode = None
        
        if msg_dict.has_key("opcode") and msg_dict["opcode"] == "DeleteTenant":
            performTenantCleanup(tenant)

            MongoClient(mongo_url)["xplainIO"].organizations.update({"guid":tenant},\
            {"$set":{"uploads":0, "queries":0, "lastTimeStamp": 0}})
            return
    except:
        logging.exception("Testing Cleanup")

    elasticConnect(tenant)
    r_collection = None
    dest_file = None
    try:
        filename = msg_dict["filename"]
        filename = urllib.unquote(filename)

        if msg_dict.has_key('uid'):
            uid = msg_dict['uid']

            collection = MongoClient(mongo_url)[tenant].uploadStats
            collection.update({'uid':uid},{'$inc':{"FPProcessing.count":1}, '$set':{"FPProcessing.socket":socket.gethostbyname(socket.gethostname())}})
            startProcessingPhase(collection, uid)
            if metrics_url is not None:
                try:
                    r_collection = MongoClient(metrics_url)["remote_"+tenant].uploadStats
                    r_collection.insert({'uid':uid, "FPProcessing": {"count":1}})
                except:
                    logging.exception("Remote collection:")
                    r_collection = None

        source = tenant + "/" + filename

        if usingAWS:
            """
            Check if the file exists in S3. 
            """ 
            file_key = bucket.get_key(source)
            if file_key is None:
                logging.error("NOT FOUND: {0} not in S3\n".format(source))     
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
            logging.info("Downloading and extracting file")

        """
        Download the file and extract:
        """ 
        dest_file = BAAZ_DATA_ROOT + tenant + "/" + filename
        destination = os.path.dirname(dest_file)
        logging.info("Destination: "+str(destination))
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
        logging.exception("Downloading file")

    logging.info("Extracted file : {0} \n".format(dest_file))     
    if not usingAWS:
        logging.info("Extracted file to /mnt/volume1/[tenent]/processing")
   
    """
    Check if this upload has requested to skip the limit check.
    """
    skipLimit = False
    if "skip_limit" in msg_dict and msg_dict["skip_limit"] == 1:
        skipLimit = True

    """
    Check if this upload has vendor pre-selected.
    """
    source_platform = None
    if "source_platform" in msg_dict:
        sourcePlatform = msg_dict["source_platform"] 

    try:
        """
        Parse the data.
        """
        context = tenant
        mongoconn = Connector.getConnector(context)
        if mongoconn is None:
            mongoconn = MongoConnector({'host':mongo_url, 'context':context, \
                                    'create_db_if_not_exist':True})

        redis_conn = RedisConnector(tenant)

        if redis_conn.getEntityProfile("dashboard_data") == {}:
            redis_conn.createEntityProfile("dashboard_data", "dashboard_data")
        '''
        Incremements a Pre-Processing count, sends to compiler, then decrements the count
        '''
        message_id = genMessageID("Pre", collection)
        incrementPendingMessage(collection, redis_conn, uid, message_id)
        logging.info("Incremementing message count: " + message_id)

        cb_ctx = callback_context(tenant, uid, ch, mongoconn, redis_conn, collection, 
                                  skipLimit, source_platform)
        parseDir(tenant, logpath, cb_ctx)

        callback_params = {'tenant':tenant, 'connection':connection1, 'channel':ch, 'uid':uid, 'queuename':'mathqueue'}
        decrementPendingMessage(collection, redis_conn, uid, message_id, end_of_phase_callback, callback_params)
        logging.info("Decrementing message count: " + message_id)

        if usingAWS:
            """
            Checkpoint the file processing.
            """
            chkpoint_key = Key(bucket)
            chkpoint_key.key = checkpoint
            chkpoint_key.set_contents_from_string("Processed")
            logging.info("Processed file : {0} \n".format(dest_file))     

    except:
        logging.exception("Parsing the input and Compiler Message")

    try:

        math_msg = {'tenant':tenant, 'opcode':"BaseStats"}
        if uid is not None:
            math_msg['uid'] = uid
        message_id = genMessageID("FP", collection)
        math_msg['message_id'] = message_id
        message = dumps(math_msg)
        connection1.publish(ch,'','mathqueue',message)
        collection.update({'uid':uid},{'$inc':{"Math2MessageCount":1}})
        incrementPendingMessage(collection, redis_conn, uid,message_id)
        logging.info("Published Message {0}\n".format(message))
    except:
        logging.exception("Publishing Math Message")

    try:
        if uid is not None:
            queryNo = redis_conn.getEntityProfile("dashboard_data", "TotalQueries")
            if queryNo is not None:
                if "TotalQueries" in queryNo:
                    if queryNo["TotalQueries"] is not None:
                        queries = int(queryNo["TotalQueries"])
                    else:
                        queries = 0
                else:
                    queries = 0
            else:
                queries = 0

            lastUploadTime = collection.find({},{"_id":0, "timestamp":1}).sort([("timestamp",-1)]).limit(1)
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
                timestamp = int(lastUploadTime)
            else:
                timestamp = 0

            MongoClient(mongo_url)["xplainIO"].organizations.update({"guid":tenant},{"$set":{"uploads": (collection.count() -1) , \
                "queries":queries, "lastTimeStamp": timestamp}})

            logging.info("Updated the overall stats values.")
    except:
        logging.exception("Error while updating the overall stats values.")

    try:
        mongoconn.close()
        if msg_dict.has_key('uid'):
            #if uid has been set, the variable will be set already
            collection.update({'uid':uid},{"$set": {"FPProcessing.time":(time.time()-starttime)}})
            if r_collection is not None:
                r_collection.update({'uid':uid},{"$set": {"FPProcessing.time":(time.time()-starttime)}})
    except:
        logging.exception("While closing mongo")

    connection1.basicAck(ch,method)

connection1 = RabbitConnection(callback, ['ftpupload'],['compilerqueue','mathqueue'], {"Fanout": {'type':"fanout"}},BAAZ_FP_LOG_FILE)


logging.info("FPProcessingService going to start consuming")

connection1.run()

if usingAWS:
    boto_conn.close()
logging.info("Closing FPProcessingService")
