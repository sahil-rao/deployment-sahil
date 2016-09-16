#!/usr/bin/env python

import time
import datetime
import pika
import socket
import uuid
from json import *

from flightpath.services.RabbitMQConnectionManager import *
from flightpath.Provenance import getMongoServer
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
import navopt_pb2

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

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
        for entry in response:
            #print "entry:", entry
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
            ret.results.extend([tables])
        #print "Ret:", ret, "tables:", ret.results
        return ret

        
    def updateUploadStats(self, tenant, filename, sourcePlatform, col_delim=None, row_delim=None):
        ret = navopt_pb2.UploadResponse()
        client = getMongoServer(tenant)
        db = client[tenant]
        userclient = getMongoServer('xplainDb')
        userdb = userclient['xplainIO']
        redis_conn = RedisConnector(tenant)
        headerInfo = None
        #mark start of upload process
        db.uploadStats.update({ 'uid': '0' }, {'$set': { 'done': False }}, upsert=True)
        fileGuid = uuid.uuid4();
        db.uploadSessionUIDs.update({ "uploadSession": "uploadSession" }, {'$push': { 'session': str(fileGuid) }}, upsert=True)
        userdb.activeUploadsUIDs.insert({'guid': tenant, 'upUID': fileGuid})
        fileTimestamp = time.time()
        newFileName = filename.split('/', 2)[2] 
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

    def getTopTables(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopTables'}
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
        for entry in response:
            #print "entry:", entry
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
        #print "Ret:", ret, "tables:", ret.results
        return ret

    def getTopQueries(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopQueries'}
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
        return ret

    def getTopColumns(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopColumns'}
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_columns(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def convert_top_filters(self, response):
        ret = navopt_pb2.GetTopFiltersResponse()
        for entry in response:
            #filters = navopt_pb2.TopFilters()
            filters = ret.results.add()
            if 'totalQueryCount' in entry:
                filters.totalQueryCount = entry['totalQueryCount']
            if 'tableName' in entry:
                filters.tableName = entry['tableName']
            if 'tid' in entry:
                filters.tid = str(entry['tid'])
            filters.columns.extend(entry['columns'])
            filters.qids.extend(entry['qids'])
            if 'popularValues' in entry:
                for val in entry['popularValues']:
                    pop_value = filters.popularValues.add()
                    if 'count' in val:
                        pop_value.count = val['count']
                    if 'group' in val:
                        for group in val['group']:
                            group_val = pop_value.group.add()
                            if 'columnName' in group:
                                group_val.columnName = group['columnName']
                            if 'isLiteral' in group:
                                group_val.isLiteral = group['isLiteral']
                            if 'literal' in group:
                                group_val.literal = group['literal']
                            if 'op' in group:
                                group_val.op = group['op']
                            #pop_value.group.extend([group_val])
                    #filters.popularValues.extend([pop_value])
            #ret.results.extend([filters])
        print "Ret:", ret, "tables:", ret.results
        return ret

    def getTopFilters(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopAccessPatterns', 'pattern': 'filter'}
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_filters(loads(response))
        #print "Got Response:", ret_response
        api_rpc.close()
        return ret_response

    def convert_top_aggs(self, response):
        ret = navopt_pb2.GetTopAggsResponse()
        for entry in response:
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
            ret.results.extend([agg])
        #print "Ret:", ret, "tables:", ret.results
        return ret

    def getTopAggs(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant 
        msg_dict = {'tenant':str(request.tenant), 'opcode':'TopAccessPatterns', 'pattern': 'AggregateFunction'}
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_top_aggs(loads(response))
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
        msg_dict = {'tenant':str(request.tenant), 'opcode':'DesignBucket'}
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_DesignBucket(loads(response))
        #print "Got Response:", ret_response
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

    def upload(self, request, context):
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        row_delim = None
        col_delim = None 
        if request.rowDelim != "":
            row_delim = request.rowDelim
        if request.colDelim != "":
            col_delim = request.colDelim

        ret_response = self.updateUploadStats(request.tenant, request.s3location, request.sourcePlatform, col_delim, row_delim)
        #msg_dict = {'tenant':str(request.tenant), 'opcode':'TopTables'}
        #response = api_rpc.call(dumps(msg_dict))
        #print "Api Service response", response, "Type:", type(loads(response))
        #ret_response = self.convert_top_tables(loads(response))
        #print "Got Response:", ret_response
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
            ret.next = response['next']
        return ret

    def getQueries(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetQueries'}
        if request.next != "":
            msg_dict['next'] = request.next
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_query_data(loads(response))
        api_rpc.close()
        return ret_response
 
    def convert_to_query_detail_data(self, response):
        ret = navopt_pb2.GetQueriesDetailResponse()
  
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

        for entry in response['tables']:
            #print "entry:", entry
            data = navopt_pb2.QueryTable()
            if 'tableName' in entry:
                data.tableName = entry['tableName']
            if 'tableType' in entry:
                data.tableType = entry['tableType']
            if 'tid' in entry:
                data.tid = entry['tid']
            ret.table.extend([data])

        #for entry in response['SignatureKeywords']:
            #print "entry:", entry
        ret.querySignature.extend(response['SignatureKeywords'])
        #print "Ret:", ret, "tables:", ret.results
        return ret

    def getQueriesDetail(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetQueryDetail'}
        if request.qid != "":
            msg_dict['qid'] = request.qid
        response = api_rpc.call(dumps(msg_dict))
        print "Api Service response", response, "Type:", type(loads(response))
        ret_response = self.convert_to_query_detail_data(loads(response))
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
            ret.next = response['next']
        return ret

    def getTables(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetTables'}
        if request.next != "":
            msg_dict['next'] = request.next
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
            ret.tid = response['type']
        if 'table_ddl' in response and response['table_ddl']:
            ret.table_ddl = response['table_ddl']
        if 'iview_ddl' in response and response['iview_ddl']:
            ret.iview_ddl = response['iview_ddl']
        if 'view_ddl' in response and response['view_ddl']:
            ret.view_ddl = response['view_ddl']

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
        print "Ret:", ret #"tables:", ret.results
        return ret

    def getTablesDetail(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetTableDetail'}
        if request.tid != "":
            msg_dict['eid'] = request.tid
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
            ret.next = response['next']
        return ret

    def getColumns(self, request, context):
        api_rpc = ApiRpcClient()
        print 'Received message: %s', request, 'Type:', type(request), 'Tenant', request.tenant
        msg_dict = {'tenant':str(request.tenant), 'opcode':'GetColumns'}
        if request.next != "":
            msg_dict['next'] = request.next
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
