#!/usr/bin/env python

import time
import datetime
import pika
import socket
import uuid
import requests
from json import *
import botocore.session
import ConfigParser

from flightpath.services.RabbitMQConnectionManager import *
from flightpath.Provenance import getMongoServer
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
import navopt_pb2
from boto.s3.key import Key
import boto

BAAZ_DATA_ROOT="/mnt/volume1/"
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

config = ConfigParser.RawConfigParser ()
config.read("/var/Baaz/hosts.cfg")
usingAWS = config.getboolean("mode", "usingAWS")

bucket_location = "partner-logs"
log_bucket_location = "xplain-servicelogs"

CLUSTER_MODE = config.get("ApplicationConfig", "mode")
CLUSTER_NAME = config.get("ApplicationConfig", "clusterName")

if CLUSTER_MODE is None:
    CLUSTER_MODE = 'production'


if CLUSTER_NAME is not None:
    bucket_location = CLUSTER_NAME

class ApiRpcClient(object):
    def __init__(self):

        rabbitservers = get_rabbit_servers()
        credentials = pika.PlainCredentials('xplain', 'xplain')
        vhost = 'xplain'

        for rabbit_server in rabbitservers:
            try:
                credentials = pika.PlainCredentials(rabbit_server['username'], rabbit_server['password'])
                parameters = pika.ConnectionParameters(rabbit_server['host'], rabbit_server['port'], RABBIT_VHOST, credentials)
                self.connection = BlockingConnection(parameters)
                print self.connection
                break
            except:
                print "Failed"
                pass

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print "Publish to APIServicequeue..."
        self.channel.basic_publish(exchange='',
                                   routing_key='apiservicequeue',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=n)
        while self.response is None:
            self.connection.process_data_events()
        return self.response

    def sendMessage(self, msg_dict):
        self.channel.basic_publish(exchange='', routing_key='ftpupload', body=msg_dict)
    def close(self):
        self.connection.close()

#api_rpc = ApiRpcClient()


class NavOptApiServer(navopt_pb2.BetaNavOptServicer):
    print 'Call inside NavOptApiServer'
 
    def createTenant(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.userGroup 
        msg_dict = {'email':str(request.userGroup), 'opcode':'CreateTenant'}
        response = api_rpc.call(dumps(msg_dict))
        response = loads(response)
        print "Api Service response", response
        ret_response = navopt_pb2.CreateTenantResponse()
        ret_response.tenant = response['tenant']
        api_rpc.close()
        return ret_response

    def getS3url(self, request, context):
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant

        session = botocore.session.get_session()
        client = session.create_client('s3')
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
        filep = "/" + timestr + "/" + request.fileName
        dest = "partner-logs" + "/" + request.tenant + filep
        presigned_url = client.generate_presigned_url('put_object', Params = 
                                     {'Bucket': bucket_location, 'Key': dest}, ExpiresIn = 300)
 
        print "Api Service response", presigned_url
        ret_response = navopt_pb2.GetS3urlResponse()
        ret_response.url = presigned_url
        return ret_response

    def getTenant(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.email 
        msg_dict = {'email':str(request.email), 'opcode':'GetTenant'}
        response = api_rpc.call(dumps(msg_dict))
        response = loads(response)
        print "Api Service response", response
        ret_response = navopt_pb2.GetTenantResponse()
        ret_response.tenant = response['tenant']
        api_rpc.close()
        return ret_response

    def convert_top_tables(self, response):
        ret = navopt_pb2.GetTopTablesResponse()
        if 'ret_data' in response:
            for entry in response['ret_data']:
                tables = navopt_pb2.TopTables()
                if 'columnCount' in entry:
                    tables.columnCount = entry['columnCount']
                if 'name' in entry:
                    tables.name = entry['name']
                if 'patternCount' in entry:
                    tables.patternCount = entry['patternCount']
                if 'workloadPercent' in entry:
                    tables.workloadPercent = entry['workloadPercent']
                if 'total' in entry:
                    tables.total = int(entry['total'])
                if 'type' in entry:
                    tables.type = entry['type']
                if 'eid' in entry:
                    tables.eid = entry['eid']
                if 'workloadPercent' in entry:
                    tables.workloadPercent = entry['workloadPercent']
                ret.results.extend([tables])
        if 'next' in response:
            ret.nextToken = response['next']
        #print "Ret:", ret, "tables:", ret.results
        return ret

        
    def updateUploadStats(self, tenant, filename, sourcePlatform, col_delim=None, row_delim=None, headerInfo=None):
        ret = navopt_pb2.UploadResponse()
        client = getMongoServer(tenant)
        db = client[tenant]
        userclient = getMongoServer('xplainDb')
        userdb = userclient['xplainIO']
        redis_conn = RedisConnector(tenant)
        #mark start of upload process
        db.uploadStats.update({ 'uid': '0' }, {'$set': { 'done': False }}, upsert=True)
        fileGuid = uuid.uuid4();
        db.uploadSessionUIDs.update({ "uploadSession": "uploadSession" }, {'$push': { 'session': str(fileGuid) }}, upsert=True)
        userdb.activeUploadsUIDs.insert({'guid': tenant, 'upUID': fileGuid})
        fileTimestamp = time.time()
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
        #newFileName = filename.split('/', 2)[2] 
        newFileName = timestr + "/" + filename 
        #update upload stats
        objectToInsert = {
            'tenent': tenant,
            'filename': newFileName,
            'uid': str(fileGuid),
            'timestamp': fileTimestamp,
            'active': True,
            'source_platform': sourcePlatform
        }
        db.uploadStats.insert(objectToInsert)
        uidKey = tenant + ":uid:" + str(fileGuid)
        redis_conn.r.mset({uidKey: objectToInsert['active']})
        msg_dict = {
            'tenent': tenant,
            #'filename': datetime.date.today() + '/' + filename,
            'filename': newFileName,
            'source_platform': sourcePlatform,
            'uid': str(fileGuid),
            'header_info': headerInfo
        }
     
        print "The msg dict:", msg_dict 
        if row_delim:
            if row_delim == "\\n":
                row_delim = "\n"
            msg_dict['row_delim'] = row_delim
        if col_delim:
            msg_dict['col_delim'] = col_delim 
        api_rpc = ApiRpcClient()
        api_rpc.sendMessage(dumps(msg_dict));
        api_rpc.close()
        ret.status.workloadId = str(fileGuid)
        return ret

    def convert_top_databases(self, response):
        ret = navopt_pb2.GetTopDatabasesResponse()
        if 'ret_data' in response:
            for entry in response['ret_data']:
                db = navopt_pb2.TopDatabases()
                if 'instanceCount' in entry:
                    db.instanceCount = entry['instanceCount']
                if 'dbName' in entry:
                    db.dbName = entry['dbName']
                if 'totalTableCount' in entry:
                    db.totalTableCount = entry['totalTableCount']
                if 'workloadPercent' in entry:
                    db.workloadPercent = entry['workloadPercent']
                if 'totalQueryCount' in entry:
                    db.totalQueryCount = int(entry['totalQueryCount'])
                if 'eid' in entry:
                    db.eid = entry['eid']
                ret.results.extend([db])
        if 'next' in response:
            ret.nextToken = response['next']
        return ret

    def getTopDatabases(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopDataBases'}
        if request.pageSize != 0:
            msg_dict['pageSize'] = request.pageSize
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_databases(loads(response))
        api_rpc.close()
        return ret_response

    def getTopTables(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopTables'}
        if request.dbName != "":
            msg_dict['dbname'] = request.dbName
        if request.pageSize != 0:
            msg_dict['pageSize'] = request.pageSize
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        print "Sending Msg Dict:", msg_dict
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_tables(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response
        #return navopt_pb2.GetTablesResponse(results=ret_response)
        #return navopt_pb2.GetTablesResponse(eid='007',
        #                                    name='James Bond')

    def convert_top_queries(self, response):
        ret = navopt_pb2.GetTopQueriesResponse()
        if 'ret_data' in response:
            for entry in response['ret_data']:
                queries = navopt_pb2.TopQueries()
                if 'impalaCompatible' in entry:
                    queries.impalaCompatible = entry['impalaCompatible']
                if 'hiveCompatible' in entry:
                    queries.hiveCompatible = entry['hiveCompatible']
                if 'instanceCount' in entry:
                    queries.instanceCount = int(entry['instanceCount'])
                if 'elapsedTime' in entry:
                    queries.elapsedTime = entry['elapsedTime']
                if 'complexity' in entry:
                    queries.complexity = entry['complexity']
                if 'eid' in entry:
                    queries.qid = entry['eid']
                if 'custom_id' in entry:
                    queries.customId = entry['custom_id']
                queries.querySignature.extend(entry['character'])
                ret.results.extend([queries])
        if 'next' in response:
            ret.nextToken = response['next']
        return ret

    def getTopQueries(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopQueries'}
        if request.pageSize != 0:
            msg_dict['pageSize'] = request.pageSize
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_queries(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def get_col_info(self, columns, entry):
        #columns = navopt_pb2.TopColumns()
        if 'columnCount' in entry:
            columns.columnCount = int(entry['columnCount'])
        if 'groupbyCount' in entry:
            columns.groupbyCol = entry['groupbyCount']
        if 'selectCount' in entry:
            columns.selectCol = entry['selectCount']
        if 'filterCount' in entry:
            columns.filterCol = entry['filterCount']
        if 'joinCount' in entry:
            columns.joinCol = entry['joinCount']
        if 'columnName' in entry:
            columns.columnName = entry['columnName']
        if 'tableName' in entry:
            columns.tableName = entry['tableName']
        if 'tid' in entry:
            columns.tid = entry['tid']
        if 'cid' in entry:
            columns.cid = entry['cid']
        if 'workloadPercent' in entry:
            columns.workloadPercent = entry['workloadPercent']
        if 'dbName' in entry:
            columns.dbName = entry['dbName']
        return columns
      
    def convert_top_columns(self, entry):
        ret = navopt_pb2.GetTopColumnsResponse()
        if 'groupbyColumns' in entry:
            for value in entry['groupbyColumns']:
                self.get_col_info(ret.groupbyColumns.add(), value)
            #print "The Columns:", val
            #ret.groupbyColumns.extend(columns)
        if 'orderbyColumns' in entry:
            for value in entry['orderbyColumns']:
                #columns = self.get_col_info(value)
                #ret.orderbyColumns.extend([columns])
                self.get_col_info(ret.orderbyColumns.add(), value)
        if 'joinColumns' in entry:
            for value in entry['joinColumns']:
                #columns = self.get_col_info(entry['joinColumns'])
                #ret.joinColumns.extend([columns])
                self.get_col_info(ret.joinColumns.add(), value)
        if 'selectColumns' in entry:
            #columns = self.get_col_info(entry['selectColumns'])
            #ret.selectColumns.extend([columns])
            for value in entry['selectColumns']:
                #columns = self.get_col_info(entry['joinColumns'])
                #ret.joinColumns.extend([columns])
                self.get_col_info(ret.selectColumns.add(), value)
        if 'filterColumns' in entry:
            #columns = self.get_col_info(entry['orderbyColumns'])
            #ret.orderbyColumns.extend([columns])
            for value in entry['filterColumns']:
                #columns = self.get_col_info(entry['joinColumns'])
                #ret.joinColumns.extend([columns])
                self.get_col_info(ret.filterColumns.add(), value)
        #print "Ret:", ret, "tables:", ret.results
        if 'next' in entry:
            ret.nextToken = entry['next']
        return ret

    def getTopColumns(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopColumns'}
        if request.dbName != "":
            msg_dict['dbname'] = request.dbName
        if request.tableName != "":
            msg_dict['tablename'] = request.tableName
        if request.dbTableList != []:
            msg_dict['dbTblist'] = list(request.dbTableList)
        if request.pageSize != 0:
            msg_dict['pageSize'] = request.pageSize
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_columns(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def convert_top_filters(self, response):
        ret = navopt_pb2.GetTopFiltersResponse()
        for entry in response['patterns']:
            #filters = navopt_pb2.TopFilters()
            filters = ret.results.add()
            if 'totalQueryCount' in entry:
                filters.totalQueryCount = entry['totalQueryCount']
            if 'tableName' in entry:
                filters.tableName = entry['tableName']
            if 'tid' in entry:
                filters.tid = str(entry['tid'])
            if 'fullColumns' in entry:
                filters.columns.extend(entry['fullColumns'])
            filters.qids.extend(entry['qids'])
            if 'popularValues' in entry:
                for val in entry['popularValues']:
                    pop_value = filters.popularValues.add()
                    if 'count' in val:
                        pop_value.count = val['count']
                    if 'group' in val:
                        for group in val['group']:
                            group_val = pop_value.group.add()
                            if 'fullColumnName' in group:
                                group_val.columnName = group['fullColumnName']
                            if 'isLiteral' in group:
                                group_val.isLiteral = group['isLiteral']
                            if 'literal' in group:
                                group_val.literal = group['literal']
                            if 'op' in group:
                                group_val.op = group['op']
                            #pop_value.group.extend([group_val])
                    #filters.popularValues.extend([pop_value])
            #ret.results.extend([filters])
        if 'next' in response:
            ret.nextToken = str(response['next'])
        print "Ret:", ret, "tables:", ret.results
        return ret

    def getTopFilters(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopAccessPatterns', 'pattern': 'filter'}
        if request.dbName != "":
            msg_dict['dbname'] = request.dbName
        if request.tableName != "":
            msg_dict['tablename'] = request.tableName
        if request.colList != []:
            msg_dict['columns'] = list(request.colList)
        if request.dbTableList != []:
            msg_dict['dbTblist'] = list(request.dbTableList)
        if request.pageSize != 0:
            msg_dict['pageSize'] = request.pageSize
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_filters(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def convert_top_aggs(self, response):
        ret = navopt_pb2.GetTopAggsResponse()
        for entry in response['patterns']:
            #print "entry:", entry
            agg = navopt_pb2.TopAgg()
            if 'aggregateClause' in entry:
                agg.aggregateClause = entry['aggregateClause']
            if 'aggregateFunction' in entry:
                agg.aggregateFunction = entry['aggregateFunction']
            if 'functionType' in entry:
                agg.functionType = entry['functionType']
            if 'location' in entry:
                agg.location = entry['location']
            if 'totalQueryCount' in entry:
                agg.totalQueryCount = entry['totalQueryCount']
            if 'aggregateColumns' in entry and entry['aggregateColumns']:
                for val in entry['aggregateColumns']:
                    agg_info = agg.aggregateInfo.add()
                    if 'columnName' in val:
                        agg_info.columnName = val['columnName']
                    if 'tableName' in val:
                        agg_info.tableName = val['tableName']
                    if 'databaseName' in val:
                        agg_info.databaseName = val['databaseName']
            ret.results.extend([agg])
        #print "Ret:", ret, "tables:", ret.results
        if 'next' in response:
            ret.nextToken = str(response['next'])
        return ret

    def getTopAggs(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopAccessPatterns', 'pattern': 'AggregateFunction'}
        if request.dbTableList != []:
            msg_dict['dbTblist'] = list(request.dbTableList)
        if request.pageSize != 0:
            msg_dict['pageSize'] = request.pageSize
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_aggs(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def convert_top_joins(self, response):
        ret = navopt_pb2.GetTopJoinsResponse()
        if 'ret_data' in response:
            for entry in response['ret_data']:
                join = navopt_pb2.TopJoins()
                if 'totalQueryCount' in entry:
                    join.totalQueryCount = entry['totalQueryCount']
                if 'totalTableCount' in entry:
                    join.totalTableCount = entry['totalTableCount']
                if 'joinType' in entry:
                    join.joinType = entry['joinType']
                if 'columns' in entry:
                    for val in entry['columns']:
                        jcol = join.joinCols.add()
                        jcol.columns.extend(val)
                if 'tables' in entry:
                    join.tables.extend(entry['tables'])
                if 'queryIds' in entry:
                    join.queryIds.extend(entry['queryIds'])
                ret.results.extend([join])
        if 'next' in response:
            ret.nextToken = response['next']
        print "Ret:", ret, "tables:", ret.results
        return ret

    def getTopJoins(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopJoins'}
        if request.dbTableList != []:
            msg_dict['dbTblist'] = list(request.dbTableList)
        if request.pageSize != 0:
            msg_dict['pageSize'] = request.pageSize
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        print "Msg Dict:", msg_dict
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_joins(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def convert_DesignBucket(self, response):
        ret = navopt_pb2.GetDesignBucketResponse()
        for entry in response:
            #print "entry:", entry
            buck = navopt_pb2.DesignBucket()
            if 'bucketName' in entry:
                buck.bucketName = entry['bucketName']
            if 'description' in entry and entry['description']:
                buck.description = entry['description']
            if 'numQueries' in entry:
                buck.numQueries = entry['numQueries']
            if 'numTables' in entry:
                buck.numTables = entry['numTables']
            ret.results.extend([buck])
        #print "Ret:", ret, "tables:", ret.results
        return ret

    def getDesignBucket(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'DesignBucket', 'query':request.query,
                    'sourcePlatform':request.sourcePlatform, 'targetPlatform':request.targetPlatform}
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_DesignBucket(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def convert_QueryCompatible(self, response):
        ret = navopt_pb2.GetQueryCompatibleResponse()
        if 'status' in response:
            ret.status = response['status']
        if 'parseError' in response:
            ret.parseError = response['parseError']
        if 'errorClause' in response:
            ret.clauseName = response['errorClause']
        if 'clauseString' in response:
            ret.clauseString = response['clauseString']
        if 'errorDetail' in response:
            # ret.queryError = navopt_pb2.QueryError()
            if 'encounteredString' in response['errorDetail']:
                ret.queryError.encounteredString = response['errorDetail']['encounteredString']
            if 'errorString' in response['errorDetail']:
                ret.queryError.errorString = response['errorDetail']['errorString']
            if 'expectedString' in response['errorDetail']:
                ret.queryError.expectedString = response['errorDetail']['expectedString']
        if 'clauseError' in response:
            # ret.clauseError = navopt_pb2.ClauseError()
            if 'startLocator' in response['clauseError']:
                # ret.clauseError.startLocator = navopt_pb2.HighLightInfo()
                if 'column' in response['clauseError']['startLocator']:
                    ret.clauseError.startLocator.column = response['clauseError']['startLocator']['column']
                if 'lineNum' in response['clauseError']['startLocator']:
                    ret.clauseError.startLocator.lineNum = response['clauseError']['startLocator']['lineNum']
                if 'tokenRank' in response['clauseError']['startLocator']:
                    ret.clauseError.startLocator.tokenRank = response['clauseError']['startLocator']['tokenRank']
                if 'offset' in response['clauseError']['startLocator']:
                    ret.clauseError.startLocator.offset = response['clauseError']['startLocator']['offset']
            if 'endLocator' in response['clauseError']:
                # ret.clauseError.endLocator = navopt_pb2.HighLightInfo()
                if 'column' in response['clauseError']['endLocator']:
                    ret.clauseError.endLocator.column = response['clauseError']['endLocator']['column']
                if 'lineNum' in response['clauseError']['endLocator']:
                    ret.clauseError.endLocator.lineNum = response['clauseError']['endLocator']['lineNum']
                if 'tokenRank' in response['clauseError']['endLocator']:
                    ret.clauseError.endLocator.tokenRank = response['clauseError']['endLocator']['tokenRank']
                if 'offset' in response['clauseError']['endLocator']:
                    ret.clauseError.endLocator.offset = response['clauseError']['endLocator']['offset']
           
        print "Ret:", ret
        return ret

    def getQueryCompatible(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant, 'Query:', request.query 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'QueryCompatible', 'query':request.query,
                    'targetPlatform':request.targetPlatform, 'sourcePlatform':request.sourcePlatform}
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_QueryCompatible(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def convert_QueryRisk(self, response):
        ret = navopt_pb2.GetQueryRiskResponse()
        if 'hive_risk' in response:
            for entry in response['hive_risk']:
                risk = navopt_pb2.RiskData()
                if 'risk' in entry:
                    risk.risk = entry['risk']
                if 'riskAnalysis' in entry:
                    risk.riskAnalysis = entry['riskAnalysis']
                if 'riskRecommendation' in entry:
                    risk.riskRecommendation = entry['riskRecommendation']
                ret.hiveRisk.extend([risk])
        if 'impala_risk' in response:
            for entry in response['impala_risk']:
                risk = navopt_pb2.RiskData()
                if 'risk' in entry:
                    risk.risk = entry['risk']
                if 'riskAnalysis' in entry:
                    risk.riskAnalysis = entry['riskAnalysis']
                if 'riskRecommendation' in entry:
                    risk.riskRecommendation = entry['riskRecommendation']
                ret.impalaRisk.extend([risk])
        if 'errorMsg' in response:
            ret.errorMsg = response['errorMsg']
        return ret

    def getQueryRisk(self, request, context):
        api_rpc = ApiRpcClient()
        '''
        # write query to a file
        filepath ="/tmp/"
        fileName = "riskUpload.sql"
        with open(filepath+fileName, 'w') as fp:
            fp.write(request.query)
        fp.close()
        # get s3 url
        session = botocore.session.get_session()
        client = session.create_client('s3')
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
        filep = "/" + timestr + "/" + fileName
        dest = "partner-logs" + "/" + request.tenant + filep
        presigned_url = client.generate_presigned_url('put_object', Params = 
                                     {'Bucket': bucket_location, 'Key': dest}, ExpiresIn = 300)
        #put file in bucket
        requests.put(presigned_url, data=open(filepath+fileName).read())
        #upload file
        ret_response = self.updateUploadStats(request.tenant, fileName, 'teradata', None, None)
        #check status
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetUploadStatus'}
        msg_dict['workloadId'] = ret_response.status.workloadId
        count = 0
        while count < 3:
            response = api_rpc.call(dumps(msg_dict))
            print "Got RESPONSE:", response
            response = loads(response)
            if response['status'] == 'in-progress' or response['status'] == 'waiting':
                time.sleep(10)
                count = count + 1
                continue
            if response['status'] == 'finished':
                break
            if response['status'] == 'failed':
                return
        '''
        #get Risk analysis
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'QueryRisk', 'query':request.query}
        if request.sourcePlatform != "":
            msg_dict['source_platform'] = request.sourcePlatform
        print "msg dict:", msg_dict
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_QueryRisk(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def getSimilarQueries(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'SimilarQueries', 'query':request.query,
                    'source_platform':request.sourcePlatform}
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_query_detail_data(loads(response), False)
        api_rpc.close()
        return ret_response

    def get_info_incompatible_queries(self, query, entry):
        #print "entry:", entry
        #query = navopt_pb2.IncompatibleQueries()
        if 'qid' in entry:
            query.qid = entry['qid']
        if 'where_count' in entry:
            query.whereError = entry['where_count']
        if 'from_count' in entry:
            query.fromError = entry['from_count']
        if 'select_count' in entry:
            query.selectError = entry['select_count']
        if 'groupby_count' in entry:
            query.groupbyError = entry['groupby_count']
        if 'orderby_count' in entry:
            query.orderbyError = entry['orderby_count']
        if 'other_count' in entry:
            query.otherError = entry['other_count']
        if 'where_clauses' in entry:
            query.whereClauses.extend(entry['where_clauses'])
        if 'from_clauses' in entry:
            query.fromClauses.extend(entry['from_clauses'])
        if 'select_clauses' in entry:
            query.selectClauses.extend(entry['select_clauses'])
        if 'join_clauses' in entry:
            query.joinClauses.extend(entry['join_clauses'])
        if 'orderby_clauses' in entry:
            query.orderbyClauses.extend(entry['orderby_clauses'])
        if 'groupby_clauses' in entry:
            query.groupbyClauses.extend(entry['groupby_clauses'])
        if 'other_clauses' in entry:
            query.otherClauses.extend(entry['other_clauses'])
        return query

    def convert_incompatible_queries(self, response):
        ret = navopt_pb2.GetHAQRResponse()
        for entry in response['impala']:
            self.get_info_incompatible_queries(ret.impala.add(), entry)
            #ret.impala.extend([query])
        for entry in response['hive']:
            self.get_info_incompatible_queries(ret.hive.add(), entry)
            #ret.hive.extend([query])
        #print "Ret:", ret, "tables:", ret.results
        return ret

    def getHAQR(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'IncompatibleQueries'}
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_incompatible_queries(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def get_stats_data(self, tenant, fileName):
        ret_dict = {}
        timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
        filename = timestr + "/" + fileName
        source = tenant + "/" + filename
        """
        Check if the file exists in S3.
        """
        if CLUSTER_NAME is not None:
            boto_conn = boto.connect_s3()
            bucket = boto_conn.get_bucket(bucket_location)
            source = "partner-logs/" + source
            file_key = bucket.get_key(source)
            if file_key is None:
                return ret_dict
        """
        Download the file and extract:
        """
        dest_file = BAAZ_DATA_ROOT + tenant + "/" + filename
        destination = os.path.dirname(dest_file)
        if not os.path.exists(destination):
            os.makedirs(destination)
        d_file = open(dest_file, "w+")
        file_key.get_contents_to_file(d_file)
        d_file.close()
        with open(dest_file) as json_data:
            ret_dict = json.load(json_data)
        return ret_dict
 
    def upload(self, request, context):
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        row_delim = None
        col_delim = None 
        headerInfo = []
        if request.rowDelim != "":
            row_delim = request.rowDelim
        if request.colDelim != "":
            col_delim = request.colDelim
        if request.headerFields:
            for entry in request.headerFields:
                entry_dict = {}
                entry = str(entry)
                entry = entry.split("\n")
                for val in entry:
                    if val == '':
                        continue
                    entry_dict[val.split(":")[0].strip()] = val.split(":")[1].strip(' "')
                print "entry:", entry_dict
                if 'coltype' in entry_dict:
                    if entry_dict['coltype'] == 'SQL_QUERY':
                        entry_dict['type'] = 'SQL_FULLTEXT'
                    else: 
                        entry_dict['type'] = entry_dict['coltype']
                    entry_dict.pop('coltype')
                else:
                    if entry_dict['name'] == "DATABASE":
                        entry_dict['type'] = 'DATABASE'
                headerInfo.append(entry_dict)

        if request.fileType == 1 or request.fileType == 2:
            stats = self.get_stats_data(request.tenant, request.fileName)
            api_rpc = ApiRpcClient()
            msg_dict = {'tenant':str(request.tenant), 'opcode':'UploadStats'}
            if request.fileType == 1:
                msg_dict['table_stats'] = stats
            else:
                msg_dict['column_stats'] = stats
            print "Message to Apiservice", msg_dict
            response = api_rpc.call(dumps(msg_dict))
            ret_response = navopt_pb2.UploadResponse()
            ret_response.status.state = 3 
            print "Api Service response", response, "Type:", type(loads(response))
            api_rpc.close()
        else:
            ret_response = self.updateUploadStats(request.tenant, request.fileName, request.sourcePlatform, col_delim, row_delim, headerInfo)
        return ret_response

    def convert_to_upload_status(self, response):
        ret = navopt_pb2.UploadStatusResponse()
        if 'status' in response:
            if response['status'] == 'in-progress':
                ret.status.state = 1
            if response['status'] == 'waiting':
                ret.status.state = 0
            if response['status'] == 'failed':
                ret.status.state = 4
            if response['status'] == 'finished':
                ret.status.state = 3
        ret.status.workloadId = response['workloadId']
        if 'errorMsg' in response:
            ret.status.statusMsg = response['errorMsg']
        if 'successQueries' in response:
            ret.status.successQueries = response['successQueries']
        if 'failedQueries' in response:
            ret.status.failedQueries = response['failedQueries']
        if 'failedQueryDetails' in response:
            for entry in response['failedQueryDetails']:
                query = navopt_pb2.FailedQuery()
                if 'query' in entry:
                    query.query = entry['query']
                if 'error' in entry:
                    query.error = entry['error']
                ret.status.failQueryDetails.extend([query])
        return ret

    def uploadStatus(self, request, context):
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        api_rpc = ApiRpcClient()
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetUploadStatus'}
        if request.workloadId != "":
            msg_dict['workloadId'] = request.workloadId
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_upload_status(loads(response))
        api_rpc.close()
        return ret_response

    def convert_to_workload_info(self, response):
        ret = navopt_pb2.WorkloadInfoResponse()
        for entry in response:
            #print "entry:", entry
            data = navopt_pb2.WorkloadData()
            if 'queries' in entry:
                data.queries = entry['queries']
            if 'workloadName' in entry:
                data.workloadName = entry['workloadName']
            if 'workloadId' in entry:
                data.workloadId = entry['workloadId']
            if 'source_platform' in entry:
                data.source_platform = entry['source_platform']
            if 'tenant' in entry:
                data.tenant = entry['tenant']
            if 'timestamp' in entry:
                data.timestamp = long(entry['timestamp'])
            if 'etype' in entry:
                data.etype = entry['etype']
            if 'active' in entry:
                data.active = entry['active']
            if 'processed_queries' in entry:
                data.processed_queries = entry['processed_queries']
            ret.results.extend([data])
        #print "Ret:", ret, "tables:", ret.results
        return ret

    def workloadInfo(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetWorkloadInfo'}
        if request.workloadId != "":
            msg_dict['workloadId'] = request.workloadId
        if request.inActive:
            msg_dict['inActive'] = request.inActive
        if request.details:
            msg_dict['details'] = request.details
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_workload_info(loads(response))
        api_rpc.close()
        return ret_response

    def convert_to_query_data(self, response):
        ret = navopt_pb2.GetQueriesResponse()
        for entry in response['data']:
            data = ret.results.add()
            if 'name' in entry:
                data.query = entry['name']
            if 'eid' in entry:
                data.qid = entry['eid']

        if 'next' in response:
            ret.nextToken = response['next']
        return ret

    def getQueries(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetQueries'}
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_query_data(loads(response))
        api_rpc.close()
        return ret_response
 
    def convert_to_query_detail_data(self, response, is_q_detail):
        if is_q_detail:
            ret = navopt_pb2.GetQueriesDetailResponse()
        else:
            ret = navopt_pb2.GetSimilarQueriesResponse()
           
        if 'query' in response:
            ret.query = response['query']
        if 'qid' in response:
            ret.qid = response['qid']
        if 'customId' in response:
            ret.customId = response['customId']
        if 'orderByCount' in response:
            ret.orderByCount = response['orderByCount']
        if 'groupByCount' in response:
            ret.groupByCount = response['groupByCount']
        if 'hiveCompatible' in response:
            ret.hiveCompatible = response['hiveCompatible']
        if 'impalaCompatible' in response:
            ret.impalaCompatible = response['impalaCompatible']
        if 'selectCount' in response:
            ret.selectCount = response['selectCount']
        if 'unionCount' in response:
            ret.unionCount = response['unionCount']
        if 'unionAllCount' in response:
            ret.unionAllCount = response['unionAllCount']
        if 'instanceCount' in response:
            ret.instanceCount = response['instanceCount']
        if 'joinCount' in response:
            ret.joinCount = response['joinCount']
        if 'filterCount' in response:
            ret.filterCount = response['filterCount']

        if 'tables' in response:
            for entry in response['tables']:
                data = navopt_pb2.QueryTable()
                if 'tableName' in entry:
                    data.tableName = entry['tableName']
                if 'tableType' in entry:
                    data.tableType = entry['tableType']
                if 'tid' in entry:
                    data.tid = entry['tid']
                if 'dbName' in entry:
                    data.dbName = entry['dbName']
                ret.table.extend([data])

        if 'SignatureKeywords' in response:
            ret.querySignature.extend(response['SignatureKeywords'])
        return ret

    def getQueriesDetail(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetQueryDetail'}
        if request.qid != "":
            msg_dict['qid'] = request.qid
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_query_detail_data(loads(response), True)
        api_rpc.close()
        return ret_response

    def convert_to_table_data(self, response):
        ret = navopt_pb2.GetTablesResponse()
        for entry in response['data']:
            data = ret.results.add()
            if 'name' in entry:
                data.name = entry['name']
            if 'eid' in entry:
                data.tid = entry['eid']

        if 'next' in response:
            ret.nextToken = response['next']
        return ret

    def getTables(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetTables'}
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_table_data(loads(response))
        api_rpc.close()
        return ret_response
 
    def convert_to_table_detail_data(self, response):
        ret = navopt_pb2.GetTablesDetailResponse()
  
        if 'name' in response:
            ret.name = response['name']
        if 'tid' in response:
            ret.tid = response['tid']
        if 'columnCount' in response:
            ret.columnCount = response['columnCount']
        if 'createCount' in response:
            ret.createCount = response['createCount']
        if 'selectCount' in response:
            ret.selectCount = int(response['selectCount'])
        if 'updateCount' in response:
            ret.updateCount = response['updateCount']
        if 'queryCount' in response:
            ret.queryCount = int(response['queryCount'])
        if 'insertCount' in response:
            ret.insertCount = response['insertCount']
        if 'deleteCount' in response:
            ret.deleteCount = response['deleteCount']
        if 'joinCount' in response:
            ret.joinCount = response['joinCount']
        if 'tid' in response:
            ret.tid = response['tid']
        if 'type' in response:
            ret.type = response['type']
        if 'table_ddl' in response and response['table_ddl']:
            ret.table_ddl = response['table_ddl']
        if 'iview_ddl' in response and response['iview_ddl']:
            ret.iview_ddl = response['iview_ddl']
        if 'view_ddl' in response and response['view_ddl']:
            ret.view_ddl = response['view_ddl']
        if 'workloadPercent' in response:
            ret.workloadPercent = response['workloadPercent']

        if 'columnStats' in response:
            for entry in response['columnStats']:
                #print "entry:", entry
                data = navopt_pb2.ColStats()
                if 'column_name' in entry:
                    data.columnName = entry['column_name']
                if 'num_distinct' in entry:
                    data.numDistinct = entry['num_distinct']
                if 'eid' in entry:
                    data.cid = entry['eid']
                if 'data_type' in entry:
                    data.dataType = entry['data_type']
                if 'num_nulls' in entry:
                    data.numNulls = entry['num_nulls']
                if 'avg_col_len' in entry:
                    data.avgColLen = entry['avg_col_len']
                ret.colStats.extend([data])

        if 'tableStats' in response:
            #data = navopt_pb2.TableStats()
            data = ret.tableStats
            if 'NUM_ROWS' in response['tableStats']:
                ret.tableStats.numRows = response['tableStats']['NUM_ROWS']
            if 'AVG_ROW_LEN' in response['tableStats']:
                ret.tableStats.avgRowLen = response['tableStats']['AVG_ROW_LEN']
            if 'ROW_RANGE' in response['tableStats']:
                ret.tableStats.rowRange = response['tableStats']['ROW_RANGE']
            if 'TABLE_NAME'in response['tableStats']:
                ret.tableStats.tableName = response['tableStats']['TABLE_NAME']
            #ret.tableStats.MergeFrom(data)
        
        if 'queryList' in response:
            for entry in response['queryList']:
                data = navopt_pb2.QueryList()
                if 'query' in entry:
                    data.query = entry['query']
                if 'eid' in entry:
                    data.qid = entry['eid']
                if 'instanceCount' in entry:
                    data.queryCount = entry['instanceCount']
                if 'character' in entry:
                    data.queryChar.extend(entry['character'])
                if 'impalaCompatible' in entry:
                    data.impalaCompatible = entry['impalaCompatible']
                if 'hiveCompatible' in entry:
                    data.hiveCompatible = entry['hiveCompatible']
                if 'complexity' in entry:
                    data.complexity = entry['complexity']
                ret.queryList.extend([data])

        if 'joinedTables' in response:
            for entry in response['joinedTables']:
                data = navopt_pb2.JoinTables()
                if 'joinpercent' in entry:
                    data.joinpercent = entry['joinpercent']
                if 'tableName' in entry:
                    data.tableName = entry['tableName']
                if 'tableEid' in entry:
                    data.tableEid = entry['tableEid']
                if 'joinColumns' in entry:
                    data.joinColumns.extend(entry['joinColumns'])
                if 'joincount' in entry:
                    data.numJoins = entry['joincount']
                ret.joinTables.extend([data])

        if 'topColumns' in response:
            for entry in response['topColumns']:
                data = navopt_pb2.TopCols()
                if 'name' in entry:
                    data.name = entry['name']
                if 'score' in entry:
                    data.score = entry['score']
                ret.topCols.extend([data])

        if 'topJoinColumns' in response:
            for entry in response['topJoinColumns']:
                data = navopt_pb2.TopCols()
                if 'name' in entry:
                    data.name = entry['name']
                if 'score' in entry:
                    data.score = entry['score']
                ret.topJoinCols.extend([data])

        print "Ret:", ret #"tables:", ret.results
        return ret

    def getTablesDetail(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetTableDetail'}
        if request.tid != "":
            msg_dict['eid'] = request.tid
        if request.tableName != "":
            msg_dict['name'] = request.tableName
        if request.dbName != "":
            msg_dict['dbname'] = request.dbName
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_table_detail_data(loads(response))
        api_rpc.close()
        return ret_response

    def convert_to_column_data(self, response):
        ret = navopt_pb2.GetColumnsResponse()
        for entry in response['data']:
            data = ret.results.add()
            if 'name' in entry:
                data.name = entry['name']
            if 'eid' in entry:
                data.cid = entry['eid']

        if 'next' in response:
            ret.nextToken = response['next']
        return ret

    def getColumns(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetColumns'}
        if request.startingToken != "":
            msg_dict['next'] = request.startingToken
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_column_data(loads(response))
        api_rpc.close()
        return ret_response

    def convert_to_column_detail_data(self, response):
        ret = navopt_pb2.GetColumnsDetailResponse()
  
        if 'columnName' in response:
            ret.columnName = response['columnName']
        if 'tableEid' in response:
            ret.tid = response['tableEid']
        if 'eid' in response:
            ret.cid = response['eid']
        if 'tableName' in response:
            ret.tableName = response['tableName']

        entry = response['stats']
        #print "entry:", entry
        data = navopt_pb2.ColStats()
        if 'column_name' in entry:
            data.columnName = entry['column_name']
        if 'num_distinct' in entry:
            data.numDistinct = entry['num_distinct']
        if 'eid' in entry:
            data.tid = entry['eid']
        if 'data_type' in entry:
            data.dataType = entry['data_type']
        if 'num_nulls' in entry:
            data.numNulls = entry['num_nulls']
        if 'avg_col_len' in entry:
            data.avgColLen = entry['avg_col_len']
        ret.colStats.extend([data])

        #print "Ret:", ret, "tables:", ret.results
        return ret

    def getColumnsDetail(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetColumnDetail'}
        if request.cid != "":
            msg_dict['cid'] = request.cid
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_column_detail_data(loads(response))
        api_rpc.close()
        return ret_response

def serve():  
    server = navopt_pb2.beta_create_NavOpt_server(NavOptApiServer())
    ip_addr = socket.gethostbyname(socket.gethostname())
    port = '8982'
    server.add_insecure_port(ip_addr+":"+port)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':  
    serve()  
