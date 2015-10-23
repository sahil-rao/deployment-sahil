#!/usr/bin/env python
import sys
from pymongo import MongoClient
from flightpath.Provenance import getMongoServer
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from flightpath.services import app_cleanup_user, app_get_upload_status
from flightpath.RedisConnector import *
import boto
import uuid
import time
import json
import pika
import datetime
import smtplib

# TODO: Move to config file
WORKLOADS = ['TPCH']
BASELINES = ['master']
TEST_CASES = ['TestDashboardData']
REGRESSION_TEST_CONFIG_LOCATION = '/home/ubuntu/regression_test_config.json'
#Email is regression_tester@xplain.io
TEST_TENANT = '00e8b526-2da6-8868-9422-b4ea9bf7cc08'
TEST_TENANTS = ["65b78d6d-eda9-1377-a35b-27e8a4748714","727d1099-d8e5-b665-5bbe-a7d9e1cd9879","548e6fb1-80a4-5948-f026-a14ae5ff0b97","0dfc46f9-f73f-3ba8-7798-893a36527955","c7937f7b-a240-5dcb-0428-c54fad172dba","432352cf-dc27-52dd-ee1f-e9d90c9d93b1","5b724d0b-57aa-72e5-2436-d27f05377588","92368d9e-a3a2-15de-08be-08177427d608","a6c09222-fb60-081e-ab75-6c987d66ebed","15f55712-01f1-ab98-2d22-b7ba400fa1e9"]
TENANT_MAP = {
  "5b724d0b-57aa-72e5-2436-d27f05377588": "scale_test7@xplain.io",
  "65b78d6d-eda9-1377-a35b-27e8a4748714": "scale_test1@xplain.io",
  "a6c09222-fb60-081e-ab75-6c987d66ebed": "scale_test9@xplain.io",
  "548e6fb1-80a4-5948-f026-a14ae5ff0b97": "scale_test3@xplain.io",
  "727d1099-d8e5-b665-5bbe-a7d9e1cd9879": "scale_test2@xplain.io",
  "15f55712-01f1-ab98-2d22-b7ba400fa1e9": "scale_test10@xplain.io",
  "c7937f7b-a240-5dcb-0428-c54fad172dba": "scale_test5@xplain.io",
  "432352cf-dc27-52dd-ee1f-e9d90c9d93b1": "scale_test6@xplain.io",
  "92368d9e-a3a2-15de-08be-08177427d608": "scale_test8@xplain.io",
  "0dfc46f9-f73f-3ba8-7798-893a36527955": "scale_test4@xplain.io"
}
WORKLOAD_LOCATIONS = {
    'TPCH': '/home/ubuntu/tpch.tar',
    'arrow': '/home/ubuntu/all_arrow.sql'
}
RABBITMQ_IP = '172.31.15.82'
RABBITMQ_PORT = 5672
TEST_REPORT_FILE = '/home/ubuntu/test_report'
MONGO_POLLING_INTERVAL = 3



def setup_tenant(workload, test_tenant = TEST_TENANT):
    workload_file = WORKLOAD_LOCATIONS[workload]
    filename = workload_file.split('/')[-1]
    
    #Put file into S3
    timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
    s3filepath =  timestr + "/" + filename
    destination = "partner-logs" + "/" + test_tenant + "/" + s3filepath
    connection = boto.connect_s3()
    bucket = connection.get_bucket('xplain-alpha') 
    file_key = boto.s3.key.Key(bucket)
    file_key.key = destination
    file_key.set_contents_from_filename(workload_file)

    #Save upload record
    mconn = getMongoServer(test_tenant)
    redis_conn = RedisConnector(test_tenant)
    uid = str(uuid.uuid4())
    upload_record = {
        'tenant': test_tenant,
        'filename': filename,
        'uid': uid,
        'timestamp': long(time.time() * 1000),
        'source_platform': 'oracle',
        'active': True
    }
    mconn[test_tenant].uploadStats.insert(upload_record)
    redis_conn.setUIDStatus(uid, True)
    redis_conn.setUIDStatus(uid, True)
    mconn.close()

    #Inject rabbitMQ event
    credentials = pika.PlainCredentials('xplain', 'xplain')
    vhost = 'xplain'
    pconn = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_IP, RABBITMQ_PORT, vhost, credentials))
    channel = pconn.channel()
    channel.queue_declare(queue='ftpupload')
    msg_dict = {
        'tenent': test_tenant,
        'filename': s3filepath,
        'uid': uid,
        'source_platform': 'oracle'
    }
    msg_json = json.dumps(msg_dict)
    channel.basic_publish(
        exchange='',
        routing_key='ftpupload',
        body=msg_json
    )

def poll_tenant(test_tenant):
    #Poll until processing is complete
    print "Upload now polling"
    done = False
    upload_status = app_get_upload_status.execute(test_tenant)
    for key in upload_status:
        if key == 'sessions':
            continue
    if 'Phase2MessageProcessed' in upload_status[key]:
        done = True
    return done

def cleanup_tenant(tenantid=TEST_TENANT):
    app_cleanup_user.execute(tenantid, {})

def run_scale_test():
    '''
    Uploads workload into all accounts.
    Polls each account to get the status.
    '''
    start_time = time.time()
    workload = 'arrow'
    all_done = False
    status_dict = {}
    for test_tenant in TEST_TENANTS:
        print 'Cleaning up user: %s'%(TENANT_MAP[test_tenant])
        cleanup_tenant(test_tenant)
        status_dict[TENANT_MAP[test_tenant]] = False
        print 'Starting upload for user: %s'%(TENANT_MAP[test_tenant])
        setup_tenant(workload, test_tenant)

    if len(status_dict) == 0:
        all_done = True
    while not all_done:
        for test_tenant in TEST_TENANTS:
             res = poll_tenant(test_tenant)
             status_dict[TENANT_MAP[test_tenant]] = res
        '''
        Checks if all tenants are done or not.
        '''
        if sum(status_dict[test_tenant] for test_tenant in status_dict) == len(status_dict):
            all_done = True
        print json.dumps(status_dict, indent = 2)

        time.sleep(MONGO_POLLING_INTERVAL)
    end_time = time.time()
    total_time = end_time - start_time
    print 'Done! %s'%(total_time)

if __name__ == '__main__':
    run_scale_test()
