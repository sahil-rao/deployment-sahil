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
from baazmath.workflows.hbase_analytics import *
import flightpath.services.app_get_table_detail as table_details
import flightpath.services.app_get_query_detail as query_details
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

def process_hbase_ddl_request(ch, properties, tenant, instances, db, redis_conn):

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
        logging.info("No program ID found for hbase_ddl_request")
        return

    if transformType == "SingleTable":
        logging.info('Received SingleTable hbase transformation request.')
        tableList = [prog_id]
    elif transformType == "SinglePattern":
        logging.info('Received SinglePattern hbase transformation request.')
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
    result = run_workflow(tenant, tableList, queryList)

    """
        Save the analytics results to a local file.
    """
    oFile_path = "/tmp/hbase_analytics.out"
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
        output_file_name = "/tmp/hbase_ddl.out"

        if os.path.isfile(output_file_name):
            os.remove(output_file_name)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", 12121))

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
            resp_dict = process_hbase_ddl_request(ch, properties, tenant, instances, db, redis_conn)
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
