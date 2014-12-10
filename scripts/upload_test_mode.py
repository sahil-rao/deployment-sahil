#!/usr/bin/python
"""
Form Join groups for given query.
"""
import os
import time
import sys
from pymongo import *
from flightpath.Provenance import getMongoServer
import datetime
import uuid
import pika
from json import *
import shutil

"""
 Arg 1: user name
 Arg 2: input file
"""

rabbit_host = "127.0.0.1"
usingAWS = False

if usingAWS:
    import boto
    from boto.s3.key import Key

def doUpload(inp_file):

    if not os.path.isfile(inp_file):
        print "Input file does not exist"
        exit(0)
    inp_splits = inp_file.split()
    filename = inp_splits[len(inp_splits)-1]

    #Connect to Rabbit
    credentials = pika.PlainCredentials('xplain', 'xplain')
    vhost = 'xplain'
    pconn = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host, 5672, vhost, credentials))
    channel = pconn.channel()
    channel.queue_declare(queue='ftpupload')

    #Generate a uid
    org = "test-tenant"
    uid = str(uuid.uuid4())

    #put file to s3
    if usingAWS:
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
        s3filepath =  timestr + "/" + filename
        destination = org + "/" + s3filepath
        connection = boto.connect_s3()
        bucket = connection.get_bucket('partner-logs') # substitute your bucket name here
        file_key = Key(bucket)
        file_key.key = destination
        file_key.set_contents_from_filename(filename)
    else:
        dest_dir = "/mnt/volume1/" + org
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        shutil.copyfile(inp_file, dest_dir + "/" + filename)
        s3filepath = filename
    
    # Save upload record.
    timestamp = long(time.time()*1000)
    upload_record = {'tenant': org, 'filename': filename,
                'uid': uid, 'timestamp': timestamp, "active": True}
    org_client = MongoClient(host=getMongoServer(org))
    org_client[org].uploadStats.insert(upload_record)
    
    #Inject event to rabbit.
    msg_dict = {"tenent": org, "filename": s3filepath, "uid": uid, "test_mode": True}
    message = dumps(msg_dict)
    channel.basic_publish(exchange='', routing_key='ftpupload', body=message)
    
    #Close rabbitmq and mongo clients
    pconn.close()
    org_client.close()
