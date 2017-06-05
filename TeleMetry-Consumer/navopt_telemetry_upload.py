#!/usr/bin/python

import os
import time

from navoptapi.api_lib import *

nav = ApiLib("navopt", "10.34.211.74", "e0819f3a-1e6f-4904-be69-5b704b299bbb", "-----BEGIN PRIVATE KEY-----\n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\nF17opGTl9M/2H+kXmsmyPwLBSQE96Q==\n-----END PRIVATE KEY-----")

while True:
    if os.path.isfile("telemetry_data.csv"):
        #get tenant
        print "Getting Tenant"
        resp =  nav.call_api("getTenant", {"email": "harshil@cloudera.com"})
        data_dict = resp.json()
        tenant = data_dict["tenant"]
        print "Doing Upload:", tenant
        #upload the file
        resp = nav.call_api("upload", {"tenant" : tenant, "fileLocation": "telemetry_data.csv", "sourcePlatform": "hive", "colDelim": ",", "rowDelim": "\n", "headerFields": [{"count": 0, "coltype": "SQL_ID", "use": True, "tag": "", "name": "SQL_ID"}, {"count": 0, "coltype": "NONE", "use": True, "tag": "", "name": "ELAPSED_TIME"}, {"count": 0, "coltype": "SQL_QUERY", "use": True, "tag": "", "name": "SQL_FULLTEXT"}, {"count": 0, "coltype": "NONE", "use": True, "tag": "", "name": "USER"}]})
        print resp
        os.remove("telemetry_data.csv")
    else:
        time.sleep(30)