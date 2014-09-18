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
from flightpath.ScaleModeConnector import *
import baazmath.workflows.hbase_analytics as Hbase
import baazmath.workflows.impala_analytics as Impala
import flightpath.services.app_get_table_detail as table_details
import flightpath.services.app_get_query_detail as query_details
import flightpath.services.app_get_upload_detail as upload_details
import flightpath.services.app_get_top_fact as top_fact
import flightpath.services.app_get_top_dim as top_dim
import flightpath.services.app_get_top_table_by_patterns as top_tables_by_pattern
import flightpath.services.app_get_top_tables as top_tables
import flightpath.services.app_get_tail_tables as tail_tables
import flightpath.services.app_get_top_select_columns as select_columns
import flightpath.services.app_get_top_join_columns as join_columns
import flightpath.services.app_get_top_filter_columns as filter_columns
import flightpath.services.app_get_top_groupby_columns as groupby_columns
import flightpath.services.app_get_top_orderby_columns as orderby_columns
import flightpath.services.app_get_table_stats as table_stats
import flightpath.services.app_get_column_stats as column_stats
import flightpath.services.app_get_access_patterns as access_patterns
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

APPSRV_LOG_FILE = "/var/log/applicationserice.err"

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

def process_mongo_rewrite_request(ch, properties, tenant, instances):

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

        if os.path.isfile(in_file):
            os.remove(in_file)

        if os.path.isfile(out_file):
            os.remove(out_file)

        sql_query = inst["query"]
        if len(sql_query.strip()) == 0:
            continue

        data_dict = { "InputFile": in_file, "OutputFile": out_file}

        """
            2. Save the query to a local file.
        """
        infile = open(in_file, "w")
        infile.write(sql_query)
        infile.flush()
        infile.close()

        """
            3. Invoke compiler to generate Xplain RA.
        """
        try:
            output_file_name = "/tmp/hbase_ddl.out"

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("localhost", 12121))

            data = dumps(data_dict)
            client_socket.send("1\n");

            """
                For Mongo rewrite the opcode is 3.
            """
            client_socket.send("3\n");
            data = data + "\n"
            client_socket.send(data)
            rx_data = client_socket.recv(512)

            if rx_data == "Done":
                status = "SUCCESS"
            else:
                status = "FAILED"

            client_socket.close()

            compile_doc = None
            """
                4. Read the output file as a JSON.
            """
            if not os.path.isfile(out_file):
                resp_dict["status"] = "Failed"
            else:
                """ 
                    Read the output file and send the RPC response.
                """
                compile_doc = None
                with open(out_file) as data_file:    
                    compile_doc = load(data_file)

                """
                    5. Invoke mongo converter template engine to convert.
                """
                mongo_query = convert_to_mongo(compile_doc["QueryBlock"])
                resp_dict['mongo_queries'].append(mongo_query)

            resp_dict["status"] = "Success"
        except:
            logging.exception("Tenent {0}, {1}\n".format(tenant, traceback.format_exc()))     
            resp_dict["status"] = "Failed"

    """
        6. Send the RPC response. 
    """
    return resp_dict
    #logging.info("Sending compiler response")
    #ch.basic_publish(exchange='',
    #                 routing_key=properties.reply_to,
    #                 properties=pika.BasicProperties(correlation_id = \
    #                                                 properties.correlation_id),
    #                 body=dumps(resp_dict))

def process_ddl_request(ch, properties, tenant, target, instances, db, redis_conn):

    """
        Steps to generate Hbase DDL are as following:
        1. Gets the pattern ID of the pattern. Finds the tables and 
           queries involved in the pattern.
        2. Invoke analytics workflow to generate Hbase analytics.
        3. Save the analytics results to a local file.
        4. Send request to DDL generator.
        5. Check the output file.
        6. Read output file and send the RPC response. 
    """
    compile_doc = None
    prog_id = None
    queryList = None
    transformType = ""
    for inst in instances:
        if 'entity_id' in inst:
            prog_id = inst['entity_id']
            transformType = 'SingleTable'
        elif "patID" in inst:
            prog_id = inst["patID"]
            transformType = 'SinglePattern'

    if prog_id is None:
        logging.info("No program ID found for ddl_request")
        return

    if transformType == "SingleTable":
        logging.info('Received SingleTable {0} transformation request.'.format(target))
        tableList = [prog_id]
    elif transformType == "SinglePattern":
        logging.info('Received SinglePattern {0} transformation request.'.format(target))
        join_group = db.entities.find_one({'profile.PatternID':prog_id}, {'eid':1, 'profile.FullQueryList':1})

        if join_group is None:
            return

        tableList = []
        queryList = []

        relations_to = redis_conn.getRelationships(join_group['eid'], None, "COOCCURRENCE_TABLE")
        for rel in relations_to:
            tableList.append(rel['end_en'])

        if "profile" in join_group:
            if "FullQueryList" in join_group['profile']:
                queryList = join_group['profile']['FullQueryList']

    """
        Invoke analytics workflow to generate Hbase analytics.
    """
    result = None
    if target == "hbase":
        result = Hbase.run_workflow(tenant, tableList, queryList)
    elif target == "impala":
        result = Impala.run_workflow(tenant, tableList, queryList)

    """
        Save the analytics results to a local file.
    """
    oFile_path = "/tmp/" + target + "_analytics.out"
    oFile = open(oFile_path, "w")
    oFile.write(dumps(result))
    oFile.flush()
    oFile.close()

    resp_dict = {}
    status = "FAILED"
    """
        Send request to DDL generator.
    """
    try:
        output_file_name = "/tmp/" + target + "_ddl.out"

        if os.path.isfile(output_file_name):
            os.remove(output_file_name)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        retry_count = 0
        socket_connected = False
        while (socket_connected == False) and (retry_count < 2):
            retry_count += 1
            try:
                client_socket.connect(("localhost", 12121))
                socket_connected = True
            except:
                logging.error("Unable to connect to JVM socket on try #%s." %retry_count)
                time.sleep(1)
        if socket_connected == False:
            raise Exception("Unable to connect to JVM socket.")

        data_dict = {"InputFile": oFile_path, "OutputFile": output_file_name, 
                     "EntityId": prog_id, "TenantId": "100"}
        data = dumps(data_dict)
        client_socket.send("1\n");

        """
            For DDL generation the opcode is 2.
        """
        client_socket.send("2\n");
        data = data + "\n"
        client_socket.send(data)
        rx_data = client_socket.recv(512)

        if rx_data == "Done":
            status = "SUCCESS"
        else:
            status = "FAILED"

        client_socket.close()

        """
            Upon response, check the output file.
        """
        if not os.path.isfile(output_file_name):
            resp_dict["status"] = "Failed"
        else:
            """ 
                Read the output file and send the RPC response.
            """
            compile_coc = None
            with open(output_file_name) as data_file:    
                compile_doc = load(data_file)
            resp_dict = compile_doc
            resp_dict["status"] = "Success"
    except:
        logging.exception("Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))     
        resp_dict["status"] = "Failed"

    """
        Publish the response to the requestor.
    """
    return resp_dict
    #logging.info("Sending compiler response")
    #ch.basic_publish(exchange='',
    #                 routing_key=properties.reply_to,
    #                 properties=pika.BasicProperties(correlation_id = \
    #                                                 properties.correlation_id),
    #                 body=dumps(resp_dict))

def callback(ch, method, properties, body):

    starttime = time.time()
    
    try:
        msg_dict = loads(body)
    except:
        logging.exception("Could not load the message JSON")
        return

    logging.info("ApplicationService: Got message : "+ str(msg_dict))
    if "opcode" not in msg_dict:
        return

    tenant = msg_dict["tenant"]
    mongo_url = getMongoServer(tenant)
    resp_dict = None

    try:
        """
         This needs to be dynamic in nature.
        """
        if msg_dict["opcode"] == "HbaseDDL":

            logging.info("Got the opcode of Hbase")
            instances = msg_dict["job_instances"]
            db = MongoClient(mongo_url)[tenant]
            redis_conn = RedisConnector(tenant)
            resp_dict = process_ddl_request(ch, properties, tenant, "hbase", instances, db, redis_conn)
        if msg_dict["opcode"] == "ImpalaDDL":

            logging.info("Got the opcode of Hbase")
            instances = msg_dict["job_instances"]
            db = MongoClient(mongo_url)[tenant]
            redis_conn = RedisConnector(tenant)
            resp_dict = process_ddl_request(ch, properties, tenant, "impala", instances, db, redis_conn)
        elif msg_dict["opcode"] == "MongoTransform":
    
            logging.info("Got the opcode For Mongo Translation")
            instances = msg_dict["job_instances"]
            resp_dict = process_mongo_rewrite_request(ch, properties, tenant, instances)
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
        elif msg_dict['opcode'] == "TopFact":
            resp_dict = top_fact.execute(tenant)
        elif msg_dict['opcode'] == "TopDim":
            resp_dict = top_dim.execute(tenant)
        elif msg_dict['opcode'] == "TopTablesByPattern":
            resp_dict = top_tables_by_pattern.execute(tenant)
        elif msg_dict['opcode'] == "TopTables":
            resp_dict = top_tables.execute(tenant)
        elif msg_dict['opcode'] == "TailTables":
            resp_dict = tail_tables.execute(tenant)
        elif msg_dict['opcode'] == "SelectColumns":
            resp_dict = select_columns.execute(tenant)
        elif msg_dict['opcode'] == "JoinColumns":
            resp_dict = join_columns.execute(tenant)
        elif msg_dict['opcode'] == "FilterColumns":
            resp_dict = filter_columns.execute(tenant)
        elif msg_dict['opcode'] == "GroupByColumns":
            resp_dict = groupby_columns.execute(tenant)
        elif msg_dict['opcode'] == "OrderByColumns":
            resp_dict = orderby_columns.execute(tenant)
        elif msg_dict['opcode'] == "TableStats":
            resp_dict = table_stats.execute(tenant)
        elif msg_dict['opcode'] == "ColumnStats" :
            resp_dict = column_stats.execute(tenant)
        elif msg_dict['opcode'] == "AccessPatterns":
            resp_dict = access_patterns.execute(tenant, msg_dict["accessPatternIds"])

    except:
        logging.exception("Proceesing request for " + msg_dict["opcode"])

    if resp_dict is None:
        resp_dict = {"status" : "Failed"}

    ch.basic_publish(exchange='',
                     routing_key=properties.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                     properties.correlation_id),
                         body=dumps(resp_dict))
    connection1.basicAck(ch,method)

connection1 = RabbitConnection(callback, ['appservicequeue'], [], {}, APPSRV_LOG_FILE)


logging.info("ApplicationService going to start consuming")

try:
    connection1.run()
except:
    logging.exception("In Run :")

if usingAWS:
    boto_conn.close()
logging.info("Closing ApplicationService")
