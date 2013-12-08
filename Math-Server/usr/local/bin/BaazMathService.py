#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenent> <log Directory>
"""
from flightpath.parsing.hadoop.HadoopConnector import *
from flightpath.MongoConnector import *
from json import *
from baazmath.interface.BaazCSV import *
from subprocess import Popen, PIPE
import baazmath.workflows.estimate_frequency as EF
import sys
import pika
import shutil
import os
import tarfile
import time
import datetime


BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"

errlog = open("/var/log/BaazMathService.err", "w+")
connection = pika.BlockingConnection(pika.ConnectionParameters(
        '172.31.10.27'))
channel = connection.channel()
channel.queue_declare(queue='mathqueue')

def generateBaseStats(tenent):
    """
    Create a destination/processing folder.
    """
    timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    destination = "/tmp"
    #destination = '/mnt/volume1/base-stats-' + tenent + "/" + timestr 
    #if not os.path.exists(destination):
    #    os.makedirs(destination)

    dest_file_name = destination + "/test.csv"
    dest_file = open(dest_file_name, "w+")
    generateBaseStatsCSV(tenent, dest_file)
    dest_file.flush()
    dest_file.close()
   
    """
    Call Base stats generation.
    """ 

def storeResourceProfile(tenent):
    print "Going to store resource profile\n"    
    if not os.path.isfile("/tmp/test_hadoop_job_resource_share.out"):
        return

    print "Resource profile file found\n"    
    mongoconn = Connector.getConnector(tenent)
    if mongoconn is None:
        mongoconn = MongoConnector({'host':'172.31.2.42', 'context':tenent, \
                                    'create_db_if_not_exist':True})

    with open("/tmp/test_hadoop_job_resource_share.out", "r") as resource_file:
        for line in resource_file:
            print "Resource profile line :", line    
            if line.strip().startswith("Entity"):
                continue

            splits = line.strip().split()
            if not len(splits) == 2:
                continue

            entity = mongoconn.getEntity(splits[0])
            if entity is None:
                errlog.write("Entity {0} not found for storing resource profile\n".format(splits[0]))    
                errlog.flush()
                continue

            errlog.write("Entity {0} resource profile {1}\n".format(splits[0], splits[1]))    
            errlog.flush()
            resource_doc = { "Resource_share": splits[1]}
            mongoconn.updateProfile(entity, "Resource", resource_doc)
    mongoconn.close()
            
def callback(ch, method, properties, body):
    msg_dict = loads(body)

    print "Analytics: Got message ", msg_dict

    """
    Validate the message.
    """ 
    if not msg_dict.has_key("tenent") or \
       not msg_dict.has_key("opcode"):
        errlog.write("Invalid message received\n")     
        errlog.write(body)
        errlog.write("\n")
        errlog.flush()
        return

    tenent = msg_dict['tenent']
    opcode = msg_dict['opcode']
    if opcode == "BaseStats":
        generateBaseStats(tenent)
        proc = Popen('mysql -ubaazdep -pbaazdep --local-infile -A HADOOP_DEV < /usr/lib/reports/queries/HADOOP/JobReports.sql', 
                     stdout=PIPE, shell=True) 
        storeResourceProfile(tenent)
        return
        
    if not msg_dict.has_key("job_instances"):
        errlog.write("Invalid message received\n")     
        errlog.write(body)
        errlog.write("\n")
        errlog.flush()
        return

    instances = msg_dict["job_instances"]

    """
    Generate the CSV from the job instances.
    """
    counter = 0
    for inst in instances:
    	"""
    	Create a destination/processing folder.
    	"""
    	timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    	destination = '/mnt/volume1/' + tenent + "/" + timestr 
    	if not os.path.exists(destination):
        	os.makedirs(destination)

    	dest_file_name = destination + "/input.csv"

        prog_id = inst["program_id"] 
        #inst_id = inst["inst_id"] 
        #if prog_collector.has_key(prog_id):
        #    prog_collector[prog_id].append(inst_id)
        #else:
        #    prog_collector[prog_id] = [inst_id]
        #counter = counter + 1
        errlog.write("Event received for {0}, entity {1}\n".format(tenent, prog_id))     
        errlog.flush()
        dest_file = open(dest_file_name, "w+")
        generateCSV1Header(prog_id, dest_file)
        generateCSV1(tenent, prog_id, None, dest_file)
        dest_file.flush()
	dest_file.close()
	try:
            EF.run_workflow(tenent, dest_file_name, destination)
        except:
            errlog.write("Tenent {0}, Entity {1}, {2}\n".format(tenent, prog_id, sys.exc_info()[2]))     
            errlog.flush()
            

    #errlog.write("Event received for {0}, {1} total runs with {1} unique jobs \n".format\
    #                (tenent, len(prog_collector.keys()), counter))     

    #for prog_id in prog_collector:
    #    dest_file = open(dest_file_name, "w+")
    #    generateCSV1Header(prog_id, dest_file)
    #    for inst in prog_collector[prog_id]:
    #        generateCSV1Header(prog_id, inst, dest_file)
        
    #    """
    #    Now start the analytics module.
    #    """
    #    dest_file.close()

    errlog.write("Event Processing Complete")     
    errlog.flush()

channel.basic_consume(callback,
                      queue='mathqueue',
                      no_ack=True)

print "Going to sart consuming"
channel.start_consuming()
print "OOps I am done"

