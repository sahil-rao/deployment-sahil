#!/usr/bin/python

import boto
from boto.s3.key import Key
import sys
import os
import pika
from json import *
import datetime
import time

errlog = open("/var/log/baazmonitor.log", "w")

splits = sys.argv[1].split()

tenent = splits[7].strip('",[]')
filepath = splits[12].strip('",[]')
filename = filepath.rsplit("/", 1)[1]

timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')

source = "/mnt/volume1/" + tenent + filepath
s3filepath =  timestr + "/" + filename
destination = tenent + "/" + s3filepath

errlog.write("Source {0}, destination {1}\n".format(source, destination))

if not os.path.isfile(source):
    errlog.write("File {0} notfound \n".format(source))
    errlog.flush()
    errlog.close()
    exit(0)

connection = boto.connect_s3()
bucket = connection.get_bucket('partner-logs') # substitute your bucket name here
file_key = Key(bucket)
file_key.key = destination

file_key.set_contents_from_filename(source)

pconn = pika.BlockingConnection(pika.ConnectionParameters(
               '172.31.10.27'))
channel = pconn.channel()
channel.queue_declare(queue='ftpupload')

msg_dict = {'tenent':tenent, 'filename':s3filepath}
message = dumps(msg_dict)
channel.basic_publish(exchange='',
                      routing_key='ftpupload',
                      body=message)
pconn.close()
connection.close()

print "File upload done"
