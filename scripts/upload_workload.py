#!/usr/bin/env python
# (c) Copyright (four-digit-year) Cloudera, Inc. All rights reserved.

"""
upload_workload - Tool for uploading large workloads.
    Checkout upload_workload.py -h for command line options.
"""

import sys
import inspect
import elasticsearch
from flightpath.services.RabbitMQConnectionManager import *
from pymongo import MongoClient
from flightpath.Provenance import getMongoServer, getElasticServer
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from flightpath.RedisConnector import *
from tendo import singleton
import uuid
import time
import json
import pika
import datetime
import smtplib
import shutil
import os
import argparse
import boto

parser = argparse.ArgumentParser()
parser.add_argument('--tenant', nargs=1, help='Tenant Id to use for testing.')
parser.add_argument('--workload', nargs=1, help='Workload to run.')
#parser.add_argument('--s3_path', nargs=1, help='s3path of the workload')
parser.add_argument('--source_platform', nargs=1, help='source platform of the workload.')
parser.add_argument('--emails', nargs="+", help='email adress to send email to')

args = parser.parse_args()

config = ConfigParser.RawConfigParser()
config.read("/var/Baaz/hosts.cfg")
usingAWS = config.getboolean("mode", "usingAWS")
CLUSTER_NAME = config.get("ApplicationConfig", "clusterName")


tenantid_list = args.tenant
if not tenantid_list:
    print "Tenant ID not given. This is a required parameter"
    print "Aborting upload"
    exit(0)
else:
    '''
    Gets the first tenant id passed in.
    '''
    tenantid = tenantid_list[0]

source_platform = args.source_platform
if not source_platform:
    source_platform = 'teradata'
else:
    source_platform = source_platform[0]
"""
s3_path = args.s3_path
if not s3_path:
    if 's3_path' in test_config:
        s3_path = test_config['s3_path']
    else:
        s3_path = None
else:
    s3_path = s3_path[0]
"""

workloads = args.workload
if not workloads:
    print "Please specify a workload to upload"
    exit(0)
else:
    workload = workloads[0] 

email_recipients = args.emails
if not email_recipients:
    email_recipients = []

"""
1 Verify that the tenantid exists in the mongo. TODO:
2 Verify workload exists.
"""

print
print "Upload Parameters : "
print "Workload : ", workload
print "Source Platform : ", source_platform
print "Tenant : ", tenantid
print
print

# TODO: Move to config file
UPLOAD_REPORT_FILE = './upload_report'
MONGO_POLLING_INTERVAL = 0.5

"""
def load_s3_path(s3_path):
    dest_dir = '/tmp/workloads/' + workload + '/'
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)
    connection = boto.connect_s3()
    bucket = connection.get_bucket(CLUSTER_NAME)
    print 'downloading to directory ' + dest_dir
    for file_key in bucket.list(prefix='testworkloads/' + s3_path):
        print 'downloading...' + file_key.name
        file_name = os.path.basename(file_key.name)
        d_file = open(dest_dir + file_name, "w+")
        file_key.get_contents_to_file(d_file)
        d_file.close()
    return dest_dir
"""

progress_chars = ['-','\\','|','/']
progress_idx = 0
 
def print_progress(prefix):
    global progress_chars
    global progress_idx
    print prefix + " " + "".join(progress_chars[progress_idx]) + "\r",
    progress_idx = (progress_idx + 1) % len(progress_chars)
    sys.stdout.flush()
    


def setup_tenant():
    global tenantid, workload, source_platform
    workload_location = os.getcwd()  + "/workloads/" + workload
 #   if s3_path:
 #       workload_location = load_s3_path(s3_path)
    
    print workload_location
    files = [f for f in os.listdir(workload_location) if os.path.isfile(workload_location + "/" + f)]
    timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
    filepath = ''
    num_files = str(len(files))
    print "total files : ", num_files

    mconn = getMongoServer(tenantid)
    
    redis_conn = RedisConnector(tenantid)
    rabbit_connection = RabbitConnection(None, [], ['ftpupload'], {})
    rabbit_connection.connect()
    uid = str(uuid.uuid4())
    for filename in files:
        workload_file = workload_location + "/" + filename
        filepath = timestr + "/" + filename
        if usingAWS:
            destination = "partner-logs" + "/" + tenantid + "/" + filepath
            connection = boto.connect_s3()
            bucket = connection.get_bucket(CLUSTER_NAME)
            file_key = boto.s3.key.Key(bucket)
            file_key.key = destination
            file_key.set_contents_from_filename(workload_file)
        else:
            destpath = '/mnt/volume1/' + tenantid + "/" + timestr
            if not os.path.isdir(destpath):
                os.makedirs(destpath)
            destfile = destpath + "/" + filename
            shutil.copy(workload_file, destfile)

        #Save upload record
        upload_record = {
                'tenant': tenantid,
                'filename': filepath,
                'uid': uid,
                'timestamp': long(time.time() * 1000),
                'source_platform': source_platform,
                'active': True
        }

        mconn[tenantid].uploadStats.insert(upload_record)
        redis_conn.setUIDStatus(uid, True)

        #Inject rabbitMQ event
        msg_dict = {
            'tenent': tenantid,
            'filename': filepath,
            'uid': uid,
            'source_platform': source_platform,
        }

        msg_json = json.dumps(msg_dict)
        rabbit_connection.publish(None, '', 'ftpupload', msg_json)

    #Poll until processing is complete
    processing = True
    while processing:
        upload_info = mconn[tenantid].uploadStats.find_one({'active':True})
        if 'Phase2MessageProcessed' in upload_info:
            print "\nUpload done"
            print upload_info
            processing = False
        else:
            print_progress("Uploading")
            time.sleep(MONGO_POLLING_INTERVAL)
            

def email_report(f):
    f.seek(0)
    upload_results = f.read()
    #TODO: Encrypt this and put into config file
    from_address = 'noreply@baazdata.com'
    password = 'Xplainio123'
    recipients = email_recipients
    if not recipients:
        return
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Upload Results'
    msg['From'] = from_address
    msg['To'] = ', '.join(recipients)
    msg.attach(MIMEText(upload_results, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(from_address, password)
    server.helo()
    server.sendmail(from_address, recipients, msg.as_string())
    server.quit()
    print "Report Emailed"


class stream_to_disk_and_screen:
    def __init__(self, stream):
        self.terminal = sys.stdout
        self.logstream = stream

    def write(self, buf):
        self.terminal.write(buf)
        self.logstream.write(buf)

    def flush(self):
        self.terminal.flush()
        self.logstream.flush()


def run_upload_job():
    with open(UPLOAD_REPORT_FILE, 'w+') as upload_report_file:
        global workload
        print "Starting test with workload "+ workload + " at " + datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d_%H:%M:%S')
        upload_report_file.write('\n======= Workload:' + workload + ' ========\n')
        setup_tenant()
        print "Upload complete"
        email_report(upload_report_file) 


if __name__ == '__main__':
    me = singleton.SingleInstance() #prevent more than one workload upload from running on one machine
    run_upload_job()
