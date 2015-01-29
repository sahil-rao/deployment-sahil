#!/usr/bin/python

"""
Compile Service:
"""
from flightpath.MongoConnector import *
from subprocess import Popen, PIPE
from json import *
import sys
import pika
import shutil
import os
import time
import datetime
import traceback
import re
import ConfigParser

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
rabbitserverIP = config.get("RabbitMQ", "server")
mongoserverIP = config.get("MongoDB", "server")

rabbitserverIP = rabbitserverIP.split(",")[0]
print rabbitserverIP
credentials = pika.PlainCredentials('xplain', 'xplain')
vhost = 'xplain'

connection = pika.BlockingConnection(pika.ConnectionParameters(
        rabbitserverIP, None, vhost, credentials))
channel = connection.channel()
channel.queue_declare('advanalytics')

print "Sending phase 2 message."

params = {}
params['tenant'] =sys.argv[1]
params['uid'] =sys.argv[2]


msg_dict = {'tenant':params['tenant'], 'opcode':"PhaseTwoAnalysis"} 
msg_dict['uid'] = params['uid']
message = dumps(msg_dict)
channel.basic_publish(exchange = '',routing_key = 'advanalytics', body = message)

print "Done"