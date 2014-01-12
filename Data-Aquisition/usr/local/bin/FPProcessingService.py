#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenant> <log Directory>
"""
#from flightpath.parsing.hadoop.HadoopConnector import *
#from flightpath.parsing.SQL.SQLScriptConnector import *
from flightpath.parsing.ParseDemux import *
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
channel1 = connection.channel()
channel1.queue_declare(queue='mathqueue')
channel2 = connection.channel()
channel2.queue_declare(queue='compilerqueue')

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

    tenant = msg_dict["tenent"]
    filename = msg_dict["filename"]

    source = tenant + "/" + filename

    """
    Check if the file exists in S3. 
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
    dest_file = BAAZ_DATA_ROOT + tenant + "/" + filename
    destination = os.path.dirname(dest_file)
    print destination
    if not os.path.exists(destination):
        os.makedirs(destination)

    d_file = open(dest_file, "w+")
    file_key.get_contents_to_file(d_file)
    d_file.close()

    logpath = destination + "/" + BAAZ_PROCESSING_DIRECTORY
    if os.path.exists(logpath):
        shutil.rmtree(logpath)
    os.makedirs(logpath)
    tar = None
    if dest_file.endswith(".gz"):
        tar = tarfile.open(dest_file, mode="r:gz")
        tar.extractall(path=logpath)
        tar.close()
    elif dest_file.endswith(".tar"):
        tar = tarfile.open(dest_file)
        tar.extractall(path=logpath)
        tar.close()
    else:
        shutil.copy(dest_file, logpath) 

    errlog.write("Extracted file : {0} \n".format(dest_file))     
    errlog.flush()

    """
    Parse the data.
    """
    context = tenant
    mongoconn = Connector.getConnector(context)
    if mongoconn is None:
        mongoconn = MongoConnector({'host':'172.31.2.42', 'context':context, \
                                'create_db_if_not_exist':True})

    parseDir(tenant, logpath, mongoconn)

    """
    Checkpoint the file processing.
    """
    chkpoint_key = Key(bucket)
    chkpoint_key.key = checkpoint
    chkpoint_key.set_contents_from_string("Processed")
    errlog.write("Processed file : {0} \n".format(dest_file))     
    errlog.flush()

    for en in mongoconn.entities:
        entity = mongoconn.getEntity(en)
        if not entity.etype == 'HADOOP_JOB': 
            continue

        jinst_dict = {'entity_id':entity.eid} 
        prog_type = ""
        if entity.instances[0].config_data.has_key("hive.query.string"):
            jinst_dict['program_type'] = "Hive"
            jinst_dict['query'] = entity.name
        elif entity.instances[0].config_data.has_key("pig.script.features"):
            jinst_dict['program_type'] = "Pig"
            jinst_dict['pig_features'] = int(entity.instances[0].config_data['pig.script.features'])
        else:
    	    errlog.write("Progname found {0}\n".format(entity.name))
    	    errlog.flush()
	    continue

	compiler_msg = {'tenant':tenant, 'job_instances':[jinst_dict]}
    	message = dumps(compiler_msg)
    	channel2.basic_publish(exchange='',
                      routing_key='compilerqueue',
                      body=message)
    	errlog.write("Published Compiler Message {0}\n".format(message))
    	errlog.flush()

    for en in mongoconn.entities:
        entity = mongoconn.getEntity(en)
        if not entity.etype == 'SQL_QUERY': 
            continue

        jinst_dict = {'entity_id':entity.eid} 
        jinst_dict['program_type'] = "SQL"
        jinst_dict['query'] = entity.name
	compiler_msg = {'tenant':tenant, 'job_instances':[jinst_dict]}
    	message = dumps(compiler_msg)
    	channel2.basic_publish(exchange='',
                      routing_key='compilerqueue',
                      body=message)
    	errlog.write("Published Compiler Message {0}\n".format(message))
    	errlog.flush()

    math_msg = {'tenant':tenant, 'opcode':"Frequency-Estimation"}
    job_insts = {}
    for en in mongoconn.entities:
        entity = mongoconn.getEntity(en)
        if not entity.etype == 'HADOOP_JOB':
            continue
        job_insts[entity.eid] = {'program_id':entity.eid}
    math_msg['job_instances'] = job_insts.values()
    message = dumps(math_msg)
    channel1.basic_publish(exchange='',
                      routing_key='mathqueue',
                      body=message)

    errlog.write("Published Message {0}\n".format(message))
    errlog.flush()

    math_msg = {'tenant':tenant, 'opcode':"BaseStats"}
    message = dumps(math_msg)
    channel1.basic_publish(exchange='',
                      routing_key='mathqueue',
                      body=message)
    errlog.write("Published Message {0}\n".format(message))
    errlog.flush()

    mongoconn.close()

channel.basic_consume(callback,
                      queue='ftpupload',
                      no_ack=True)

print "Going to sart consuming"
channel.start_consuming()
boto_conn.close()
print "OOps I am done"

