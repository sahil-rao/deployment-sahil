#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenant> <log Directory>
"""
from flightpath.parsing.hadoop.HadoopConnector import *
from flightpath.MongoConnector import *
from flightpath.utils import *
from json import *
from baazmath.interface.BaazCSV import *
from subprocess import Popen, PIPE
import baazmath.workflows.estimate_frequency as EF
import baazmath.workflows.create_profiles as CP
import baazmath.workflows.generate_dashboard as Dashboard
import baazmath.workflows.form_join_groups as JoinGroup
import baazmath.workflows.base_stats as BaseStats
import baazmath.workflows.compute_join_popularity as JoinPopularity
import baazmath.workflows.compute_table_popularity as TablePopularity
import baazmath.workflows.summarize_hive_exceptions as SummarizeHiveExceptions
import baazmath.workflows.form_join_supersets as FormJoinSupersets
import baazmath.workflows.form_complexity_treemap as FormComplexityTreemap
import baazmath.workflows.overall_stats as OverallStats
import baazmath.workflows.joinScore as JoinScore
import sys
import pika
import shutil
import os
import tarfile
import time
import datetime
import ConfigParser
import traceback
import logging

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"
BAAZ_MATH_LOG_FILE = "/var/log/BaazMathService.err"

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
rabbitserverIP = config.get("RabbitMQ", "server")
mongoserverIP = config.get("MongoDB", "server")
try:
   replicationGroup = config.get("MongoDB", "replicationGroup")
except:
   replicationGroup = None

mongo_url = "mongodb://" + mongoserverIP + "/"
if replicationGroup is not None:
    mongo_url = mongo_url + "?replicaset=" + replicationGroup

if os.path.isfile(BAAZ_MATH_LOG_FILE):
    timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    shutil.copy(BAAZ_MATH_LOG_FILE, BAAZ_MATH_LOG_FILE+timestr)

logging.basicConfig(filename=BAAZ_MATH_LOG_FILE,level=logging.INFO,)

#errlog = open("/var/log/BaazMathService.err", "w+")
connection = pika.BlockingConnection(pika.ConnectionParameters(
        rabbitserverIP))
channel = connection.channel()

client_params = {"x-ha-policy":"all"}
channel.queue_declare(queue='mathqueue',arguments = client_params)

def generateBaseStats(tenant):
    """
    Create a destination/processing folder.
    """
    timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    destination = "/tmp"
    #destination = '/mnt/volume1/base-stats-' + tenant + "/" + timestr 
    #if not os.path.exists(destination):
    #    os.makedirs(destination)

    dest_file_name = destination + "/test.csv"
    dest_file = open(dest_file_name, "w+")
    generateBaseStatsCSV(tenant, dest_file)
    dest_file.flush()
    dest_file.close()
   
    """
    Call Base stats generation.
    """ 

def storeResourceProfile(tenant):
    print "Going to store resource profile\n"    
    if not os.path.isfile("/tmp/test_hadoop_job_resource_share.out"):
        return

    print "Resource profile file found\n"    
    mongoconn = Connector.getConnector(tenant)
    if mongoconn is None:
        mongoconn = MongoConnector({'host':mongoserverIP, 'context':tenant, \
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
                logging.error("Entity {0} not found for storing resource profile\n".format(splits[0]))    
                continue

            logging.info("Entity {0} resource profile {1}\n".format(splits[0], splits[1]))    
            resource_doc = { "Resource_share": splits[1]}
            mongoconn.updateProfile(entity, "Resource", resource_doc)
    mongoconn.close()
            
def callback(ch, method, properties, body):

    startTime = time.time()
    msg_dict = loads(body)

    print "Analytics: Got message ", msg_dict

    """
    Validate the message.
    """ 
    if not msg_dict.has_key("tenant") or \
       not msg_dict.has_key("opcode"):
        logging.error("Invalid message received\n")     

        endTime = time.time()
        if msg_dict.has_key('uid'):
            collection.update({'uid':uid},{'$inc':{"Math.tmpcount":1, "Math.time":(endTime-startTime)}})
            decrementPendingMessage(collection, uid)

        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    tenant = msg_dict['tenant']
    opcode = msg_dict['opcode']

    uid = None
    if msg_dict.has_key('uid'):
        uid = msg_dict['uid']

        """
        Check if this is a valid UID. If it so happens that this flow has been deleted,
        then drop the message.
        """
	db = MongoClient(mongo_url)[tenant]
        if not checkUID(db, uid):
            """
            Just drain the queue.
            """
    	    ch.basic_ack(delivery_tag=method.delivery_tag)
            return
      
        collection = MongoClient(mongo_url)[tenant].uploadStats
        collection.update({'uid':uid},{'$inc':{"Math.count":1}})
    else:
        """
        We do not expect anything without UID. Discard message if not present.
        """
    	ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if opcode == "BaseStats":
        logging.info("Got Base Stats\n")     
        try:
            generateBaseStats(tenant)
            proc = Popen('mysql -ubaazdep -pbaazdep --local-infile -A HADOOP_DEV < /usr/lib/reports/queries/HADOOP/JobReports.sql', 
                         stdout=PIPE, shell=True) 
            proc.wait()
            storeResourceProfile(tenant)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.generateBaseStats.success": 1, "Math.generateBaseStats.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.generateBaseStats.success": 0, "Math.generateBaseStats.failure": 1}})
            pass

        """ Compute single table profile of SQL queries
        """
        logging.info("Generating BaseStats for {0}\n".format(tenant))     
        decrementPendingMessage(collection, uid)
        ch.basic_ack(delivery_tag=method.delivery_tag)

        endTime = time.time()
        if msg_dict.has_key('uid'):
	    #if uid has been set, the variable will be set already
            collection.update({'uid':uid},{"$inc": {"Math.time":(endTime-startTime)}})

        return
        
    if opcode == "GenerateTableProfile":
        logging.info("Got GenerateTableProfile {0}\n".format(tenant))     

        """ Compute single table profile of SQL queries
        TODO: If a single or a set of table is given then perform the
        operation only on that set.
        """
        logging.info("Generating Single Table profile for {0}\n".format(tenant))     
        entityid = None
        if "entityid" in msg_dict:
            entityid = msg_dict["entityid"]    

        try:
            CP.updateTableProfile(tenant, entityid)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.updateTableProfile.success": 1, "Math.updateTableProfile.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.updateTableProfile.success": 0, "Math.updateTableProfile.failure": 1}})
            #traceback.print_exc()
            logging.exception("Update table Profile: Tenant {0}, Entity {1}, {2}\n".format(tenant, entityid, sys.exc_info()[2]))     
        decrementPendingMessage(collection, uid)
        ch.basic_ack(delivery_tag=method.delivery_tag)

        endTime = time.time()
        if msg_dict.has_key('uid'):
	    #if uid has been set, the variable will be set already
            collection.update({'uid':uid},{"$inc": {"Math.time":(endTime-startTime)}})

        return

    if opcode == "GenerateQueryProfile":
        logging.info("Got GenerateTableProfile for {0}\n".format(tenant))     

        """ Compute single table profile of SQL queries
        """
        logging.info("Generating Single Table profile for {0}\n".format(tenant))     
        entityid = None
        if "entityid" in msg_dict:
            entityid = msg_dict["entityid"]    

	try:
            CP.updateSingleTableProfile(tenant, entityid)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.updateSingleTableProfile.success": 1, "Math.updateSingleTableProfile.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.updateSingleTableProfile.success": 0, "Math.updateSingleTableProfile.failure": 1}})
            logging.exception("Single table Profile: Tenant {0}, Entity {1}, {2}\n".format(tenant, entityid, sys.exc_info()[2]))     
 
        try:
            Dashboard.run_workflow(tenant, None, None)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.Dashboard.success": 1, "Math.Dashboard.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.Dashboard.success": 0, "Math.Dashboard.failure": 1}})
            logging.exception("Dashboard: Tenant {0}, Entity {1}, {2}\n".format(tenant, entityid, sys.exc_info()[2]))     
 
        logging.info("Going to form Join Groups {0}\n".format(tenant))     
        try:
            JoinGroup.formJoinGroup(tenant, entityid)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.JoinGroup.success": 1, "Math.JoinGroup.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.JoinGroup.success": 0, "Math.JoinGroup.failure": 1}})
            logging.exception("Join Group: Tenant {0}, Entity {1}, {2}\n".format(tenant, entityid, sys.exc_info()[2]))     

        try:
            BaseStats.run_workflow(tenant, None, None)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.BaseStats.success": 1, "Math.BaseStats.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.BaseStats.success": 0, "Math.BaseStats.failure": 1}})
            logging.exception("Base Stats: Tenant {0}, Entity {1}, {2}\n".format(tenant, entityid, sys.exc_info()[2]))     

        try:
            JoinPopularity.run_workflow(tenant, None, None)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.JoinPopularity.success": 1, "Math.JoinPopularity.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.JoinPopularity.success": 0, "Math.JoinPopularity.failure": 1}})
            logging.exception("Join Popularity: Tenant {0}, Entity {1}, {2}\n".format(tenant, entityid, sys.exc_info()[2]))     

        try:
            TablePopularity.run_workflow(tenant, None, None)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.TablePopularity.success": 1, "Math.TablePopularity.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.TablePopularity.success": 0, "Math.TablePopularity.failure": 1}})
            logging.exception("Table Popularity: Tenant {0}, Entity {1}, {2}\n".format(tenant, entityid, sys.exc_info()[2]))     

        try:
            SummarizeHiveExceptions.run_workflow(tenant, None, None)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.SummarizeHiveExceptions.success": 1, "Math.SummarizeHiveExceptions.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.SummarizeHiveExceptions.success": 0, "Math.SummarizeHiveExceptions.failure": 1}})
            logging.exception("Summarize Hive Exceptions: Tenant {0}, Entity {1}, {2}\n".format(tenant, entityid, sys.exc_info()[2]))     

        try:
            FormJoinSupersets.buildJoinSuperSets(tenant)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.FormJoinSupersets.success": 1, "Math.FormJoinSupersets.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.FormJoinSupersets.success": 0, "Math.FormJoinSupersets.failure": 1}})
            logging.exception("Build Join Supersets: Tenant {0}\n".format(tenant))

        try:
            FormComplexityTreemap.buildComplexityTreemap(tenant)
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.FormComplexityTreemap.success": 1, "Math.FormComplexityTreemap.failure": 0}})
        except:
	    if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.FormComplexityTreemap.success": 0, "Math.FormComplexityTreemap.failure": 1}})
            logging.exception("Form Complexity Treemap: Tenant {0}\n".format(tenant))

        try:
            OverallStats.updateOrgs()
            if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.OverallStats.success": 1, "Math.OverallStats.failure": 0}})
        except:
            if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.OverallStats.success": 0, "Math.OverallStats.failure": 1}})
            logging.exception("Overall Stats: Tenant {0}\n".format(tenant))

        try:
            JoinScore.compute_join_score(tenant)
            if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.OverallStats.success": 1, "Math.OverallStats.failure": 0}})
        except:
            if msg_dict.has_key('uid'):
                collection.update({'uid':uid},{"$inc": {"Math.OverallStats.success": 0, "Math.OverallStats.failure": 1}})
            logging.exception("Join Score: Tenant {0}\n".format(tenant))

        endTime = time.time()
        if msg_dict.has_key('uid'):
	    #if uid has been set, the variable will be set already
            collection.update({'uid':uid},{"$inc": {"Math.time":(endTime-startTime)}})

        decrementPendingMessage(collection, uid)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        if not msg_dict.has_key("job_instances"):
            logging.error("Invalid message received\n")     
            decrementPendingMessage(collection, uid)
            ch.basic_ack(delivery_tag=method.delivery_tag)

            endTime = time.time()
            if msg_dict.has_key('uid'):
	        #if uid has been set, the variable will be set already
                collection.update({'uid':uid},{"$inc": {"Math.time":(endTime-startTime)}})
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
            destination = '/mnt/volume1/' + tenant + "/" + timestr 
            if not os.path.exists(destination):
                os.makedirs(destination)

            dest_file_name = destination + "/input.csv"

            prog_id = inst["program_id"] 
            logging.info("Event received for {0}, entity {1}\n".format(tenant, prog_id))     
            dest_file = open(dest_file_name, "w+")
            generateCSV1Header(prog_id, dest_file)
            generateCSV1(tenant, prog_id, None, dest_file)
            dest_file.flush()
	    dest_file.close()
	    try:
                EF.run_workflow(tenant, dest_file_name, destination)
            except:
                logging.exception("Estimate Frequency: Tenant {0}, Entity {1}, {2}\n".format(tenant, prog_id, sys.exc_info()[2]))     
    except:
        logging.exception("{0}, Entity {1}, {2}\n".format(tenant, prog_id, sys.exc_info()[2]))     
            

    logging.info("Event Processing Complete")     
    decrementPendingMessage(collection, uid)
    ch.basic_ack(delivery_tag=method.delivery_tag)

    endTime = time.time()
    if msg_dict.has_key('uid'):
	#if uid has been set, the variable will be set already
        collection.update({'uid':uid},{"$inc": {"Math.time":(endTime-startTime)}})


channel.basic_consume(callback,
                      queue='mathqueue')

print "Going to sart consuming"
channel.start_consuming()
print "OOps I am done"

