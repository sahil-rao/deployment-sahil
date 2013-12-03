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


BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"

errlog = open("/var/log/BaazCompileService.err", "w+")
connection = pika.BlockingConnection(pika.ConnectionParameters(
        '172.31.10.27'))
channel = connection.channel()
channel.queue_declare(queue='compilerqueue')

    
def callback(ch, method, properties, body):
    msg_dict = loads(body)

    print "Got message ", msg_dict

    """
    Validate the message.
    """ 
    if not msg_dict.has_key("tenent") or \
       not msg_dict.has_key("job_instances"):
        errlog.write("Invalid message received\n")     
        errlog.write(body)
        errlog.write("\n")
        errlog.flush()

    tenent = msg_dict["tenent"]
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
    	destination = '/mnt/volume1/compile-' + tenent + "/" + timestr 
    	if not os.path.exists(destination):
        	os.makedirs(destination)

    	dest_file_name = destination + "/input.query"

        prog_id = inst["entity_id"] 
        query = inst["query"] 
        #inst_id = inst["inst_id"] 
        #if prog_collector.has_key(prog_id):
        #    prog_collector[prog_id].append(inst_id)
        #else:
        #    prog_collector[prog_id] = [inst_id]
        #counter = counter + 1
        errlog.write("Event received for {0}, entity {1}\n".format(tenent, prog_id))     
        errlog.flush()
        dest_file = open(dest_file_name, "w+")
        dest_file.write(query)
        dest_file.flush()
	dest_file.close()
	try:
            """
                Call the process here
            """ 
            proc = Popen('java com.baaz.hive.ast.BaazHiveQueryAnalyzer {0}'.format(dest_file_name),\
                         stdout=PIPE, env=dict(os.environ, \
                        CLASSPATH='/usr/lib/BAAZ_COMPILER/bin:/usr/lib/hive/lib/antlr-runtime-3.4.jar:/usr/lib/hive/lib/avro-1.7.1.jar:/usr/lib/hive/lib/avro-mapred-1.7.1.jar:/usr/lib/hive/lib/commons-cli-1.2.jar:/usr/lib/hive/lib/commons-codec-1.4.jar:/usr/lib/hive/lib/commons-collections-3.2.1.jar:/usr/lib/hive/lib/commons-compress-1.4.1.jar:/usr/lib/hive/lib/commons-configuration-1.6.jar:/usr/lib/hive/lib/commons-dbcp-1.4.jar:/usr/lib/hive/lib/commons-io-2.4.jar:/usr/lib/hive/lib/commons-lang-2.4.jar:/usr/lib/hive/lib/commons-logging-1.0.4.jar:/usr/lib/hive/lib/commons-logging-api-1.0.4.jar:/usr/lib/hive/lib/commons-pool-1.5.4.jar:/usr/lib/hive/lib/datanucleus-connectionpool-2.0.3.jar:/usr/lib/hive/lib/datanucleus-core-2.0.3.jar:/usr/lib/hive/lib/datanucleus-enhancer-2.0.3.jar:/usr/lib/hive/lib/datanucleus-rdbms-2.0.3.jar:/usr/lib/hive/lib/derby-10.4.2.0.jar:/usr/lib/hive/lib/guava-11.0.2.jar:/usr/lib/hive/lib/hbase-0.94.6.1.jar:/usr/lib/hive/lib/hbase-0.94.6.1-tests.jar:/usr/lib/hive/lib/hive-beeline-0.11.0.jar:/usr/lib/hive/lib/hive-cli-0.11.0.jar:/usr/lib/hive/lib/hive-common-0.11.0.jar:/usr/lib/hive/lib/hive-contrib-0.11.0.jar:/usr/lib/hive/lib/hive-exec-0.11.0.jar:/usr/lib/hive/lib/hive-hbase-handler-0.11.0.jar:/usr/lib/hive/lib/hive-hwi-0.11.0.jar:/usr/lib/hive/lib/hive-jdbc-0.11.0.jar:/usr/lib/hive/lib/hive-metastore-0.11.0.jar:/usr/lib/hive/lib/hive-serde-0.11.0.jar:/usr/lib/hive/lib/hive-service-0.11.0.jar:/usr/lib/hive/lib/hive-shims-0.11.0.jar:/usr/lib/hive/lib/jackson-core-asl-1.8.8.jar:/usr/lib/hive/lib/jackson-jaxrs-1.8.8.jar:/usr/lib/hive/lib/jackson-mapper-asl-1.8.8.jar:/usr/lib/hive/lib/jackson-xc-1.8.8.jar:/usr/lib/hive/lib/JavaEWAH-0.3.2.jar:/usr/lib/hive/lib/javolution-5.5.1.jar:/usr/lib/hive/lib/jdo2-api-2.3-ec.jar:/usr/lib/hive/lib/jetty-6.1.26.jar:/usr/lib/hive/lib/jetty-util-6.1.26.jar:/usr/lib/hive/lib/jline-0.9.94.jar:/usr/lib/hive/lib/json-20090211.jar:/usr/lib/hive/lib/libfb303-0.9.0.jar:/usr/lib/hive/lib/libthrift-0.9.0.jar:/usr/lib/hive/lib/log4j-1.2.16.jar:/usr/lib/hive/lib/maven-ant-tasks-2.1.3.jar:/usr/lib/hive/lib/metrics-core-2.1.2.jar:/usr/lib/hive/lib/protobuf-java-2.4.1.jar:/usr/lib/hive/lib/servlet-api-2.5-20081211.jar:/usr/lib/hive/lib/slf4j-api-1.6.1.jar:/usr/lib/hive/lib/slf4j-log4j12-1.6.1.jar:/usr/lib/hive/lib/snappy-0.2.jar:/usr/lib/hive/lib/ST4-4.0.4.jar:/usr/lib/hive/lib/tempus-fugit-1.1.jar:/usr/lib/hive/lib/xz-1.0.jar:/usr/lib/hive/lib/zookeeper-3.4.3.jar')) 
            for line in proc.stdout:
                errlog.write(line)
                errlog.flush()
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
                      queue='compilerqueue',
                      no_ack=True)

print "Going to sart consuming"
channel.start_consuming()
print "OOps I am done"

