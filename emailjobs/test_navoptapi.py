# Copyright (c) 2016 Cloudera, Inc. All rights reserved.

import json
import unittest
import sys
import time
import uuid
from flightpath.services import app_cleanup_user
from flightpath.Provenance import getMongoServer
from navoptapi.api_lib import ApiLib

class TestNavOptApi(unittest.TestCase):

    def setUp(self):
        self.service_name = "navopt"
        #self.host_name = "navoptapi.navopt-dev.cloudera.com"
        self.host_name = "10.34.211.74"
        self.access_key = "e0819f3a-1e6f-4904-be69-5b704b299bbb"
        self.private_key = "-----BEGIN PRIVATE KEY-----\n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\nF17opGTl9M/2H+kXmsmyPwLBSQE96Q==\n-----END PRIVATE KEY-----"
        self.nav = ApiLib(self.service_name, self.host_name,
                          self.access_key, self.private_key)
        resp = self.nav.call_api("getTenant", {"email": "harshil@cloudera.com"})
        resp_dict = resp.json()
        self.tenant = resp_dict["tenant"]

    def ordered(self, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ['eid', 'workloadPercent', 'total', 'columnCount', 'patternCount', 'tid', 'cid', 'queryIds']:
                    obj.pop(k)
            return sorted((k, self.ordered(v)) for k, v in obj.items())
        if isinstance(obj, list):
            return sorted(self.ordered(x) for x in obj)
        else:
            return obj

    def test_upload(self):
        '''
        test upload api
        '''
        result_file = 'test_results.txt'
        fp = open(result_file, "a+")
        #upload DDL
        resp = self.nav.call_api("upload",
                                 {"tenant": self.tenant,
                                  "fileLocation": "ddl4.csv",
                                  "sourcePlatform": "hive",
                                  "colDelim": ",", "rowDelim": "\n",
                                  "headerFields": [{"count": 0,
                                                    "coltype": "SQL_ID",
                                                    "use": True,
                                                    "tag": "",
                                                    "name": "SQL_ID"},
                                                   {"count": 0,
                                                    "coltype": "NONE",
                                                    "use": True,
                                                    "tag": "",
                                                    "name": "ELAPSED_TIME"},
                                                   {"count": 0,
                                                    "coltype": "SQL_QUERY",
                                                    "use": True,
                                                    "tag": "",
                                                    "name": "SQL_FULLTEXT"},
                                                   {"count": 0,
                                                    "coltype": "NONE",
                                                    "use": True,
                                                    "tag": "DATABASE",
                                                    "name": "DATABASE"}]})
        resp_dict = json.loads(resp)
        self.assertEqual(resp_dict['status']['state'], "WAITING")
        self.assertNotEqual(resp_dict['status']['workloadId'], "")
        fp.write("Uploading DDL: PASS\n")
        #wait for some time
        time.sleep(60)
        #upload query file
        resp = self.nav.call_api("upload",
                                 {"tenant": self.tenant,
                                  "fileLocation": "file4.csv",
                                  "sourcePlatform": "hive",
                                  "colDelim": ",", "rowDelim": "\n",
                                  "headerFields": [{"count": 0,
                                                    "coltype": "SQL_ID",
                                                    "use": True,
                                                    "tag": "",
                                                    "name": "SQL_ID"},
                                                   {"count": 0,
                                                    "coltype": "NONE",
                                                    "use": True,
                                                    "tag": "",
                                                    "name": "ELAPSED_TIME"},
                                                   {"count": 0,
                                                    "coltype": "SQL_QUERY",
                                                    "use": True,
                                                    "tag": "",
                                                    "name": "SQL_FULLTEXT"},
                                                   {"count": 0,
                                                    "coltype": "NONE",
                                                    "use": True,
                                                    "tag": "DATABASE",
                                                    "name": "DATABASE"}]})
        resp_dict = json.loads(resp)
        self.assertEqual(resp_dict['status']['state'], "WAITING")
        self.assertNotEqual(resp_dict['status']['workloadId'], "")
        self.workloadId = resp_dict['status']['workloadId']
        print "Tenant:", self.tenant, "workloadId:", self.workloadId
        #wait for some time
        time.sleep(140)

        # get status of the upload
        resp = self.nav.call_api("uploadStatus",
                                 {"tenant": self.tenant,
                                  "workloadId": self.workloadId})
        resp_dict = resp.json()
        self.assertEqual(resp_dict['status']['state'], "FINISHED")
        fp.write("Uploading Query: PASS\n")

        # Get Top Tables for a workload:
        compare_dict = {"nextToken": "",
                        "results": [
                          {
                            "name": "default.y",
                            "type": "Dimension",
                          },
                          {
                            "name": "default.x",
                            "type": "Dimension",
                          }
                        ]
                       }
        resp = self.nav.call_api("getTopTables",
                                 {"tenant": self.tenant})
        resp_dict = resp.json()
        resp_dict = self.ordered(resp_dict)
        compare_dict = self.ordered(compare_dict)
        self.assertEqual(resp_dict, compare_dict)
        fp.write("Get Top Tables: PASS\n")

        # Get Top Databases for a workload:
        compare_dict = {"nextToken": "",
                        "results": [
                           {
                             "instanceCount": 2,
                             "totalTableCount": 2,
                             "totalQueryCount": 1,
                            "dbName": "default",
                           }
                        ]
                       }
        resp = self.nav.call_api("getTopDatabases",
                                 {"tenant": self.tenant})
        resp_dict = resp.json()
        resp_dict = self.ordered(resp_dict)
        compare_dict = self.ordered(compare_dict)
        self.assertEqual(resp_dict, compare_dict)
        fp.write("Get Top Databases: PASS\n")

        # Get Top Columns for a workload:
        compare_dict = {"orderbyColumns": [],
                        "selectColumns": [
                           {
                             "columnCount": 1,
                             "filterCol": 0,
                             "orderbyCol": 0,
                             "dbName": "default",
                             "tableName": "x",
                             "selectCol": 1,
                             "columnName": "x",
                             "joinCol": 0,
                             "tableType": "",
                             "groupbyCol": 0
                           }
                        ],
                        "filterColumns": [],
                        "joinColumns": [
                           {
                             "columnCount": 1,
                             "filterCol": 0,
                             "orderbyCol": 0,
                             "dbName": "default",
                             "tableName": "x",
                             "selectCol": 0,
                             "columnName": "a",
                             "joinCol": 1,
                             "tableType": "",
                             "groupbyCol": 0
                           },
                           {
                             "columnCount": 1,
                             "filterCol": 0,
                             "orderbyCol": 0,
                             "dbName": "default",
                             "tableName": "y",
                             "selectCol": 0,
                             "columnName": "a",
                             "joinCol": 1,
                             "tableType": "",
                             "groupbyCol": 0
                           }
                        ],
                        "groupbyColumns": [],
                        "nextToken": ""}
        resp = self.nav.call_api("getTopColumns",
                                 {"tenant": self.tenant})
        resp_dict = resp.json()
        resp_dict = self.ordered(resp_dict)
        compare_dict = self.ordered(compare_dict)
        self.assertEqual(resp_dict, compare_dict)
        fp.write("Get Top Columns: PASS\n")

        # Get Top Filters for a workload:
        compare_dict = {"nextToken": "", "results": []}
        resp = self.nav.call_api("getTopFilters",
                                 {"tenant": self.tenant})
        resp_dict = resp.json()
        resp_dict = self.ordered(resp_dict)
        compare_dict = self.ordered(compare_dict)
        self.assertEqual(resp_dict, compare_dict)
        fp.write("Get Top Filters: PASS\n")

        # Get Top Aggregates for a workload:
        compare_dict = {"nextToken": "", "results": []}
        resp = self.nav.call_api("getTopAggs",
                                 {"tenant": self.tenant})
        resp_dict = resp.json()
        resp_dict = self.ordered(resp_dict)
        compare_dict = self.ordered(compare_dict)
        self.assertEqual(resp_dict, compare_dict)
        fp.write("Get Top Aggregates: PASS\n")

        # Get Top Joins for a workload:
        compare_dict = {"nextToken": "",
                        "results": [
                          {
                            "joinType": "join",
                            "tables": [
                               "default.x",
                               "default.y"
                            ],
                            "joinCols": [
                              {
                                "columns": [
                                             "default.x.a",
                                             "default.y.a"
                                ]
                              }
                            ],
                            "totalTableCount": 2,
                            "totalQueryCount": 1
                          }
                        ]
                       }
        resp = self.nav.call_api("getTopJoins",
                                 {"tenant": self.tenant, "dbTableList": ["default.x", "default.y"]})
        resp_dict = resp.json()
        resp_dict = self.ordered(resp_dict)
        compare_dict = self.ordered(compare_dict)
        self.assertEqual(resp_dict, compare_dict)
        fp.write("Get Top Joins: PASS\n")

        # Get Query Compatibility:
        compare_dict = {
                         "status": "FAIL",
                         "clauseString": "partsupp.ps_supplycost = (select min(partsupp.ps_supplycost)\n                                       from   partsupp,\n                                              supplier,\n                                              nation,\n                                              region\n                                       where  part.p_partkey = partsupp.ps_partkey\n                                              and supplier.s_suppkey = partsupp.ps_suppkey\n                                              and supplier.s_nationkey = nation.n_nationkey\n                                              and nation.n_regionkey = region.r_regionkey\n                                              and region.r_name = 'europe')",
                         "queryError": {
                           "errorString": "line 21:39 cannot recognize input near 'select' 'min' '(' in expression specification",
                           "encounteredString": "",
                           "expectedString": ""
                         },
                         "parseError": "",
                         "clauseName": "Where",
                         "clauseError": {
                           "endLocator": {
                             "column": 75,
                             "lineNum": 30,
                             "tokenRank": 232,
                             "offset": 1333
                           },
                           "startLocator": {
                             "column": 14,
                             "lineNum": 21,
                             "tokenRank": 146,
                             "offset": 623
                           }
                         }
                       }
        resp = self.nav.call_api("getQueryCompatible",
                                 {"tenant": self.tenant,
                                  "query": "select supplier.s_acctbal, supplier.s_name, nation.n_name, part.p_partkey, part.p_mfgr, supplier.s_address, supplier.s_phone, supplier.s_comment from part, supplier, partsupp, nation, region where part.p_partkey = partsupp.ps_partkey and supplier.s_suppkey = partsupp.ps_suppkey and part.p_size = 15 and part.p_type like '%BRASS' and supplier.s_nationkey = nation.n_nationkey and nation.n_regionkey = region.r_regionkey and region.r_name = 'EUROPE' and partsupp.ps_supplycost = ( select min(partsupp.ps_supplycost) from partsupp, supplier, nation, region where part.p_partkey = partsupp.ps_partkey and supplier.s_suppkey = partsupp.ps_suppkey and supplier.s_nationkey = nation.n_nationkey and nation.n_regionkey = region.r_regionkey and region.r_name = 'EUROPE' ) order by supplier.s_acctbal desc, nation.n_name, supplier.s_name, part.p_partkey",
                                  "sourcePlatform": "teradata",
                                  "targetPlatform": "hive"})
        resp_dict = resp.json()
        resp_dict = self.ordered(resp_dict)
        compare_dict = self.ordered(compare_dict)
        self.assertEqual(resp_dict, compare_dict)
        fp.write("Get Query Compatiblity: PASS\n")

        # Get Query Risk Analysis:
        compare_dict = {
                        "errorMsg": "",
                        "noStats": ["default.web_logs"],
                        "impalaRisk": [
                          {
                            "riskTables": ["default.web_logs"],
                            "riskAnalysis": "Query has no filters.",
                            "riskId": 17,
                            "risk": "high",
                            "riskRecommendation": "Rewrite query to add filtering conditions and reduce size of the result set."
                          }
                        ],
                        "noDDL": ["default.web_logs"],
                        "hiveRisk": [
                          {
                            "riskTables": ["default.web_logs"],
                            "riskAnalysis": "Query has no filters.",
                            "riskId": 17,
                            "risk": "high",
                            "riskRecommendation": "Rewrite query to add filtering conditions and reduce size of the result set."
                          }
                        ]
                       }
        resp = self.nav.call_api("getQueryRisk",
                                 {"tenant": self.tenant,
                                  "query": "select * from web_logs",
                                  "sourcePlatform": "hive",
                                  "dbName": "default"})
        resp_dict = resp.json()
        resp_dict = self.ordered(resp_dict)
        compare_dict = self.ordered(compare_dict)
        self.assertEqual(resp_dict, compare_dict)
        fp.write("Get Query Risk: PASS\n")
        fp.close()

    def tearDown(self):
        app_cleanup_user.execute(self.tenant, {})
        self.post_cleanup_tenant()

    def post_cleanup_tenant(self):
        tenantid = str(uuid.uuid4())
        org_record = {
           "upLimit" : 1000000,
           "users" : [ "harshil@cloudera.com" ],
           "workloadName" : "NavOpt API Workload",
           "isDemo" : False,
           "__v" : 0,
           "guid" : tenantid
        }
        client = getMongoServer('xplainDb')
        users = client['xplainIO'].users
        organizations = client['xplainIO'].organizations
        #xplaindb = getMongoServer('xplainIO')['xplainIO']

        #create entry in organizations
        organizations.insert(org_record)

        print "==> Insert tenant:", tenantid
        users.update({'email': 'harshil@cloudera.com'},
                     {'$push': {'organizations': tenantid},
                      '$set': {'lastSelectedWorkload': tenantid}})
        mconn = getMongoServer(tenantid)
        #create uid:0 entry
        mconn[tenantid].uploadStats.insert({'uid':'0', 'query_processed': 0, 'limit_reached': False})

if __name__ == '__main__':
    fsock = open('test_results.txt', 'a+')
    sys.stdout = sys.stderr = fsock
    unittest.main()
    fsock.close()
    #result_file = 'test_results.txt'
    #f = open(result_file, "a+")
    #sys.stdout = sys.stderr = f
    #runner = unittest.TextTestRunner(f)
    #unittest.main(testRunner=runner)
    #f.close()
