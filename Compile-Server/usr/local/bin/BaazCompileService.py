#!/usr/bin/python

"""
Compile Service:
"""
from flightpath import cluster_config
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from flightpath.ScaleModeConnector import *
from flightpath.FilterModeConnector import *
from flightpath.services.RabbitMQConnectionManager import *
from flightpath.services.RotatingS3FileHandler import *
from baazmath.workflows.hbase_analytics import *
from flightpath.utils import *
from flightpath.Provenance import getMongoServer
from flightpath.services.mq_template import *
import flightpath.thriftclient.compilerthriftclient as tclient

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
import logging
import socket
import pprint
from rlog import RedisHandler

BAAZ_DATA_ROOT="/mnt/volume1/"
BAAZ_PROCESSING_DIRECTORY="processing"
BAAZ_COMPILER_LOG_FILE = "/var/log/cloudera/navopt/BaazCompileService.err"

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
rabbitserverIP = config.get("RabbitMQ", "server")

usingAWS = config.getboolean("mode", "usingAWS")
mode = cluster_config.get_cluster_mode()
logging_level = logging.INFO
if mode == "development":
    logging_level = logging.INFO

if usingAWS:
    from boto.s3.key import Key
    import boto
    from datadog import initialize, statsd

CLUSTER_NAME = config.get("ApplicationConfig", "clusterName")

if CLUSTER_NAME is not None:
    bucket_location = CLUSTER_NAME

"""
For VM there is not S3 connectivity. Save the logs with a timestamp.
At some point we should move to using a log rotate handler in the VM.
"""
if not usingAWS:
    if os.path.isfile(BAAZ_COMPILER_LOG_FILE):
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        shutil.copy(BAAZ_COMPILER_LOG_FILE, BAAZ_COMPILER_LOG_FILE+timestr)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',filename=BAAZ_COMPILER_LOG_FILE,level=logging_level,datefmt='%m/%d/%Y %I:%M:%S %p')
es_logger = logging.getLogger('elasticsearch')
es_logger.propagate = False
es_logger.setLevel(logging.WARN)

"""
In AWS use S3 log rotate to save the log files.
"""
if usingAWS:
    boto_conn = boto.connect_s3()
    log_bucket = boto_conn.get_bucket('xplain-servicelogs')
    logging.getLogger().addHandler(RotatingS3FileHandler(BAAZ_COMPILER_LOG_FILE, maxBytes=104857600, backupCount=5, s3bucket=log_bucket))
    redis_host = config.get("RedisLog", "server")
    if redis_host:
        logging.getLogger().addHandler(RedisHandler('logstash', level=logging_level, host=redis_host, port=6379))

COMPILER_MODULES='/usr/lib/baaz_compiler'

dirList=os.listdir(COMPILER_MODULES)
classpath = ""
for fname in dirList:
    fullpath = os.path.join(COMPILER_MODULES, fname)
    if not os.path.isfile(fullpath):
        continue
    if not fullpath.lower().endswith(".jar"):
        continue
    classpath = classpath + fullpath + ":"

#HIVE_MODULES='/usr/lib/hive/lib'
#dirList=os.listdir(HIVE_MODULES)
#for fname in dirList:
#    fullpath = os.path.join(HIVE_MODULES, fname)
#    if not os.path.isfile(fullpath):
#        continue
#    if not fullpath.lower().endswith(".jar"):
#        continue
#    classpath = classpath + fullpath + ":"

table_regex = re.compile("([\w]*)\.([\w]*)")
myip = socket.gethostbyname(socket.gethostname())


class Compiler_Context:
    def __init__(self):
        pass

def end_of_phase_callback(params, current_phase):
    if current_phase > 1:
        logging.info("Attempted end of phase callback, but current phase > 1")
        return

    logging.info("Changing processing Phase")

    msg_dict = {'tenant':params['tenant'], 'opcode':"PhaseTwoAnalysis"}
    msg_dict['uid'] = params['uid']
    message = dumps(msg_dict)
    params['connection'].publish(params['channel'],'',params['queuename'],message)
    return

def processColumns(columnset, mongoconn, redis_conn, tenant, uid, entity, clog):
    tableCount = 0
    table_entity = None
    for column_entry in columnset:
        if "tableName" not in column_entry:
            continue

        tablename = column_entry["tableName"].replace('"', '')
        columnname = column_entry["columnName"].replace('"', '')
        table_entity = mongoconn.getEntityByName(tablename)

        column_entity_name = tablename.lower() + "." + columnname.lower()
        column_entity = mongoconn.getEntityByName(column_entity_name)

        if table_entity is None:
            clog.debug("Creating table entity for {0} position 6\n".format(tablename))
            eid = IdentityService.getNewIdentity(tenant, True)
            table_entity = mongoconn.addEn(eid, tablename, tenant,\
                    EntityType.SQL_TABLE, {"uid" : uid}, None)
            if eid == table_entity.eid:
                #create Elastic search index
                sendToElastic(connection1, redis_conn, tenant, uid,
                              table_entity, tablename, EntityType.SQL_TABLE)
                redis_conn.createEntityProfile(table_entity.eid, "SQL_TABLE")
                tableCount = tableCount + 1

        if column_entity is None:
            clog.debug("Creating Column entity for {0}\n".format(column_entity_name))
            eid = IdentityService.getNewIdentity(tenant, True)
            column_entry['tableEid'] = table_entity.eid
            column_entry["uid"] = uid
            column_entity = mongoconn.addEn(eid, column_entity_name, tenant,\
                            EntityType.SQL_TABLE_COLUMN, column_entry, None)

            if column_entity.eid == eid:
                #create Elastic search index
                sendToElastic(connection1, redis_conn, tenant, uid,
                              column_entity, column_entity_name, EntityType.SQL_TABLE_COLUMN)
                clog.debug("TABLE_COLUMN Relation between {0} {1}\n".format(table_entity.eid, column_entity.eid))
                redis_conn.createEntityProfile(column_entity.eid, "SQL_TABLE_COLUMN")
                redis_conn.createRelationship(table_entity.eid, column_entity.eid, "TABLE_COLUMN")
                redis_conn.setRelationship(table_entity.eid, column_entity.eid,
                                           "TABLE_COLUMN", {'weight':1, "columnName":column_entity.columnName})
        else:
            eid = column_entity.eid
            if 'dataType' in column_entry and 'primaryKey' in column_entry and 'foreignKey' in column_entry:
                mongoconn.db.entities.update({'eid':eid}, {'$set': column_entry})


    """
    Create relationships.
    """
    if entity is not None and table_entity is not None:
        redis_conn.createRelationship(entity.eid, table_entity.eid, "CREATE")
        clog.debug(" CREATE Relation between {0} {1}\n".format(entity.eid, table_entity.eid))
        redis_conn.incrEntityCounterWithSecKey(table_entity.eid,
                                               "instance_count",
                                               sec_key=table_entity.name,
                                               sort=True, incrBy=1)
    return [0, tableCount]

def processTableSet(tableset, mongoconn, redis_conn, tenant, uid, entity, isinput, context, clog, tableEidList=None, hive_success=0):
    dbCount = 0
    tableCount = 0
    if tableset is None or len(tableset) == 0:
        return [dbCount, tableCount]

    outmost_query = None
    queue_len = len(context.queue)
    if queue_len > 0:
        if context.queue[0]['etype'] == EntityType.SQL_STORED_PROCEDURE:
            if queue_len > 1:
                outmost_query = context.queue[1]['eid']
        elif context.queue[0]['etype'] == EntityType.SQL_QUERY:
            outmost_query = context.queue[0]['eid']

    endict = {"uid" : uid}
    #mongoconn.startBatchUpdate()
    for tableentry in tableset:
        database_name = None
        entryname = tableentry["TableName"].lower()
        entryname = entryname.replace('"', '')
        matches = table_regex.search(entryname)
        if matches is not None:
            database_name = matches.group(1)
            tablename = matches.group(2)
        else:
            tablename = entryname

        """
        Create the Table Entity first if it does not already exist.
        """
        table_entity = mongoconn.getEntityByName(tablename)
        if table_entity is None:
            clog.debug("Creating table entity for {0} position 5\n".format(tablename))
            eid = IdentityService.getNewIdentity(tenant, True)
            table_entity = mongoconn.addEn(eid, tablename, tenant,\
                      EntityType.SQL_TABLE, endict, None)

            if eid == table_entity.eid:
                #create Elastic search index
                sendToElastic(connection1, redis_conn, tenant, uid,
                              table_entity, tablename, EntityType.SQL_TABLE)
                redis_conn.createEntityProfile(table_entity.eid, "SQL_TABLE")
                '''
                Incrementing by 0 to set the secondary sort key.
                This way it does not need to be passed in later.
                '''
                redis_conn.incrEntityCounterWithSecKey(table_entity.eid,
                                                       "instance_count",
                                                       sec_key=table_entity.name,
                                                       sort=True, incrBy=0)
                tableCount = tableCount + 1

        tableEidList.add(table_entity.eid)

        """
        If the database is found then create database Entity if it does not already exist.
        """
        database_entity = None
        if database_name is not None:
            database_entity = mongoconn.getEntityByName(database_name)
            if database_entity is None:
                clog.debug("Creating database entity for {0}\n".format(database_name))
                eid = IdentityService.getNewIdentity(tenant, True)
                mongoconn.addEn(eid, database_name, tenant,\
                          EntityType.SQL_DATABASE, endict, None)
                database_entity = mongoconn.getEntityByName(database_name)
                #create Elastic search index
                sendToElastic(connection1, redis_conn, tenant, uid,
                              database_entity, database_name, EntityType.SQL_DATABASE)
                dbCount = dbCount + 1

        """
        Create relations, first between tables and query
            Then between query and database, table and database
        """
        if entity is not None and table_entity is not None:
            if isinput:

                if outmost_query is not None and outmost_query != entity.eid:
                    redis_conn.createRelationship(table_entity.eid, entity.eid, "SUBQUERYREAD")
                    redis_conn.setRelationship(table_entity.eid, entity.eid, "SUBQUERYREAD", {"hive_success":hive_success})
                    clog.debug("SUBQUERYREAD Relation between {0} {1} position 1\n".format(table_entity.eid, entity.eid))

                else:
                    redis_conn.createRelationship(table_entity.eid, entity.eid, "READ")
                    redis_conn.setRelationship(table_entity.eid, entity.eid, "READ", {"hive_success":hive_success})
                    clog.debug("READ Relation between {0} {1} position 2\n".format(table_entity.eid, entity.eid))
            else:
                if outmost_query is not None and outmost_query != entity.eid:
                    redis_conn.createRelationship(entity.eid, table_entity.eid, "SUBQUERYWRITE")
                    redis_conn.setRelationship(entity.eid, table_entity.eid, "SUBQUERYWRITE", {"hive_success":hive_success})
                    clog.debug("SUBQUERYWRITE Relation between {0} {1} position 3\n".format(entity.eid, table_entity.eid))

                else:
                    redis_conn.createRelationship(entity.eid,table_entity.eid, "WRITE")
                    redis_conn.setRelationship(entity.eid,table_entity.eid, "WRITE", {"hive_success":hive_success})
                    clog.debug("WRITE Relation between {0} {1} position 4\n".format(entity.eid,table_entity.eid))

            '''
            Makes sure to follow context for the table and outmost query.
            '''
            if table_entity.eid is not None:
                if isinput:
                    for query in context.queue:
                        if query['etype'] == EntityType.SQL_QUERY:
                            redis_conn.createRelationship(table_entity.eid, query['eid'], "READ")
                            redis_conn.incrRelationshipCounter(table_entity.eid, query['eid'], "READ", "instance_count", incrBy=1)
                        elif query['etype'] == EntityType.SQL_SUBQUERY:
                            redis_conn.createRelationship(table_entity.eid, query['eid'], "SUBQUERYREAD")
                            redis_conn.incrRelationshipCounter(table_entity.eid, query['eid'], "SUBQUERYREAD", "instance_count", incrBy=1)
                        elif query['etype'] == EntityType.SQL_STORED_PROCEDURE:
                            redis_conn.createRelationship(table_entity.eid, query['eid'], "STOREDPROCEDUREREAD")
                            redis_conn.incrRelationshipCounter(table_entity.eid, query['eid'], "STOREDPROCEDUREREAD", "instance_count", incrBy=1)
                        elif query['etype'] == EntityType.SQL_INLINE_VIEW:
                            if 'view_entity_id' in query:
                                redis_conn.createRelationship(query['view_entity_id'],
                                                              table_entity.eid, "IVIEW_TABLE")
                else:
                    for query in context.queue:
                        if query['etype'] == EntityType.SQL_QUERY:
                            redis_conn.createRelationship(query['eid'], table_entity.eid, "WRITE")
                            redis_conn.incrRelationshipCounter(query['eid'], table_entity.eid, "WRITE", "instance_count", incrBy=1)
                        elif query['etype'] == EntityType.SQL_SUBQUERY:
                            redis_conn.createRelationship(query['eid'], table_entity.eid, "SUBQUERYWRITE")
                            redis_conn.incrRelationshipCounter(query['eid'], table_entity.eid, "SUBQUERYWRITE", "instance_count", incrBy=1)
                        elif query['etype'] == EntityType.SQL_STORED_PROCEDURE:
                            redis_conn.createRelationship(query['eid'], table_entity.eid, "STOREDPROCEDUREWRITE")
                            redis_conn.incrRelationshipCounter(query['eid'], table_entity.eid, "STOREDPROCEDUREWRITE", "instance_count", incrBy=1)
                        elif query['etype'] == EntityType.SQL_INLINE_VIEW:
                            if 'view_entity_id' in query:
                                redis_conn.createRelationship(query['view_entity_id'],
                                                              table_entity.eid, "IVIEW_TABLE")

                context.tables.append(table_entity.eid)

        if database_entity is not None:
            if table_entity is not None:
                redis_conn.createRelationship(database_entity.eid, table_entity.eid, "CONTAINS")
                clog.debug("Relation between {0} {1} position 5\n".format(database_entity.eid, table_entity.eid))

            """ Note this assumes that formRelations is idempotent
            """
            if entity is not None:
                redis_conn.createRelationship(database_entity.eid, entity.eid, "CONTAINS")
                clog.debug("Relation between {0} {1} position 6\n".format(database_entity.eid, entity.eid))

    return [dbCount, tableCount]

def getTableName(tableentry):
    database_name = None
    tablename = None
    entryname = tableentry["TableName"].lower()
    entryname = entryname.replace('"', '')
    matches = table_regex.search(entryname)

    if matches is not None:
        database_name = matches.group(1)
        tablename = matches.group(2)
    else:
        tablename = entryname
        if "databaseName" in tableentry:
            database_name = tableentry["databaseName"].lower()
    return tablename

def processCreateViewOrInlineView(viewName, mongoconn, redis_conn, entity_col,
                    tenant, uid, entity, context, inputTableList, clog,
                    tableEidList=None, hive_success=0, viewAlias=None,
                    current_queue_entry=None):
    dbCount = 0
    tableCount = 0
    table_alias = None
    if viewName is None:
        return [dbCount, tableCount]

    outmost_query = None
    queue_len = len(context.queue)
    if queue_len > 0:
        if context.queue[0]['etype'] == EntityType.SQL_STORED_PROCEDURE:
            if queue_len > 1:
                outmost_query = context.queue[1]['eid']
        elif context.queue[0]['etype'] == EntityType.SQL_QUERY:
            outmost_query = context.queue[0]['eid']

    if viewAlias is not None:
            endict = {"uid" : uid, "profile" : { "is_inline_view" : True}}
    else:
        endict = {"uid" : uid, "profile" : { "is_view" : True}}
    database_name = None
    entryname = viewName.lower()
    entryname = entryname.replace('"', '')
    matches = table_regex.search(entryname)

    if matches is not None:
        database_name = matches.group(1)
        viewname = matches.group(2)
    else:
        viewname = entryname

    """
    Create the Table Entity first if it does not already exist.
    """
    view_entity = mongoconn.getEntityByName(viewname)
    if view_entity is None:
        clog.debug("Creating table entity for view {0}\n".format(viewname))
        eid = IdentityService.getNewIdentity(tenant, True)
        endict['display_name'] = "InlineView" + eid
        view_entity = mongoconn.addEn(eid, viewname, tenant,\
                  EntityType.SQL_TABLE, endict, None)

        if eid == view_entity.eid:
            #create Elastic search index
            sendToElastic(connection1, redis_conn, tenant, uid,
                          view_entity, viewname, EntityType.SQL_TABLE)
            redis_conn.createEntityProfile(view_entity.eid, "SQL_TABLE")
            #incrementing by 0 so secondary sort_key is set.
            redis_conn.incrEntityCounterWithSecKey(view_entity.eid,
                                                   "instance_count",
                                                   sec_key=view_entity.name,
                                                   sort=True, incrBy=0)
            tableCount = tableCount + 1
            #add alias to the list
            if viewAlias != 'no_alias':
                redis_conn.addToList(view_entity.eid, "iview_alias", viewAlias)
            """
            If the current queue entry from the context is given,
            set the view entity id.
            """
            if current_queue_entry is not None:
                current_queue_entry["view_entity_id"] = view_entity.eid
    else:
        """
        Append new alias to existing array
        """
        if viewAlias is not None:
            #add alias to the list
            if viewAlias != 'no_alias':
                redis_conn.addToList(view_entity.eid, "iview_alias", viewAlias)
        else:
            """
            Mark this table as view
            """
            entity_col.update({"eid": view_entity.eid}, {'$set': {'profile.is_view': True}})
    tableEidList.add(view_entity.eid)

    """
    If the database is found then create database Entity if it does not already exist.
    """
    database_entity = None
    if database_name is not None:
        database_entity = mongoconn.getEntityByName(database_name)
        if database_entity is None:
            clog.debug("Creating database entity for {0}\n".format(database_name))
            eid = IdentityService.getNewIdentity(tenant, True)
            mongoconn.addEn(eid, database_name, tenant,\
                      EntityType.SQL_DATABASE, endict, None)
            database_entity = mongoconn.getEntityByName(database_name)
            #create Elastic search index
            sendToElastic(connection1, redis_conn, tenant, uid,
                          database_entity, database_name, EntityType.SQL_DATABASE)
            dbCount = dbCount + 1

    """
    Create realtion between Outmost Query and Inline view table entity
    """
    if viewAlias and outmost_query is not None and outmost_query != entity.eid:
        redis_conn.createRelationship(outmost_query, view_entity.eid, "OQ_IVIEW")
        redis_conn.setRelationship(outmost_query, view_entity.eid, "OQ_IVIEW", {"hive_success":hive_success})

    """
    Create relations, first between table(View) and query
        Then between query and database, table and database
    """
    if entity is not None and view_entity is not None:
        redis_conn.createRelationship(entity.eid, view_entity.eid, "WRITE")
        redis_conn.setRelationship(entity.eid, view_entity.eid, "WRITE", {"hive_success":hive_success})
        clog.debug("WRITE Relation between {0} {1} position 2\n".format(entity.eid, view_entity.eid))
        redis_conn.createRelationship(view_entity.eid, entity.eid, "TABLE_ACCESS_PATTERN")
        redis_conn.setRelationship(view_entity.eid, entity.eid, "TABLE_ACCESS_PATTERN", {"hive_success":hive_success})
        clog.debug("Pattern Relation between {0} {1} position 2\n".format(view_entity.eid, entity.eid))

    if database_entity is not None:
        if view_entity is not None:
            redis_conn.createRelationship(database_entity.eid, view_entity.eid, "CONTAINS")
            clog.debug("Relation between {0} {1} position 5\n".format(database_entity.eid, view_entity.eid))

        """ Note this assumes that formRelations is idempotent
        """
        if entity is not None:
            redis_conn.createRelationship(database_entity.eid, entity.eid, "CONTAINS")
            clog.debug("Relation between {0} {1} position 6\n".format(database_entity.eid, entity.eid))

    for tableentry in inputTableList:
        tablename = getTableName(tableentry)
        table_entity = mongoconn.getEntityByName(tablename)
        if table_entity is None:
            clog.debug("No table with name {0} found\n".format(tablename))
            continue

        '''
        create relationship only if view eid and table eid are different,
        since inputable list can include view table eid also
        '''
        if view_entity.eid != table_entity.eid:
            if viewAlias is not None:
                redis_conn.createRelationship(view_entity.eid, table_entity.eid, "IVIEW_TABLE")
            else:
                redis_conn.createRelationship(view_entity.eid, table_entity.eid, "VIEW_TABLE")
        clog.debug("Relation IVIEW_TABLE between {0} {1}\n".format(view_entity.eid, table_entity.eid))

    return [dbCount, tableCount]

def processCreateTable(table, mongoconn, redis_conn, tenant, uid, entity, isinput, context, clog, tableEidList=None, hive_success=0):
    dbCount = 0
    tableCount = 0
    if table is None or table['tableName'] is None:
        return [dbCount, tableCount]

    outmost_query = None
    queue_len = len(context.queue)
    if queue_len > 0:
        if context.queue[0]['etype'] == EntityType.SQL_STORED_PROCEDURE:
            if queue_len > 1:
                outmost_query = context.queue[1]['eid']
        elif context.queue[0]['etype'] == EntityType.SQL_QUERY:
            outmost_query = context.queue[0]['eid']

    endict = {"uid" : uid}
    #mongoconn.startBatchUpdate()
    tableentry = table
    database_name = None
    entryname = tableentry["tableName"].lower()
    entryname = entryname.replace('"', '')
    matches = table_regex.search(entryname)

    if matches is not None:
        database_name = matches.group(1)
        tablename = matches.group(2)
    else:
        tablename = entryname
        if "databaseName" in tableentry:
            database_name = tableentry["databaseName"].lower()

    """
    Create the Table Entity first if it does not already exist.
    """
    table_entity = mongoconn.getEntityByName(tablename)
    if table_entity is None:
        clog.debug("Creating table entity for {0} position 5\n".format(tablename))
        eid = IdentityService.getNewIdentity(tenant, True)
        table_entity = mongoconn.addEn(eid, tablename, tenant,\
                  EntityType.SQL_TABLE, endict, None)

        if eid == table_entity.eid:
            #create Elastic search index
            sendToElastic(connection1, redis_conn, tenant, uid,
                          table_entity, tablename, EntityType.SQL_TABLE)
            redis_conn.createEntityProfile(table_entity.eid, "SQL_TABLE")
            redis_conn.incrEntityCounter(table_entity.eid, "instance_count", sort=True, incrBy=0)
            tableCount = tableCount + 1

    tableEidList.add(table_entity.eid)

    """
    If the database is found then create database Entity if it does not already exist.
    """
    database_entity = None
    if database_name is not None:
        database_entity = mongoconn.getEntityByName(database_name)
        if database_entity is None:
            clog.debug("Creating database entity for {0}\n".format(database_name))
            eid = IdentityService.getNewIdentity(tenant, True)
            mongoconn.addEn(eid, database_name, tenant,\
                      EntityType.SQL_DATABASE, endict, None)
            database_entity = mongoconn.getEntityByName(database_name)
            #create Elastic search index
            sendToElastic(connection1, redis_conn, tenant, uid,
                          database_entity, database_name, EntityType.SQL_DATABASE)
            dbCount = dbCount + 1

    """
    Create relations, first between tables and query
        Then between query and database, table and database
    """
    if entity is not None and table_entity is not None:
        if isinput:

            if outmost_query is not None and outmost_query != entity.eid:
                redis_conn.createRelationship(table_entity.eid, entity.eid, "SUBQUERYREAD")
                redis_conn.setRelationship(table_entity.eid, entity.eid, "SUBQUERYREAD", {"hive_success":hive_success})
                clog.debug("SUBQUERYREAD Relation between {0} {1} position 1\n".format(table_entity.eid, entity.eid))

            else:
                redis_conn.createRelationship(table_entity.eid, entity.eid, "READ")
                redis_conn.setRelationship(table_entity.eid, entity.eid, "READ", {"hive_success":hive_success})
                clog.debug("READ Relation between {0} {1} position 2\n".format(table_entity.eid, entity.eid))
        else:
            if outmost_query is not None and outmost_query != entity.eid:
                redis_conn.createRelationship(entity.eid, table_entity.eid, "SUBQUERYWRITE")
                redis_conn.setRelationship(entity.eid, table_entity.eid, "SUBQUERYWRITE", {"hive_success":hive_success})
                clog.debug("SUBQUERYWRITE Relation between {0} {1} position 3\n".format(entity.eid, table_entity.eid))

            else:
                redis_conn.createRelationship(entity.eid, table_entity.eid, "WRITE")
                redis_conn.setRelationship(entity.eid, table_entity.eid, "WRITE", {"hive_success":hive_success})
                clog.debug("WRITE Relation between {0} {1} position 4\n".format(entity.eid, table_entity.eid))

        '''
        Makes sure to follow context for the table and outmost query.
        '''
        if table_entity.eid is not None:
            if isinput:
                for query in context.queue:
                    if query['etype'] == EntityType.SQL_QUERY:
                        redis_conn.createRelationship(table_entity.eid, query['eid'], "READ")
                        redis_conn.incrRelationshipCounter(table_entity.eid, query['eid'], "READ", "instance_count", incrBy=1)
                    elif query['etype'] == EntityType.SQL_SUBQUERY:
                        redis_conn.createRelationship(table_entity.eid, query['eid'], "SUBQUERYREAD")
                        redis_conn.incrRelationshipCounter(table_entity.eid, query['eid'], "SUBQUERYREAD", "instance_count", incrBy=1)
                    elif query['etype'] == EntityType.SQL_STORED_PROCEDURE:
                        redis_conn.createRelationship(table_entity.eid, query['eid'], "STOREDPROCEDUREREAD")
                        redis_conn.incrRelationshipCounter(table_entity.eid, query['eid'], "STOREDPROCEDUREREAD", "instance_count", incrBy=1)
            else:
                for query in context.queue:
                    if query['etype'] == EntityType.SQL_QUERY:
                        redis_conn.createRelationship(query['eid'], table_entity.eid, "WRITE")
                        redis_conn.incrRelationshipCounter(query['eid'], table_entity.eid, "WRITE", "instance_count", incrBy=1)
                    elif query['etype'] == EntityType.SQL_SUBQUERY:
                        redis_conn.createRelationship(query['eid'], table_entity.eid, "SUBQUERYWRITE")
                        redis_conn.incrRelationshipCounter(query['eid'], table_entity.eid, "SUBQUERYWRITE", "instance_count", incrBy=1)
                    elif query['etype'] == EntityType.SQL_STORED_PROCEDURE:
                        redis_conn.createRelationship(query['eid'], table_entity.eid, "STOREDPROCEDUREWRITE")
                        redis_conn.incrRelationshipCounter(query['eid'], table_entity.eid, "STOREDPROCEDUREWRITE", "instance_count", incrBy=1)


            context.tables.append(table_entity.eid)

    if database_entity is not None:
        if table_entity is not None:
            redis_conn.createRelationship(database_entity.eid, table_entity.eid, "CONTAINS")
            clog.debug("Relation between {0} {1} position 5\n".format(database_entity.eid, table_entity.eid))

        """ Note this assumes that formRelations is idempotent
        """
        if entity is not None:
            redis_conn.createRelationship(database_entity.eid, entity.eid, "CONTAINS")
            clog.debug("Relation between {0} {1} position 6\n".format(database_entity.eid, entity.eid))

    #mongoconn.finishBatchUpdate()

    return [dbCount, tableCount]

def process_scale_mode(tenant, uid, instances, smc, clog):

    for inst in instances:
        msg_data = None
        if "data" in inst:
            msg_data = inst["data"]

        """
        Create input and output folders for compiler
        """
        if 'query' in inst:
            query = inst["query"].strip()
        else:
            clog.error("Could not find query")
            continue
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        destination = '/mnt/volume1/compile-' + tenant + "/" + timestr
        if not os.path.exists(destination):
            os.makedirs(destination)


        data_dict = { "input_query": query,
                      "Compiler": "gsp",
                      "EntityId": "",
                      "TenantId": "100" }
        opcode = 1
        retries = 3
        response = tclient.send_compiler_request(opcode, data_dict, retries)
        if response.isSuccess == True:
          clog.debug("Got Done")

        compile_doc = None
        clog.info("Loading file : "+ output_file_name)
        if not response.isSuccess:
          clog.error("compiler request failed")
          return None
        else:
          compile_doc = loads(response.result)

        compile_doc_fields = ["ErrorSignature",
                              "SignatureKeywords",
                              "OperatorList",
                              "selectColumnNames",
                              "groupByColumns",
                              "orderByColumns",
                              "whereColExpr",
                              "joinPredicates",
                              "queryHash",
                              "queryNameHash",
                              "InputTableList",
                              "OutputTableList",
                              "ComplexityScore",
                              "viewName"]

        try:
            smc.process(compile_doc, compile_doc_fields, 'gsp', {'etype': 'SQL_QUERY'}, msg_data)
        except:
            clog.exception("Error in ScaleModeConnector")

def updateRelationCounter(redis_conn, eid):

    relationshipTypes = ['QUERY_SELECT', 'QUERY_JOIN', 'QUERY_FILTER', "READ", "WRITE", "COOCCURRENCE_TABLE",
                         'QUERY_GROUPBY', 'QUERY_ORDERBY', "COOCCURRENCE_GROUP", "COOCCURRENCE_QUERY"]

    relations_to = redis_conn.getRelationships(eid, None, None)
    for rel in relations_to:
        if rel['rtype'] in relationshipTypes:
            redis_conn.incrRelationshipCounter(eid, rel['end_en'], rel['rtype'], "instance_count", incrBy=1)

    relations_from = redis_conn.getRelationships(None, eid, None)
    for rel in relations_from:
        if rel['rtype'] in relationshipTypes:
            redis_conn.incrRelationshipCounter(rel['start_en'], eid, rel['rtype'], "instance_count", incrBy=1)

def sendAnalyticsMessage(mongoconn, redis_conn, ch, collection, tenant, uid, entity, opcode, received_msg):
    if received_msg is not None and "test_mode" in received_msg:
        return

    if entity is not None:
        if opcode is not None:
            msg_dict = {'tenant':tenant, 'opcode':opcode, "entityid":entity.eid}
            if uid is not None:
                msg_dict['uid'] = uid
            message_id = genMessageID("Comp", redis_conn, entity.eid)
            msg_dict['message_id'] = message_id
            if received_msg is not None:
                if "message_id" in received_msg:
                    msg_dict['query_message_id'] = received_msg["message_id"]
            message = dumps(msg_dict)
            logging.info("Sending message to Math pos1:" + str(msg_dict))
            incrementPendingMessage(collection, redis_conn, uid,message_id)
            connection1.publish(ch,'','mathqueue',message)

def sendAdvAnalyticsMessage(ch, msg_dict):
    if msg_dict is None:
        return

    message = dumps(msg_dict)
    connection1.publish(ch,'','advanalytics',message)

def create_query_character(signature_keywords, operator_list):
    '''
    Takes in SignatureKeywords and OperatorList lists and creates the filtered
    version for the UI. Takes ranking into account.
    '''
    character = []

    '''
    Check for ddl character in operator list
    '''
    ddl_char = ['CREATE_TABLE', 'ALTER_TABLE', 'DROP_TABLE']
    for entry in ddl_char:
        if entry in operator_list:
           character.append('DDL')
           return character

    operators = ['INSERT', 'UPDATE', 'DELETE']
    for operator in operators:
        if '%s_VALUES'%(operator) in operator_list:
            character.append('%s: singleton'%(operator))
            return character
        elif '%s_SIMPLE'%(operator) in operator_list:
            character.append('%s: singleton'%(operator))
            return character

    if 'Single Table' in signature_keywords[0]:
        temp_character = signature_keywords[0].split(':')
        if len(temp_character) > 1:
            temp_character = temp_character[1]

        if 'No Table Only' in temp_character:
            character.append('No Table')
            character = [' '.join(character)]
            return character

        character.append('Single Table : ')
        if 'Only' in temp_character:
            character.append(temp_character)
            character = [' '.join(character)]
            return character

        if 'Group By' in temp_character:
            character.append('Group By')
        if 'Aggregation' in temp_character:
            character.append('Aggregation')
        if 'Where' in temp_character:
            character.append('Filter')
        if 'Case' in temp_character:
            character.append('Case')
        if 'Order By' in temp_character:
            character.append('Order By')
        if 'SELECT' in temp_character:
            character.append('Select')
        if 'In' in temp_character:
            character.append('In')
        if 'Exists' in temp_character:
            character.append('Exists')

        #Logic to get rid of comma between
        #'Single Table' and first operator
        start_character = ''.join(character[:2])
        character = [start_character] + character[2:]
        return character[:2]
    else:
        prefix = []
        if 'Insert' in signature_keywords:
            prefix.append('INSERT: ')
        if 'UPDATE' in operator_list:
            prefix.append('UPDATE: ')
        if 'DELETE' in operator_list:
            prefix.append('DELETE: ')

        if 'Join' in signature_keywords:
            character.append('Join')
        if 'Group By' in signature_keywords:
            character.append('Group By')
        if 'Subquery' in signature_keywords:
            character.append('Subquery')
        if 'Views' in signature_keywords:
            character.append('Views')
        if 'Union' in signature_keywords:
            character.append('Union')
        if 'Aggregation' in signature_keywords:
            character.append('Aggregation')
        if 'Where' in signature_keywords:
            character.append('Filter')
        if 'Case' in signature_keywords:
            character.append('Case')
        if 'Order By' in signature_keywords:
            character.append('Order By')
        if 'In' in signature_keywords:
            character.append('In')
        if 'Exists' in signature_keywords:
            character.append('Exists')

        if 'SELECT' in operator_list:
            character.append('Select')

        start_character = ''.join(prefix + character[:1])
        character = [start_character] + character[1:]
        return character[:2]

def check_query_type(query_character_list):
    found_single_table = False
    for char_entry in query_character_list:
        if 'Single Table' in char_entry:
            found_single_table = True
        if found_single_table and 'Only' in char_entry:
            return True
        else:
            return False


def process_tag_array(tenant, q_eid, mongoconn, redis_conn, tagArray, data, uid):
    '''
    Given a tagArray, creates entities for each tag in the array,
        then creates relationships between the entities that were created.
    '''
    for tagKey in tagArray:
        '''
        Creates a FILE_TAG entity.
        Creates a relationship between FILE_TAG and SQL_QUERY entity.
        '''
        if tagKey in data:
            tag_eid = IdentityService.getNewIdentity(tenant, True)
            tag_etype = EntityType.FILE_TAG
            tag_profile = {'tagKey': tagKey, 'tagVal': data[tagKey]}
            tag_name = '%s:%s' % (tagKey, data[tagKey])
            tag_entity = mongoconn.addEn(tag_eid, tag_name, tenant, tag_etype,
                                         tag_profile, None)
            if tag_eid == tag_entity.eid:
                redis_conn.createEntityProfile(tag_entity.eid, tag_etype)
            #create Elastic search index
            sendToElastic(connection1, redis_conn, tenant, uid,
                          tag_entity, tag_name, tag_etype)
            """
            Establish relationship between the Tag entity and the query.
                Tag -> Query.
            """
            created = redis_conn.createRelationship(tag_entity.eid, q_eid, 'QUERY_TAG')
            if created:
                redis_conn.setRelationship(tag_entity.eid, q_eid, 'QUERY_TAG', tag_profile)
            redis_conn.incrRelationshipCounter(tag_entity.eid, q_eid, 'QUERY_TAG', "count")


def process_count_array(tenant, q_eid, mongoconn, redis_conn, countArray, data, clog):
    '''
    Given a countArray, increments the count on q_eid for the tag
        by an amount equal to the value passed in.
    '''
    for countKey in countArray:
        if countKey in data:
            try:
                val = float(data[countKey])
                redis_conn.incrEntityCounter(q_eid, countKey, sort=True, incrBy=val)
                redis_conn.incrEntityCounter("dashboard_data", 'total_'+countKey, sort=False, incrBy=val)
            except:
                clog.exception("Non numerical count value passed")


def processCompilerOutputs(mongoconn, redis_conn, ch, collection, tenant, uid, query, data, compile_doc, source_platform, smc, context, clog, tagArray=None, countArray=None):

    """
        Takes a list of compiler output files and performs following:
            1. If the compiler is unsuccessful in parsing the query:
                  Build the profile info
            2. If the compiler is successful in parsing the query:
                - Check if the entity with MD5 hash already exists.
                    o If the query entity exists, then add the instance and return
                      No further processing is necessary.
                    o If the query entity does not exist, then add the profile, record the hash.
            3. After all the compiler outputs have been processed, create the query entity.
            4. If the query is a stored procedure, creates the entity with an etype of SQL_STORED_PROCEDURE.
            5. If the query is a subquery, creates the entity with an etype of SQL_SUBQUERY.
    """
    entity = None
    is_failed_in_gsp = False
    elapsed_time = None
    tableEidList = set()
    if compile_doc is None:
        clog.error("No compile_doc found")
        return None, None

    compiler_to_use = get_compiler(source_platform)
    profile_dict = {"uid": uid, "profile": {'character': [], "Compiler": {}}, 'compiler_to_use': compiler_to_use, 'parse_success': True}
    comp_profile = profile_dict["profile"]["Compiler"]

    q_hash = None
    q_name_hash = None

    if len(context.queue) < 1:
        etype = EntityType.SQL_QUERY
    elif len(context.queue) == 1:
        if context.queue[0]['etype'] == EntityType.SQL_STORED_PROCEDURE:
            etype = EntityType.SQL_QUERY
        else:
            etype = EntityType.SQL_SUBQUERY
    else:
        etype = EntityType.SQL_SUBQUERY

    compiler = compiler_to_use

    if compiler in compile_doc:
        if compile_doc[compiler].has_key("isInlineView") and compile_doc[compiler]["isInlineView"] == True:
            etype = EntityType.SQL_INLINE_VIEW

        #check for meta query and drop it
        if etype == EntityType.SQL_QUERY:
            if 'OperatorList' in compile_doc[compiler] and \
                'METAQUERY' in compile_doc[compiler]['OperatorList']:
                meta_key = "Compiler."+compiler+".metaQueryCount"
                redis_conn.incrEntityCounter(uid, meta_key, incrBy = 1)
                etype = EntityType.SQL_METAQUERY
                #return None, None

        compile_doc_fields = ["SignatureKeywords",
                      "OperatorList",
                      "selectColumnNames",
                      "groupByColumns",
                      "orderByColumns",
                      "whereColExpr",
                      "joinPredicates",
                      "InputTableList",
                      "OutputTableList",
                      "ComplexityScore",
                      "createTableName",
                      "ddlColumns",
                      "viewName",
                      "unqualifiedColumn"]
        if etype == EntityType.SQL_QUERY:
            compile_doc_fields = ["ErrorSignature", "queryHash", "queryNameHash"] + compile_doc_fields

        try:
            smc.process(compile_doc, compile_doc_fields, compiler, {'etype': etype}, data)
        except:
            clog.exception("Error in ScaleModeConnector")

    else:
        is_failed_in_gsp = True

    smc_json = smc.generate_json()
    unique_count = int(smc_json["unique_uniquequeries"])
    sem_unique_count = int(smc_json["unique_queries"])
    total_query_count = int(smc_json["parsed"])
    clog.debug("Updating query counts " + str(unique_count))
    dash_update_dict = {
                        "TotalQueries": total_query_count,
                        "semantically_unique_count": sem_unique_count,
                        "unique_count": unique_count}
    redis_conn.setEntityProfile('dashboard_data', dash_update_dict)

    for key in compile_doc:
        comp_profile[key] = compile_doc[key]
        if key == compiler:

            if "queryExtendedHash" in compile_doc[key]:
                q_hash =  compile_doc[key]["queryExtendedHash"]
                profile_dict["md5"] = q_hash
                clog.debug("Compiler {0} Program {1}  md5 {2}".format(key, query, q_hash))
            elif "queryHash" in compile_doc[key]:
                q_hash =  compile_doc[key]["queryHash"]
                profile_dict["md5"] = q_hash
                clog.debug("Compiler {0} Program {1}  md5 {2}".format(key, query, q_hash))
            if "queryNameHash" in compile_doc[key]:
                q_name_hash =  compile_doc[key]["queryNameHash"]
            if "queryTemplate" in compile_doc[key]:
                profile_dict["logical_name"] = compile_doc[key]["queryTemplate"]
            if 'OperatorList' in compile_doc[key] and \
                'PROCEDURE' in compile_doc[key]['OperatorList']:
                etype = EntityType.SQL_STORED_PROCEDURE
            if 'SignatureKeywords' in compile_doc[key]:
                operator_list = []
                if 'OperatorList' in compile_doc[key]:
                    operator_list = compile_doc[key]['OperatorList']
                character = create_query_character(compile_doc[key]['SignatureKeywords'], operator_list)
                profile_dict['profile']['character'] = character

            #check if this is a simple or complex query
            if etype == EntityType.SQL_QUERY and \
                    'ErrorSignature' in compile_doc[key] and compile_doc[key]["ErrorSignature"] == "":
                temp_keywords = None
                if 'SignatureKeywords' in compile_doc[key]:
                    temp_keywords = compile_doc[key]['SignatureKeywords']
                    if temp_keywords is not None:
                        is_simple = check_query_type(temp_keywords)
                        if is_simple:
                            #mark the query as complex query
                            redis_conn.incrEntityCounter('dashboard_data', 'simple_query_count', incrBy=1)
                        else:
                            #mark the query as simple query
                            redis_conn.incrEntityCounter('dashboard_data', 'complex_query_count', incrBy=1)
            if "combinedQueryList" in compile_doc[key]:
                for entry in compile_doc[key]['combinedQueryList']:
                    if "combinerClause" in entry:
                        if entry["combinerClause"] == "UNION":
                            #mark the query as simple query
                            redis_conn.incrEntityCounter('dashboard_data', 'union_count', incrBy=1)
                        if entry["combinerClause"] == "UNION_ALL":
                            #mark the query as simple query
                            redis_conn.incrEntityCounter('dashboard_data', 'union_all_count', incrBy=1)
            if 'ErrorSignature' in compile_doc[key] and len(compile_doc[key]["ErrorSignature"]) > 0:
                is_failed_in_gsp = True
                profile_dict['parse_success'] = False

    custom_id = None
    if data is not None and "custom_id" in data:
        custom_id = data['custom_id']

    """
        get Entity
        if no entity then create entity
    """
    entity = None
    if q_hash is not None:
        entity = mongoconn.searchEntity({"md5":q_hash})

    update = False
    if entity is None:
        clog.debug("Going to create the entity")
        profile_dict["instance_count"] = 1
        if custom_id is not None:
            profile_dict['custom_id'] = custom_id
        if data is not None:
            profile_dict['profile']['stats'] = data
            if 'ELAPSED_TIME' in data:
                elapsed_time = data['ELAPSED_TIME']
        try:
            eid = IdentityService.getNewIdentity(tenant, True)
            entity = mongoconn.addEn(eid, query, tenant,\
                       etype, profile_dict, None)
            if entity is None:
                clog.error("No Entity found")
                return None, None
            if eid == entity.eid:

                #create Elastic search index
                sendToElastic(connection1, redis_conn, tenant, uid,
                              entity, query, etype)
                redis_conn.createEntityProfile(entity.eid, etype)
                redis_conn.incrEntityCounterWithSecKey(entity.eid,
                                                       "instance_count",
                                                       sec_key=custom_id,
                                                       sort=True, incrBy=1)
                if elapsed_time is not None:
                    try:
                        redis_conn.incrEntityCounter(entity.eid, "total_elapsed_time", sort=True, incrBy=float(elapsed_time))
                        redis_conn.incrEntityCounter("dashboard_data", "total_elapsed_time", sort=False, incrBy=float(elapsed_time))
                    except:
                        clog.exception("No or junk elapsed time found:%s", elapsed_time)

                inst_dict = {"query": query}
                if data is not None:
                    inst_dict.update(data)
                    if tagArray is not None:
                        process_tag_array(tenant, entity.eid, mongoconn, redis_conn, tagArray, data, uid)
                    if countArray is not None:
                        process_count_array(tenant, entity.eid, mongoconn, redis_conn, countArray, data, clog)

                if custom_id is not None:
                    mongoconn.updateInstance(entity, custom_id, None, inst_dict)
                else:
                    mongoconn.updateInstance(entity, eid, None, inst_dict)

                entityProfile = entity.profile

                if "Compiler" in entityProfile\
                        and compiler in entityProfile['Compiler']\
                        and "ComplexityScore" in entityProfile['Compiler'][compiler]:
                    redis_conn.incrEntityCounter(entity.eid, "ComplexityScore", sort = True,
                        incrBy= entityProfile["Compiler"][compiler]["ComplexityScore"])
                else:
                    clog.error("No ComplexityScore found.")
                temp_keywords = None
                if "Compiler" in entityProfile\
                 and compiler in entityProfile['Compiler']\
                 and 'ErrorSignature' in entityProfile['Compiler'][compiler]\
                 and entityProfile['Compiler'][compiler]["ErrorSignature"] == ""\
                 and 'SignatureKeywords' in entityProfile["Compiler"][compiler]:
                    temp_keywords = entityProfile["Compiler"][compiler]['SignatureKeywords']
                    if temp_keywords is not None:
                        is_simple = check_query_type(temp_keywords)
                        if is_simple:
                            for entry in temp_keywords:
                                simple_type_list = entry.split(':')
                                keyword_to_use = simple_type_list[0]
                                if len(simple_type_list) > 1:
                                    type_to_use = simple_type_list[1]
                                set_key = tenant + ':eid:simple_query:set:' + keyword_to_use
                                redis_conn.addToSet('simple_query', keyword_to_use, entity.eid)
                                redis_conn.r.sadd(tenant+':simple_query', set_key)
                            #mark the query as complex query
                            redis_conn.incrEntityCounter('dashboard_data', 'unique_simple_query_count', incrBy=1)
                        else:
                            for entry in temp_keywords:
                                set_key = tenant + ':eid:complex_query:set:' + entry
                                redis_conn.addToSet('complex_query', entry, entity.eid)
                                redis_conn.r.sadd(tenant+':complex_query', set_key)
                            #mark the query as simple query
                            redis_conn.incrEntityCounter('dashboard_data', 'unique_complex_query_count', incrBy=1)
            else:
                update = True

        except DuplicateKeyError:
            inst_dict = {}

            if custom_id is not None:
                inst_dict = {'custom_id':custom_id}
            entity = mongoconn.searchEntity({"md5":q_hash})
            if entity is None:
                clog.exception("Entity not found for hash - {0}".format(q_hash))
                return None, None
    else:
        update = True
        #update the stats since they were provided

        if data is not None:
            entity_instance = mongoconn.db.entities.find_one({'md5':q_hash})
            stats = entity_instance["profile"]["stats"]
            setDict = stats.copy()
            for field in data:
                if field == "custom_id":
                    setDict["custom_id"] = data["custom_id"]
                    continue
                if field in setDict and setDict[field] is not None and not isinstance(setDict[field], list):
                    setDict[field] = [setDict[field]]
                else:
                    setDict[field] = []
                setDict[field].append(data[field])
            mongoconn.db.entities.update({'md5':q_hash}, {'$set':{'profile.stats': setDict}})


    """
    Context Queue entry.
    It contains, the entity id of the query/suquery/inline view and type.
    It can also contain additional information required to process the
    entity and form the relationships.
    For Eg. In case on Inline view, it can contain information about the
    inline view table object.
    """
    current_queue_entry = {'eid': entity.eid, 'etype': etype}
    context.queue.append(current_queue_entry)

    if update == True and etype == "SQL_QUERY":
        inst_dict = {"query": query}
        if data is not None:
            inst_dict.update(data)
            if tagArray is not None:
                process_tag_array(tenant, entity.eid, mongoconn, redis_conn, tagArray, data, uid)
            if countArray is not None:
                process_count_array(tenant, entity.eid, mongoconn, redis_conn, countArray, data, clog)

        if custom_id is not None:
            mongoconn.updateInstance(entity, custom_id, None, inst_dict)
        else:
            eid = IdentityService.getNewIdentity(tenant, True)
            mongoconn.updateInstance(entity, eid, None, inst_dict)
        if 'ELAPSED_TIME' in data:
            elapsed_time = data['ELAPSED_TIME']
        if elapsed_time is not None:
            try:
                redis_conn.incrEntityCounter(entity.eid, "total_elapsed_time", sort = True,incrBy=float(elapsed_time))
                redis_conn.incrEntityCounter("dashboard_data", "total_elapsed_time", sort=False, incrBy=float(elapsed_time))
            except:
                clog.exception("No or junk elapsed time found:%s", elapsed_time)
        try:
            for key in compile_doc:
                stats_runsuccess_key = "Compiler." + key + ".run_success"
                stats_runfailure_key = "Compiler." + key + ".run_failure"
                stats_success_key = "Compiler." + key + ".success"
                stats_failure_key = "Compiler." + key + ".failure"
                stats_proc_success_key = "Compiler." + key + ".storeproc_success"
                stats_proc_failure_key = "Compiler." + key + ".storeproc_failure"
                stats_sub_success_key = "Compiler." + key + ".subquery_success"
                stats_sub_failure_key = "Compiler." + key + ".subquery_failure"

                if compile_doc[key].has_key("ErrorSignature") \
                    and len(compile_doc[key]["ErrorSignature"]) > 0:
                    if etype == "SQL_QUERY":
                        #No need to add HAQR call here since this is executed only when there is a repetition of hash
                        redis_conn.incrEntityCounter(uid, stats_failure_key, incrBy = 1)
                        redis_conn.incrEntityCounter(uid, stats_runsuccess_key, incrBy = 1)
                    elif etype == "SQL_SUBQUERY":
                        redis_conn.incrEntityCounter(uid, stats_sub_failure_key, incrBy = 1)

                    elif etype == "SQL_STORED_PROCEDURE":
                        redis_conn.incrEntityCounter(uid, stats_proc_failure_key, incrBy = 1)
                    elif etype == "SQL_INLINE_VIEW":
                        redis_conn.incrEntityCounter(uid, stats_proc_failure_key, incrBy = 1)
                else:
                    if etype == "SQL_QUERY":
                        redis_conn.incrEntityCounter(uid, stats_success_key, incrBy = 1)
                        redis_conn.incrEntityCounter(uid, stats_runsuccess_key, incrBy = 1)
                    elif etype == "SQL_SUBQUERY":
                        redis_conn.incrEntityCounter(uid, stats_sub_success_key, incrBy = 1)
                    elif etype == "SQL_STORED_PROCEDURE":
                        redis_conn.incrEntityCounter(uid, stats_proc_success_key, incrBy = 1)
                    elif etype == "SQL_INLINE_VIEW":
                        redis_conn.incrEntityCounter(uid, stats_proc_success_key, incrBy = 1)

            return entity, "UpdateQueryProfile"
        except:
            clog.exception("Tenent {0}, {1}\n".format(tenant, traceback.format_exc()))
            if uid is not None:
                if etype == "SQL_QUERY":
                    redis_conn.incrEntityCounter(uid, stats_runfailure_key, incrBy = 1)
                elif etype == "SQL_SUBQUERY":
                    redis_conn.incrEntityCounter(uid, stats_sub_failure_key, incrBy = 1)
                elif etype == "SQL_STORED_PROCEDURE":
                    redis_conn.incrEntityCounter(uid, stats_proc_failure_key, incrBy = 1)
                elif etype == "SQL_INLINE_VIEW":
                    redis_conn.incrEntityCounter(uid, stats_proc_failure_key, incrBy = 1)
            return None, None

    '''
    Creates relationships between the queries in the hierarchy.
    '''
    if len(context.queue) > 1:
        '''
        context.queue[-2] is used here because the last element
        on the queue is the current query.
        '''

        current_query = context.queue[-2]['eid']

        if etype == EntityType.SQL_QUERY:
            '''
            Stored procedure -> Query relationship
            '''
            redis_conn.incrRelationshipCounter(current_query, entity.eid, "STORED_PROCEDURE_QUERY", "count")

        elif etype == EntityType.SQL_SUBQUERY:
            '''
            Query -> Subquery relationship
            '''
            redis_conn.incrRelationshipCounter(current_query, entity.eid, "SQL_SUBQUERY", "count")
        elif etype == EntityType.SQL_INLINE_VIEW:
            '''
            Query -> Subquery relationship
            '''
            redis_conn.incrRelationshipCounter(current_query, entity.eid, "SQL_INLINE_VIEW", "count")

    for i, key in enumerate(compile_doc):
        try:
            stats_newdbs_key = "Compiler." + key + ".newDBs"
            stats_newtables_key = "Compiler." + key + ".newTables"
            stats_runsuccess_key = "Compiler." + key + ".run_success"
            stats_runfailure_key = "Compiler." + key + ".run_failure"
            stats_success_key = "Compiler." + key + ".success"
            stats_failure_key = "Compiler." + key + ".failure"
            stats_proc_success_key = "Compiler." + key + ".storeproc_success"
            stats_proc_failure_key = "Compiler." + key + ".storeproc_failure"
            stats_sub_success_key = "Compiler." + key + ".subquery_success"
            stats_sub_failure_key = "Compiler." + key + ".subquery_failure"

            inputTableList = []
            if compile_doc[key].has_key("isInlineView") and compile_doc[key]["isInlineView"] == True:
                inlineViewAlias = None
                if compile_doc[key].has_key("inlineViewAlias"):
                    inlineViewAlias = compile_doc[key]["inlineViewAlias"]
                else:
                    inlineViewAlias = 'no_alias'
                tmpAdditions = processCreateViewOrInlineView(compile_doc[key]["inlineViewName"], mongoconn,
                                                 redis_conn, mongoconn.db.entities,
                                                 tenant, uid, entity,context , inputTableList, clog, tableEidList,
                                                 0, inlineViewAlias, current_queue_entry)
                if uid is not None:
                    redis_conn.incrEntityCounter(uid, stats_newdbs_key, incrBy=tmpAdditions[0])
                    redis_conn.incrEntityCounter(uid, stats_newtables_key, incrBy=tmpAdditions[1])
                    redis_conn.incrEntityCounter('dashboard_data', 'inlineViewCount', incrBy=tmpAdditions[1])

            if key == compiler_to_use and compile_doc[key].has_key("subQueries") and\
                len(compile_doc[key]["subQueries"]) > 0:
                clog.debug("Processing Sub queries")

                for sub_q_dict in compile_doc[key]["subQueries"]:

                    if "origQuery" not in sub_q_dict:
                        clog.error("Original query not found in sub query dictionary")
                        continue
                    sub_q = sub_q_dict["origQuery"]
                    clog.debug("Processing Sub queries " + sub_q)
                    sub_entity, sub_opcode = processCompilerOutputs(mongoconn, redis_conn, ch, collection,
                                                    tenant, uid, sub_q, data, {key:sub_q_dict}, source_platform, smc, context, clog)
                    temp_msg = {'test_mode':1} if context.test_mode else None
                    sendAnalyticsMessage(mongoconn, redis_conn, ch, collection, tenant, uid, sub_entity, sub_opcode, temp_msg)

                    if sub_entity is not None:
                        context.queue.pop()

            hive_success = 0
            if key == "hive" and 'ErrorSignature' in compile_doc:
                if len(compile_doc['ErrorSignature']) == 0:
                    hive_success = 1

            mongoconn.updateProfile(entity, "Compiler", key, compile_doc[key])

            if compile_doc[key].has_key("InputTableList"):
                inputTableList = compile_doc[key]["InputTableList"]
                tmpAdditions = processTableSet(compile_doc[key]["InputTableList"],
                                               mongoconn, redis_conn, tenant, uid, entity, True,
                                               context, clog, tableEidList)
                if uid is not None:
                    redis_conn.incrEntityCounter(uid, stats_newdbs_key, incrBy=tmpAdditions[0])
                    redis_conn.incrEntityCounter(uid, stats_newtables_key, incrBy=tmpAdditions[1])
                    redis_conn.incrEntityCounter('dashboard_data', 'TableCount', incrBy=tmpAdditions[1])

            if compile_doc[key].has_key("OutputTableList"):
                tmpAdditions = processTableSet(compile_doc[key]["OutputTableList"],
                                                mongoconn, redis_conn, tenant, uid, entity, False,
                                                context, clog, tableEidList)
                if uid is not None:
                    redis_conn.incrEntityCounter(uid, stats_newdbs_key, incrBy=tmpAdditions[0])
                    redis_conn.incrEntityCounter(uid, stats_newtables_key, incrBy=tmpAdditions[1])
                    redis_conn.incrEntityCounter('dashboard_data', 'TableCount', incrBy=tmpAdditions[1])

            if compile_doc[key].has_key("ddlColumns"):
                tmpAdditions = processColumns(compile_doc[key]["ddlColumns"],
                                              mongoconn, redis_conn, tenant, uid, entity, clog)
                if uid is not None:
                    redis_conn.incrEntityCounter(uid, stats_newdbs_key, incrBy=tmpAdditions[0])
                    redis_conn.incrEntityCounter(uid, stats_newtables_key, incrBy=tmpAdditions[1])
                    redis_conn.incrEntityCounter('dashboard_data', 'TableCount', incrBy=tmpAdditions[1])


            if compile_doc[key].has_key("createTableName"):
                tmpAdditions = processCreateTable(compile_doc[key]["createTableName"],
                                              mongoconn, redis_conn,tenant, uid, entity, False, context, clog, tableEidList)
                if uid is not None:
                    redis_conn.incrEntityCounter(uid, stats_newdbs_key, incrBy=tmpAdditions[0])
                    redis_conn.incrEntityCounter(uid, stats_newtables_key, incrBy=tmpAdditions[1])
                    redis_conn.incrEntityCounter('dashboard_data', 'TableCount', incrBy=tmpAdditions[1])

            if compile_doc[key].has_key("viewName") and compile_doc[key].has_key("view") and compile_doc[key]["view"] == True:
                tmpAdditions = processCreateViewOrInlineView(compile_doc[key]["viewName"],
                                         mongoconn, redis_conn, mongoconn.db.entities,
                                         tenant, uid, entity,context, inputTableList, clog, tableEidList,
                                         0, None, current_queue_entry)
                if uid is not None:
                    redis_conn.incrEntityCounter(uid, stats_newdbs_key, incrBy=tmpAdditions[0])
                    redis_conn.incrEntityCounter(uid, stats_newtables_key, incrBy=tmpAdditions[1])
                    redis_conn.incrEntityCounter('dashboard_data', 'ViewCount', incrBy=tmpAdditions[1])

            if compile_doc[key].has_key("ErrorSignature") \
                and len(compile_doc[key]["ErrorSignature"]) > 0:
                if etype == "SQL_QUERY":
                    redis_conn.incrEntityCounter(uid, stats_failure_key, incrBy=1)
                    redis_conn.incrEntityCounter(uid, stats_runsuccess_key, incrBy=1)
                    #if its 'gsp' and it failed we do not send it to HAQR...
                    #if is_failed_in_gsp == True:
                    #    continue
                    if key == "impala":
                        try:
                            haqr_query = query
                            if compiler_to_use in compile_doc and\
                               "queryTemplate" in compile_doc[compiler_to_use]:
                                   haqr_query = compile_doc[compiler_to_use]["queryTemplate"]

                            #call advance analytics to start HAQR Phase
                            adv_analy_dict = {'tenant': tenant,
                                              'query': haqr_query,
                                              'key': key,
                                              'eid' : eid,
                                              'source_platform': source_platform,
                                              'opcode': "HAQRPhase"
                                             }
                            sendAdvAnalyticsMessage(ch, adv_analy_dict)
                            #analyzeHAQR(query,key,tenant,entity.eid,source_platform,mongoconn,redis_conn)
                        except:
                            clog.exception('analyzeHAQR has failed.')
                    if key == "hive":
                        try:
                            haqr_query = query
                            if compiler_to_use in compile_doc and\
                               "queryTemplate" in compile_doc[compiler_to_use]:
                                   haqr_query = compile_doc[compiler_to_use]["queryTemplate"]

                            #call advance analytics to start HAQR Phase
                            adv_analy_dict = {'tenant': tenant,
                                              'query': haqr_query,
                                              'key': key,
                                              'eid' : eid,
                                              'source_platform': source_platform,
                                              'opcode': "HAQRPhase"
                                             }
                            sendAdvAnalyticsMessage(ch, adv_analy_dict)
                            #analyzeHAQR(query,key,tenant,entity.eid,source_platform,mongoconn,redis_conn)
                        except:
                            clog.exception('analyzeHAQR has failed.')
                elif etype == "SQL_SUBQUERY":
                    redis_conn.incrEntityCounter(uid, stats_sub_failure_key, incrBy=1)
                elif etype == "SQL_INLINE_VIEW":
                    redis_conn.incrEntityCounter(uid, stats_sub_failure_key, incrBy=1)
                elif etype == "SQL_STORED_PROCEDURE":
                    redis_conn.incrEntityCounter(uid, stats_proc_failure_key, incrBy=1)
                elif etype == "SQL_SUBQUERY":
                    redis_conn.incrEntityCounter(uid, stats_sub_failure_key, incrBy=1)
            else:
                if etype == "SQL_QUERY":
                    redis_conn.incrEntityCounter(uid, stats_success_key, incrBy=1)
                    redis_conn.incrEntityCounter(uid, stats_runsuccess_key, incrBy=1)
                elif etype == "SQL_SUBQUERY":
                    redis_conn.incrEntityCounter(uid, stats_sub_success_key, incrBy=1)
                elif etype == "SQL_INLINE_VIEW":
                    redis_conn.incrEntityCounter(uid, stats_sub_success_key, incrBy=1)
                elif etype == "SQL_STORED_PROCEDURE":
                    redis_conn.incrEntityCounter(uid, stats_proc_success_key, incrBy=1)

        except:
            clog.exception("Tenent {0}, {1}\n".format(tenant, traceback.format_exc()))
            if uid is not None:
                if etype == "SQL_QUERY":
                    redis_conn.incrEntityCounter(uid, stats_runfailure_key, incrBy=1)
                elif etype == "SQL_SUBQUERY":
                    redis_conn.incrEntityCounter(uid, stats_sub_failure_key, incrBy=1)
                elif etype == "SQL_INLINE_VIEW":
                    redis_conn.incrEntityCounter(uid, stats_sub_failure_key, incrBy=1)
                elif etype == "SQL_STORED_PROCEDURE":
                    redis_conn.incrEntityCounter(uid, stats_proc_failure_key, incrBy=1)
            return None, None

    if update == True and etype != "SQL_QUERY":
        redis_conn.incrEntityCounter(entity.eid, "instance_count", sort = True, incrBy=1)
        return entity, "UpdateQueryProfile"

    return entity, "GenerateQueryProfile"

def analyzeHAQR(query, platform, tenant, eid,source_platform,mongoconn,redis_conn):
    if platform != "impala":
        return #currently HAQR supported only for impala

    queryFsmFile = "/etc/xplain/QueryFSM.csv";
    selectFsmFile = "/etc/xplain/SelectFSM.csv";
    whereFsmFile = "/etc/xplain/WhereFSM.csv";
    groupByFsmFile = "/etc/xplain/GroupbyFSM.csv";
    whereSubClauseFsmFile = "/etc/xplain/WhereSubclauseFSM.csv";
    fromFsmFile = "/etc/xplain/FromFSM.csv";
    selectSubClauseFsmFile = "/etc/xplain/SelectSubclauseFSM.csv";
    groupBySubClauseFsmFile = "/etc/xplain/GroupBySubclauseFSM.csv";
    fromSubClauseFsmFile = "/etc/xplain/FromSubclauseFSM.csv";

    data_dict = {
        "input_query": query,
        "EntityId": eid,
        "TenantId": tenant,
        "queryFsmFile": queryFsmFile,
        "selectFsmFile": selectFsmFile,
        "whereFsmFile": whereFsmFile,
        "groupByFsmFile": groupByFsmFile,
        "whereSubClauseFsmFile": whereSubClauseFsmFile,
        "fromFsmFile": fromFsmFile,
        "selectSubClauseFsmFile": selectSubClauseFsmFile,
        "groupBySubClauseFsmFile": groupBySubClauseFsmFile,
        "fromSubClauseFsmFile": fromSubClauseFsmFile,
        "source_platform": source_platform
    }
    opcdode_HAQR = 4
    retries = 3
    response = tclient.send_compiler_request(opcdode_HAQR, data_dict, retries)

    data = None
    data = loads(response.result)

    logging.debug(dumps(data))

    mongoconn.db.entities.update({'eid':eid},{"$set":{'profile.Compiler.HAQR':data}})
    updateRedisforHAQR(redis_conn,data,tenant,eid)

    return

def updateRedisforHAQR(redis_conn,data,tenant,eid):
    redis_conn.createEntityProfile("HAQR", "HAQR")

    redis_conn.incrEntityCounter("HAQR", "numInvocation", sort=False, incrBy=1)
    if data['sourceStatus']=='SUCCESS':
        redis_conn.incrEntityCounter("HAQR", "sourceSucess", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "sourceFailure", sort=False, incrBy=1)
        return

    if data['platformCompilationStatus']['Impala']['queryStatus']=="SUCCESS":
        redis_conn.incrEntityCounter("HAQR", "impalaSuccess", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "impalaFail", sort=False, incrBy=1)

    if data['platformCompilationStatus']['Impala']['clauseStatus']['Select']['clauseStatus']=="SUCCESS":
        redis_conn.incrEntityCounter("HAQR", "impalaSelectSuccess", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "impalaSelectFail", sort=False, incrBy=1)
        if 'subClauseList' in data['platformCompilationStatus']['Impala']['clauseStatus']['Select']:
            for subClause in data['platformCompilationStatus']['Impala']['clauseStatus']['Select']['subClauseList']:
                if subClause['clauseStatus']=="SUCCESS":
                    redis_conn.incrEntityCounter("HAQR", "impalaSelectSubClauseSuccess", sort=False, incrBy=1)
                else:
                    redis_conn.incrEntityCounter("HAQR", "impalaSelectSubClauseFailure", sort=False, incrBy=1)
                    redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseSelectFailure", sort=False, incrBy=1)
    if data['platformCompilationStatus']['Impala']['clauseStatus']['From']['clauseStatus']=="SUCCESS":
        redis_conn.incrEntityCounter("HAQR", "impalaFromSuccess", sort=False, incrBy=1)
    elif data['platformCompilationStatus']['Impala']['clauseStatus']['From']['clauseStatus']=="AUTO_SUGGEST":
        redis_conn.incrEntityCounter("HAQR", "impalaFromAutoCorrect", sort=False, incrBy=1)
    else:
        redis_conn.incrEntityCounter("HAQR", "impalaFromFailure", sort=False, incrBy=1)
    if 'subClauseList' in data['platformCompilationStatus']['Impala']['clauseStatus']["From"]:
        for subClause in data['platformCompilationStatus']['Impala']['clauseStatus']["From"]['subClauseList']:
            if subClause['clauseStatus']=="SUCCESS":
                redis_conn.incrEntityCounter("HAQR", "impalaFromSubClauseSuccess", sort=False, incrBy=1)
            elif subClause['clauseStatus']=="AUTO_SUGGEST":
                redis_conn.incrEntityCounter("HAQR", "impalaFromSubClauseAutoCorrect", sort=False, incrBy=1)
            else:
                redis_conn.incrEntityCounter("HAQR", "impalaFromSubClauseFailure", sort=False, incrBy=1)
                redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseFromFailure", sort=False, incrBy=1)

    if "Group By" in data['platformCompilationStatus']['Impala']['clauseStatus']:
        if data['platformCompilationStatus']['Impala']['clauseStatus']["Group By"]['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaGroupBySuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaGroupByFailure", sort=False, incrBy=1)
            if 'subClauseList' in data['platformCompilationStatus']['Impala']['clauseStatus']["Group By"]:
                for subClause in data['platformCompilationStatus']['Impala']['clauseStatus']["Group By"]['subClauseList']:
                    if subClause['clauseStatus']=="SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaGroupBySubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaGroupBySubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseGroupByFailure", sort=False, incrBy=1)

    if "Where" in data['platformCompilationStatus']['Impala']['clauseStatus']:
        if data['platformCompilationStatus']['Impala']['clauseStatus']["Where"]['clauseStatus']=="SUCCESS":
            redis_conn.incrEntityCounter("HAQR", "impalaWhereSuccess", sort=False, incrBy=1)
        else:
            redis_conn.incrEntityCounter("HAQR", "impalaWhereFailure", sort=False, incrBy=1)
            if 'subClauseList' in data['platformCompilationStatus']['Impala']['clauseStatus']["Where"]:
                for subClause in data['platformCompilationStatus']['Impala']['clauseStatus']["Where"]['subClauseList']:
                    if subClause['clauseStatus']=="SUCCESS":
                        redis_conn.incrEntityCounter("HAQR", "impalaWhereSubClauseSuccess", sort=False, incrBy=1)
                    else:
                        redis_conn.incrEntityCounter("HAQR", "impalaWhereSubClauseFailure", sort=False, incrBy=1)
                        redis_conn.incrEntityCounter(eid, "HAQRimpalaQueryByClauseWhereFailure", sort=False, incrBy=1)
    return

def compile_query(mongoconn, redis_conn, compilername, data_dict):
    """
    Interact with the compiler service to compile the query.
    Column resolution is performed as a second pass if :
       - the query has unqualified columns.
       - metadata is available for the tables in the query.
    """
    opcode = 1
    retries = 3
    response = tclient.send_compiler_request(opcode, data_dict, retries)

    compile_doc = None
    if not response.isSuccess:
        logging.error("compiler request failed")
    else:
        compile_doc = loads(response.result)

    if compile_doc == None:
        logging.error("Got Null compiler doc from compiler")
        return compile_doc

    compiler_data = compile_doc[compilername]

    for key in compile_doc:
        if key == compilername:
            if "queryExtendedHash" in compile_doc[key]:
                q_hash =  compile_doc[key]["queryExtendedHash"]
            elif "queryHash" in compile_doc[key]:
                q_hash =  compile_doc[key]["queryHash"]
            else:
                logging.exception("No query hash found in compile_doc")

    entity = mongoconn.searchEntity({"md5":q_hash})
    # if there is an unqualified column, try again with catalog included
    if entity is None and "unqualifiedColumn" in compiler_data and\
	 compiler_data["unqualifiedColumn"] and\
         "InputTableList" in compiler_data:
        try:
            compile_doc = compile_query_with_catalog(mongoconn, redis_conn, compilername, data_dict, compile_doc)
        except:
            logging.exception("CAUGHT: {0}\n".format(traceback.format_exc()))

    return compile_doc


def compile_query_with_catalog(mongoconn, redis_conn, compilername, data_dict, compile_doc):
    compiler_data = compile_doc[compilername]
    table_dict = {}
    # get list of input tables
    for table_entry in compiler_data["InputTableList"]:
        table_dict[table_entry["TableName"]] = []

    if not table_dict:
        """
        No tables from the compiler.
        """
        return compile_doc


    # get the tables data.
    for entry in mongoconn.db.entities.find({"etype":"SQL_TABLE", "name": { "$in" : table_dict.keys()}},
                                            {"eid":1, "name":1}):
        table_eid = entry["eid"]
        column_eids = []
        for rel in redis_conn.getRelationships(table_eid, None, "TABLE_COLUMN"):
            column_eids.append(rel["end_en"])

        logging.debug(column_eids)
        for column_entry in mongoconn.db.entities.find({"etype":"SQL_TABLE_COLUMN",
                                                        "eid": { "$in" : column_eids}},
                                                        {"name":1}):
            c_split = column_entry["name"].split(".")
            if len(c_split) == 2:
                table_dict[entry["name"]].append(c_split[1])
            else:
                table_dict[entry["name"]].append(column_entry["name"])

    # filter out tables with no data
    nonempty_dict = {}
    for table in table_dict:
        if len(table_dict[table]) != 0:
            nonempty_dict[table] = table_dict[table]
    table_dict = nonempty_dict

    if len(table_dict.keys()) == 0:
        return compile_doc

    try:
        opcode = 10
        retries = 3
        data_dict["catalog"] = dumps(table_dict)
        response = tclient.send_compiler_request(opcode, data_dict, retries)

        if not response.isSuccess:
            logging.warn("compiler request returned isSuccess false")
        else:
            compile_doc = loads(response.result)
    except:
        logging.exception("CAUGHT: opcode 10 exception {0}\n".format(traceback.format_exc()))

    return compile_doc


def callback(ch, method, properties, body):
    startTime = time.time()
    dbAdditions = [0,0]
    tmpAdditions = [0,0]
    msg_dict = loads(body)

    logging.info("compiler Got message "+ str(msg_dict))


    """
    Validate the message.
    """
    if not msg_dict.has_key("tenant") or \
       not msg_dict.has_key("job_instances"):
        logging.error("Invalid message received\n")

    tenant = msg_dict["tenant"]
    instances = msg_dict["job_instances"]
    try:
        received_msgID = msg_dict["message_id"]
    except:
        received_msgID = None
    uid = None
    db = None

    client = getMongoServer(tenant)
    log_dict = {'tenant':tenant, 'tag': 'compileservice'}
    if 'uid' in msg_dict:
        log_dict['uid'] = msg_dict['uid']
    if 'opcode' in msg_dict:
        log_dict['opcode'] = msg_dict['opcode']
    clog = LoggerCustomAdapter(logging.getLogger(__name__), log_dict)

    if "opcode" in msg_dict and msg_dict["opcode"] == "HbaseDDL":
        clog.debug("Got the opcode of Hbase")
        db = client[tenant]
        redis_conn = RedisConnector(tenant)
        process_hbase_ddl_request(ch, properties, tenant, instances, db, redis_conn)
        """
        Read the input and respond.
        """
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if "opcode" in msg_dict and msg_dict["opcode"] == "MongoTransform":
        clog.debug("Got the opcode For Mongo Translation")
        process_mongo_rewrite_request(ch, properties, tenant, instances)

        """
        Read the input and respond.
        """
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if "opcode" in msg_dict and msg_dict["opcode"] == "scale_mode":
        clog.debug("Got the opcode for scale mode analysis")
        if 'uid' in msg_dict:
            uid = msg_dict['uid']
            db = client[tenant]
            redis_conn = RedisConnector(tenant)
            if not checkUID(redis_conn, uid):
                ch.basic_ack(delivery_tag=method.delivery_tag)
                clog.error("Invalid uid, dropping scale mode message")
                return
        else:
            clog.error("No uid, dropping scale mode message")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        redis_conn = RedisConnector(tenant)
        collection = client[tenant].uploadStats
        smc = ScaleModeConnector(tenant)
        process_scale_mode(tenant, uid, instances, smc, clog)
        decrementPendingMessage(collection, redis_conn, uid, received_msgID)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if msg_dict.has_key('uid'):
        uid = msg_dict['uid']

        """
        Check if this is a valid UID. If it so happens that this flow has been deleted,
        then drop the message.
        """
        db = client[tenant]
        redis_conn = RedisConnector(tenant)
        if not checkUID(redis_conn, uid):
            """
            Just drain the queue.
            """
            #connection1.basicAck(ch,method)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        collection = client[tenant].uploadStats
        redis_conn.incrEntityCounter(uid, 'Compiler.count', incrBy = 1)
    else:
        """
        We do not expect anything without UID. Discard message if not present.
        """
        #connection1.basicAck(ch,method)
        ch.basic_ack(delivery_tag=method.delivery_tag)

        return

    mongoconn = Connector.getConnector(tenant)
    if mongoconn is None:
        mongoconn = MongoConnector({'client':client, 'context':tenant, \
                                    'create_db_if_not_exist':True})

    redis_conn = RedisConnector(tenant)
    smc = ScaleModeConnector(tenant)

    compconfig = ConfigParser.RawConfigParser()
    compconfig.read("/etc/xplain/compiler.cfg")

    source_platform = None
    if "source_platform" in msg_dict:
        source_platform = msg_dict["source_platform"]

    """
    Generate the CSV from the job instances.
    """
    msg_data = None
    counter = 0
    for inst in instances:
        compile_doc = None
        prog_id = ""
        if "entity_id" in inst:
            prog_id = inst["entity_id"]
            try:
                entity = mongoconn.getEntity(prog_id)
            except:
                continue

        if "data" in inst:
            msg_data = inst["data"]

        query = inst["query"].encode('utf-8').strip()
        clog.debug("Program Entity : {0}, eid {1}\n".format(query, prog_id))

        clog.debug("Event received for {0}, entity {1}\n".format(tenant, prog_id))

        """
          Parameters required to create a query entity in the system.
          entity_id, query, tenant, profile documents, source_platform.
        """
        comp_outs = {}

        """
          Get the list of compilers we need to run.
          Run each valid compiler we find.
        """
        for section in compconfig.sections():
            compilername = ""
            additonalparams = ""
            if not compconfig.has_option(section, "CompilerType"):
                continue

            compilername = compconfig.get(section, "CompilerType")
            if compconfig.has_option(section, "AdditionalParameter") and\
                len(compconfig.get(section, "AdditionalParameter")) > 0:
                additonalparmas = compconfig.get(section, "AdditionalParameter")

            try:
                stats_newdbs_key = "Compiler." + compilername + ".newDBs"
                stats_newtables_key = "Compiler." + compilername + ".newTables"
                stats_runsuccess_key = "Compiler." + compilername + ".run_success"
                stats_runfailure_key = "Compiler." + compilername + ".run_failure"
                stats_success_key = "Compiler." + compilername + ".success"
                stats_failure_key = "Compiler." + compilername + ".failure"

                data_dict = { "input_query": query,
                              "Compiler": compilername, "EntityId": prog_id, "TenantId": tenant, "uid":uid}
                if source_platform is not None:
                    data_dict["source_platform"] = source_platform

                compile_doc = compile_query(mongoconn, redis_conn, compilername, data_dict)
                """
                It is possible the tenant has been cleared. If this is the case then do not add an new entities.
                """

                if not checkUID(redis_conn, uid):
                    """
                    Just drain the queue.
                    """
                    mongoconn.close()
                    #connection1.basicAck(ch,method)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                if compile_doc == None:
                    redis_conn.incrEntityCounter(uid, stats_runfailure_key, incrBy = 1)
                    redis_conn.incrEntityCounter(uid, stats_runsuccess_key, incrBy = 0)
                    continue
                else:
                    for key in compile_doc:
                        comp_outs[key] = compile_doc[key]

            except:
                clog.exception("Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))
                if msg_dict.has_key('uid'):
                    redis_conn.incrEntityCounter(uid, stats_runfailure_key, incrBy = 1)
                    redis_conn.incrEntityCounter(uid, stats_runsuccess_key, incrBy = 0)
                #mongoconn.updateProfile(entity, "Compiler", section, {"Error":traceback.format_exc()})

        try:
            context = Compiler_Context()
            context.test_mode = False
            context.tables = []
            context.queue = []

            if 'test_mode' in msg_dict:
                context.test_mode = True

            temp_msg = {'test_mode':1} if context.test_mode else {'message_id': received_msgID}

            entity, opcode = processCompilerOutputs(mongoconn, redis_conn, ch, collection, tenant, uid, query, msg_data, comp_outs, source_platform, smc, context, clog, inst["tagArray"], inst["countArray"])
            if entity is not None and opcode is not None:
                sendAnalyticsMessage(mongoconn, redis_conn, ch, collection, tenant, uid, entity, opcode, temp_msg)
            else:
                redis_conn.incrEntityCounter(uid, 'processed_queries', incrBy = 1)
        except:
            redis_conn.incrEntityCounter(uid, 'processed_queries', incrBy = 1)
            clog.exception("Failure in processing compiler output for Tenent {0}, Entity {1}, {2}\n".format(tenant, prog_id, traceback.format_exc()))

        if not usingAWS:
            continue


    logging.info("Event Processing Complete")

    endTime = time.time()
    #send stats to datadog
    if statsd:
        totalTime = ((endTime - startTime) * 1000)
        statsd.timing("compileservice.per.msg.time", totalTime, tags=["tenant:"+tenant, "uid:"+uid])
    if msg_dict.has_key('uid'):
        #if uid has been set, the variable will be set already
        redis_conn.incrEntityCounter(uid, 'Compiler.time', incrBy = endTime-startTime)

    mongoconn.close()
    connection1.basicAck(ch,method)
    callback_params = {'tenant':tenant, 'connection':connection1, 'channel':ch, 'uid':uid, 'queuename':'advanalytics'}
    decrementPendingMessage(collection, redis_conn, uid, received_msgID, end_of_phase_callback, callback_params)

connection1 = RabbitConnection(callback, ['compilerqueue'], ['mathqueue', 'elasticpub'], {})

logging.info("BaazCompiler going to start Consuming")

connection1.run()

#logging.debug("Closing BaazCompiler")
