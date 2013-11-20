#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenent> <log Directory>
"""
from flightpath.parsing.hadoop.HadoopConnector import *
import sys
from flightpath.MongoConnector import *
from boto.s3.key import Key
from json import *
import pika
import shutil
import os
import boto
import tarfile

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"

errlog = open("/var/log/FPProcessing.err", "w+")
connection = pika.BlockingConnection(pika.ConnectionParameters(
        '172.31.10.27'))
channel = connection.channel()
channel.queue_declare(queue='ftpupload')

boto_conn = boto.connect_s3()
bucket = boto_conn.get_bucket('partner-logs') 

def callback(ch, method, properties, body):
    msg_dict = loads(body)

    print "Got message ", msg_dict
    """
    Validate the message.
    """ 
    if not msg_dict.has_key("tenent") or \
       not msg_dict.has_key("filename"):
        errlog.write("Invalid message received\n")     
        errlog.write(body)
        errlog.write("\n")
        errlog.flush()

    tenent = msg_dict["tenent"]
    filename = msg_dict["filename"]

    source = tenent + "/" + filename

    """
    Check if the file exists in S3 TODO:
    """ 
    file_key = bucket.get_key(source)
    if file_key is None:
        errlog.write("NOT FOUND: {0} not in S3\n".format(source))     
        errlog.flush()
        return

    """
    Check if the file has already been processed. TODO:
    """
    checkpoint = source + ".processed"
    chkpoint_key = bucket.get_key(checkpoint)
    if chkpoint_key is not None:
        errlog.write("ALREADY PROCESSED: {0} \n".format(source))     
        errlog.flush()
        return

    """
    Download the file and extract TODO:
    """ 
    destination = BAAZ_DATA_ROOT + tenent 
    if not os.path.exists(destination):
        os.makedirs(destination)
    dest_file = destination + "/" + filename
    d_file = open(dest_file, "w+")
    file_key.get_contents_to_file(d_file)

    logpath = destination + "/" + BAAZ_PROCESSING_DIRECTORY
    if os.path.exists(logpath):
        shutil.rmtree(logpath)
    os.makedirs(logpath)
    tar = None
    if dest_file.endswith(".gz"):
        tar = tarfile.open(dest_file, mode="r:gz")
    else:
        tar = tarfile.open(dest_file)
    tar.extractall(path=logpath)
    tar.close()

    errlog.write("Extracted file : {0} \n".format(dest_file))     
    errlog.flush()

    """
    Parse the data.
    """
    context = tenent
    connector = HadoopConnector({'logpath':logpath})
    mongoconn = Connector.getConnector(context)
    if mongoconn is None:
        mongoconn = MongoConnector({'host':'172.31.2.42', 'context':context, \
                                'create_db_if_not_exist':True})

    """
    Perorm Audit steps TODO.
    """
    for ev in connector.events:
        initiator = None
        for en in ev.initiators:
            initiator = en

        if ev.targets is not None:
            for en in ev.targets:
                connector.formRelation(initiator, en, 'WRITE')

        for en in ev.cohorts:
            connector.formRelation(en, initiator, 'READ')

    """
    The graph is now created.
    """ 
    for en in connector.entities:
        entity = connector.getEntity(en)
        mongoconn.updateEntity(entity)

    for rel in connector.relations:
        mongoconn.updateConsociation(rel)

    #for en in connector.entities:
    #    mongoconn.getEntity(en)

    connector.close()
    mongoconn.close()

    """
    Checkpoint the file processing.
    """
    chkpoint_key = Key(bucket)
    chkpoint_key.key = checkpoint
    chkpoint_key.set_contents_from_string("Processed")
    errlog.write("Processed file : {0} \n".format(dest_file))     
    errlog.flush()

channel.basic_consume(callback,
                      queue='ftpupload',
                      no_ack=True)

print "Going to sart consuming"
channel.start_consuming()
boto_conn.close()
print "OOps I am done"

