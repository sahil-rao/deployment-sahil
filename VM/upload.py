#!/usr/bin/python
import sys
import os
import pika
from json import *
import shutil

if len(sys.argv) != 3:
    sys.exit ('Incorrect Usage, use upload.py <tenant> <filepath>')

tenent = sys.argv[1]
filepath = sys.argv[2]

filename = os.path.split (filepath) [1]
destpath = '/mnt/volume1/' + tenent + "/"
if not os.path.isdir(destpath):
    os.makedirs(destpath)
shutil.copy(filepath, destpath)

pconn = pika.BlockingConnection(pika.ConnectionParameters(
               '127.0.0.1'))
channel = pconn.channel()
channel.queue_declare(queue='ftpupload')

#tenent = "customer"

msg_dict = {'tenent':tenent, 'filename':filename}
message = dumps(msg_dict)
channel.basic_publish(exchange='',
                      routing_key='ftpupload',
                      body=message)
pconn.close()
