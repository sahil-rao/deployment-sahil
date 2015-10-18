#!/usr/bin/python
"""
Form Join groups for given query.
"""
import os
import time
import sys
import ConfigParser
from pymongo import *
from flightpath.Provenance import getMongoServer
from flightpath.RedisConnector import deleteTenant
import datetime
import uuid
import boto
from boto.s3.key import Key
import pika
from json import *
import redis


"""
 Arg 1: user name - user name will be appended with numbers...eg. 
        "scale" -> scale@xplain.io1, scale@xplain.io2....
 Arg 2: number of users.
 Arg 3: Input file.
"""

#print "This is currently incomplete - Please do not run"
#exit(0)

account_name = sys.argv[1]

mongo_servers = ["server"]
client = getMongoServer('xplainIO')
r = redis.StrictRedis(host='10.0.0.211', port=6379, db=0)

import boto
s3 = boto.connect_s3()
bucket = s3.get_bucket("partner-logs")

credentials = pika.PlainCredentials('xplain', 'xplain')
vhost = 'xplain'

pconn = pika.BlockingConnection(pika.ConnectionParameters('10.0.0.196', 5672, vhost, credentials))

channel = pconn.channel()
channel.queue_declare(queue='ftpupload')

# Find users 
user_dict = {}
uname = account_name + "@xplain.io"
for user_entry in client.xplainIO.users.find():
    if not user_entry["email"].startswith(uname):
        continue

    # Get tenant ID
    user_dict[user_entry["email"]] = user_entry["organizations"][0]

print "Total users found to be deleted : ", len(user_dict.keys())

for key in user_dict:
    uid = user_dict[key]

    # delete the user account
    client.xplainIO.users.remove({"email":key})

    #delete the organizaton
    client.xplainIO.organizations.remove({"guid":uid})

    #delete tenant database
    #tenant_client_server = None
    #routing_info = client.tenantrouting.tenantrouting.find_one()
    #if routing_info is not None and uid in routing_info:
    #    tenant_client_server = routing_info[uid]
    mongo_server = getMongoServer(uid)
    print "Going to drop :", uid, " From :", mongo_server
    tenant_client =  MongoClient(host=mongo_server)
    tenant_client.drop_database(uid)
    tenant_client.close()

    #delete tenant data from redis
    deleteTenant(uid, host='10.0.0.211')

    #Delete the s3 partner-upload directory
    bucketListResultSet = bucket.list(prefix=uid)
    result = bucket.delete_keys([key.name for key in bucketListResultSet])

    #Inject event to rabbit.
    msg_dict = {"tenent": uid, "opcode": "DeleteTenant"}
    message = dumps(msg_dict)
    print "Message :", message
    channel.basic_publish(exchange='',
                          routing_key='ftpupload',
                          body=message)
    print "User : ", key, " Dropped."

pconn.close()
client.close()