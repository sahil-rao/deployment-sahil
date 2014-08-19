#!/usr/bin/python
"""
Form Join groups for given query.
"""
import os
import time
import sys
import ConfigParser
from pymongo import *
from flightpath.Provenance import getMongoServer
import datetime
import uuid
import boto
from boto.s3.key import Key
import pika
from json import *
import redis

"""
data_file = [
{"interop_profile_v1" :  { "file" : "interop_profile_v1.hbs", "template_engine_version" : "1" }},
{"interop_profile_scripts_v1" :  { "file" : "scripts/interop_profile_scripts_v1.hbs", "template_engine_version" : "1" }},
{"recommendation_profile_v1": { "file" : "recommendation_profile_v1.hbs", "template_engine_version" : "1" }},
{"interop_profile_stylesheets_v1":{ "file" : "stylesheets/interop_profile_stylesheets_v1.hbs", "template_engine_version" : "1" }},
{"recommendation_profile":{ "layout" : "layout_sidebar", "components" : [ { "topbar" : "topbar_v1" }, { "sidebar" : "sidebar_v1" }, { "main_content" : "recommendation_profile_v1" }, { "component_scripts" : "recommendation_profile_scripts_v1" }, { "component_stylesheets" : "recommendation_profile_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"recommendation_profile_scripts_v1":{ "file" : "scripts/recommendation_profile_scripts_v1.hbs", "template_engine_version" : "1" }},
{"recommendation_profile_stylesheets_v1":{ "file" : "stylesheets/recommendation_profile_stylesheets_v1.hbs", "template_engine_version" : "1" }},
{"workflow_profile": { "layout" : "layout_sidebar", "components" : [ { "topbar" : "topbar_v1" }, { "sidebar" : "sidebar_v1" }, { "main_content" : "workflow_profile_v1" }, { "component_scripts" : "workflow_profile_scripts_v1" }, { "component_stylesheets" : "workflow_profile_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"workflow_profile_v1" : { "file" : "workflow_profile_v1.hbs", "template_engine_version" : "1" }},
{"workflow_profile_scripts_v1" : { "file" : "scripts/workflow_profile_scripts_v1.hbs", "template_engine_version" : "1" }},
{"workflow_profile_stylesheets_v1" : { "file" : "stylesheets/workflow_profile_stylesheets_v1.hbs", "template_engine_version" : "1" }},
{"table_map" : { "layout" : "layout_sidebar", "components" : [ { "topbar" : "topbar_v1" }, { "sidebar" : "sidebar_v1" }, { "main_content" : "table_map_v1" }, { "component_scripts" : "table_map_scripts_v1" }, { "component_stylesheets" : "table_map_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"table_map_v1" : { "file" : "table_map_v1.hbs", "template_engine_version" : "1" }},
{"table_map_scripts_v1" : { "file" : "scripts/table_map_scripts_v1.hbs", "template_engine_version" : "1" }},
{"table_map_stylesheets_v1" : { "file" : "stylesheets/table_map_stylesheets_v1.hbs", "template_engine_version" : "1" }},
{"table_matrix" : { "layout" : "layout_sidebar", "components" : [ { "topbar" : "topbar_v1" }, { "sidebar" : "sidebar_v1" }, { "main_content" : "table_matrix_v1" }, { "component_scripts" : "table_matrix_scripts_v1" }, { "component_stylesheets" : "table_matrix_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"table_matrix_v1" : { "file" : "table_matrix_v1.hbs", "template_engine_version" : "1" }},
{"table_matrix_scripts_v1" : { "file" : "scripts/table_matrix_scripts_v1.hbs", "template_engine_version" : "1" }},
{"table_matrix_stylesheets_v1" : { "file" : "stylesheets/table_matrix_stylesheets_v1.hbs", "template_engine_version" : "1" }},
{"layout_sidebar" : { "file" : "layout_sidebar_v1.hbs", "template_engine_version" : "1" }},
{"topbar_v1" : { "file" : "topbar_v1.hbs", "template_engine_version" : "1" }},
{"sidebar_v1" : { "file" : "sidebar_v1.hbs", "template_engine_version" : "1" }},
{"datasets" : { "layout" : "layout_sidebar", "components" : [ { "topbar" : "topbar_v1" }, { "sidebar" : "sidebar_v1" }, { "main_content" : "datasets_v1" }, { "component_scripts" : "datasets_scripts_v1" }, { "component_stylesheets" : "datasets_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"datasets_v1" : { "file" : "datasets_v1.hbs", "template_engine_version" : "1" }},
{"datasets_scripts_v1" : { "file" : "scripts/datasets_scripts_v1.hbs", "template_engine_version" : "1" }},
{"datasets_stylesheets_v1" : { "file" : "stylesheets/datasets_stylesheets_v1.hbs", "template_engine_version" : "1" }},
{"workload_statistics" : { "layout" : "layout_sidebar", "components" : [ { "topbar" : "topbar_v1" }, { "sidebar" : "sidebar_v1" }, { "main_content" : "workload_statistics_v1" }, { "component_scripts" : "workload_statistics_scripts_v1" }, { "component_stylesheets" : "workload_statistics_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"workload_statistics_v1" : { "file" : "workload_statistics_v1.hbs", "template_engine_version" : "1" }},
{"workload_statistics_scripts_v1" : { "file" : "scripts/workload_statistics_scripts_v1.hbs", "template_engine_version" : "1" }},
{"workload_statistics_stylesheets_v1" : { "file" : "stylesheets/workload_statistics_stylesheets_v1.hbs", "template_engine_version" : "1" }},
{"tables_found" : { "layout" : "layout_sidebar", "components" : [ { "topbar" : "topbar_v1" }, { "sidebar" : "sidebar_v1" }, { "main_content" : "tables_found_v1" }, { "component_scripts" : "tables_found_scripts_v1" }, { "component_stylesheets" : "tables_found_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"tables_found_v1" : { "file" : "tables_found_v1.hbs", "template_engine_version" : "1" }},
{"tables_found_scripts_v1" : { "file" : "scripts/tables_found_scripts_v1.hbs", "template_engine_version" : "1" }},
{"tables_found_stylesheets_v1" : { "file" : "stylesheets/tables_found_stylesheets_v1.hbs", "template_engine_version" : "1" }},
{"program_profile" : { "layout" : "layout_sidebar", "components" : [ { "topbar" : "topbar_v1" }, { "sidebar" : "sidebar_v1" }, { "main_content" : "program_profile_v1" }, { "component_scripts" : "program_profile_scripts_v1" }, { "component_stylesheets" : "program_profile_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"program_profile_v1" : { "file" : "program_profile_v1.hbs", "template_engine_version" : "1" }},
{"program_profile_scripts_v1" : { "file" : "scripts/program_profile_scripts_v1.hbs", "template_engine_version" : "1" }},
{"program_profile_stylesheets_v1" : { "file" : "stylesheets/program_profile_stylesheets_v1.hbs", "template_engine_version" : "1" }},
{"interop_profile" : { "layout" : "layout_sidebar", "components" : [ { "topbar" : "topbar_v1" }, { "sidebar" : "sidebar_v1" }, { "main_content" : "interop_profile_v1" }, { "component_scripts" : "interop_profile_scripts_v1" }, { "component_stylesheets" : "interop_profile_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"dashboard_layout_v2" : { "file" : "dashboard_v2.hbs", "template_engine_version" : "1" },"dashboard_v2" : { "layout" : "dashboard_layout_v2", "components" : [ { "topbar" : "dashboard_topbar_v2" }, { "insights" : "insights_v1" }, { "info_boxes" : "info_boxes_v1" }, { "table_histogram" : "table_histogram_v1" }, { "query_treemap" : "query_treemap_v1" }, { "footer" : "footer_v2" }, { "upload_modal" : "upload_modal_v1" }, { "component_scripts" : "dashboard_scripts_v2" }, { "component_stylesheets" : "dashboard_stylesheets_v2" } ], "template_engine_version" : "1" }},
{"dashboard_topbar_v2" : { "file" : "dashboard_topbar_v2.hbs", "template_engine_version" : "1" }},
{"insights_v1" : { "file" : "insights_v1.hbs", "template_engine_version" : "1" }},
{"info_boxes_v1" : { "file" : "info_boxes_v1.hbs", "template_engine_version" : "1" }},
{"table_histogram_v1" : { "file" : "table_histogram_v1.hbs", "template_engine_version" : "1" }},
{"query_treemap_v1" : { "file" : "query_treemap_v1.hbs", "template_engine_version" : "1" }},
{"footer_v2" : { "file" : "footer_v2.hbs", "template_engine_version" : "1" }},
{"upload_modal_v1" : { "file" : "upload_modal_v1.hbs", "template_engine_version" : "1" }},
{"dashboard_scripts_v2" : { "file" : "scripts/dashboard_scripts_v2.hbs", "template_engine_version" : "1" }},
{"dashboard_stylesheets_v2" : { "file" : "stylesheets/dashboard_stylesheets_v2.hbs", "template_engine_version" : "1" }},
{"dashboard_layout" : { "file" : "dashboard_v1.hbs", "template_engine_version" : "1" }},
{"dashboard" : { "layout" : "dashboard_layout", "components" : [ { "topbar" : "dashboard_topbar_v1" }, { "workload_analysis_summary" : "workload_analysis_summary_v1" }, { "table_access_frequency" : "table_access_frequency_v1" }, { "inferred_grouping" : "inferred_grouping_v1" }, { "footer" : "footer_v1" }, { "component_scripts" : "dashboard_scripts_v1" }, { "component_stylesheets" : "dashboard_stylesheets_v1" } ], "template_engine_version" : "1" }},
{"dashboard_topbar_v1" : { "file" : "dashboard_topbar_v1.hbs", "template_engine_version" : "1" }},
{"workload_analysis_summary_v1" : { "file" : "workload_analysis_summary_v1.hbs", "template_engine_version" : "1" }},
{"table_access_frequency_v1" : { "file" : "table_access_frequency_v1.hbs", "template_engine_version" : "1" }},
{"inferred_grouping_v1" : { "file" : "inferred_grouping_v1.hbs", "template_engine_version" : "1" }},
{"footer_v1" : { "file" : "footer_v1.hbs", "template_engine_version" : "1" }},
{"dashboard_scripts_v1" : { "file" : "scripts/dashboard_scripts_v1.hbs", "template_engine_version" : "1" }},
{"dashboard_stylesheets_v1" : { "file" : "stylesheets/dashboard_stylesheets_v1.hbs", "template_engine_version" : "1" }}
]
"""

data_file = [
            { "dashboard_layout_v2": {
                    "file": "dashboard_v2.hbs",
                    "template_engine_version": "1"
                }
            },
            { "dashboard_v2": {
                "layout": "dashboard_layout_v2",
                "components": [
                    { "topbar": "dashboard_topbar_v2" },
                    { "insights": "insights_v1" },
                    { "info_boxes": "info_boxes_v1" },
                    { "table_histogram": "table_histogram_v1" },
                    { "query_treemap": "query_treemap_v1" },
                    { "footer": "footer_v2" },
                    { "upload_modal": "upload_modal_v1" },
                    { "component_scripts": "dashboard_scripts_v2" },
                    { "component_stylesheets": "dashboard_stylesheets_v2" }
                ],
                "template_engine_version": "1" }
            },
            { "dashboard_topbar_v2": {
                    "file": "dashboard_topbar_v2.hbs",
                    "template_engine_version": "1"
                }
            },
            { "insights_v1": {
                    "file": "insights_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "info_boxes_v1": {
                    "file": "info_boxes_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "table_histogram_v1": {
                    "file": "table_histogram_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "query_treemap_v1": {
                    "file": "query_treemap_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "footer_v2": {
                    "file": "footer_v2.hbs",
                    "template_engine_version": "1"
                }
            },
            { "upload_modal_v1": {
                    "file": "upload_modal_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "dashboard_scripts_v2": {
                    "file": "scripts/dashboard_scripts_v2.hbs",
                    "template_engine_version": "1"
                }
            },
            { "dashboard_stylesheets_v2": {
                    "file": "stylesheets/dashboard_stylesheets_v2.hbs",
                    "template_engine_version": "1"
                }
            },
            { "dashboard_layout": {
            "file": "dashboard_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "dashboard": {
                "layout": "dashboard_layout",
                "components": [
                    { "topbar": "dashboard_topbar_v1" },
                    { "workload_analysis_summary": "workload_analysis_summary_v1" },
                    { "table_access_frequency": "table_access_frequency_v1" },
                    { "inferred_grouping": "inferred_grouping_v1" },
                    { "footer": "footer_v1" },
                    { "component_scripts": "dashboard_scripts_v1" },
                    { "component_stylesheets": "dashboard_stylesheets_v1" }
                ],
                "template_engine_version": "1" }
            },
            { "dashboard_topbar_v1": {
                    "file": "dashboard_topbar_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "workload_analysis_summary_v1": {
                    "file": "workload_analysis_summary_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "table_access_frequency_v1": {
                    "file": "table_access_frequency_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "inferred_grouping_v1": {
                    "file": "inferred_grouping_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "footer_v1": {
                    "file": "footer_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "dashboard_scripts_v1": {
                    "file": "scripts/dashboard_scripts_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "dashboard_stylesheets_v1": {
                    "file": "stylesheets/dashboard_stylesheets_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "layout_sidebar": {
                    "file": "layout_sidebar_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "topbar_v1": {
                    "file": "topbar_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "sidebar_v1": {
                    "file": "sidebar_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "datasets": {
                "layout": "layout_sidebar",
                "components": [
                    { "topbar": "topbar_v1" },
                    { "sidebar": "sidebar_v1" },
                    { "main_content": "datasets_v1" },
                    { "component_scripts": "datasets_scripts_v1" },
                    { "component_stylesheets": "datasets_stylesheets_v1" }
                ],
                "template_engine_version": "1" }
            },
            { "datasets_v1": {
                    "file": "datasets_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "datasets_scripts_v1": {
                    "file": "scripts/datasets_scripts_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "datasets_stylesheets_v1": {
                    "file": "stylesheets/datasets_stylesheets_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "workload_statistics": {
                    "layout": "layout_sidebar",
                    "components": [
                        { "topbar": "topbar_v1" },
                        { "sidebar": "sidebar_v1" },
                        { "main_content": "workload_statistics_v1" },
                        { "component_scripts": "workload_statistics_scripts_v1" },
                        { "component_stylesheets": "workload_statistics_stylesheets_v1" }
                    ],
                    "template_engine_version": "1"
                }
            },
            { "workload_statistics_v1": {
                    "file": "workload_statistics_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "workload_statistics_scripts_v1": {
                    "file": "scripts/workload_statistics_scripts_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "workload_statistics_stylesheets_v1": {
                    "file": "stylesheets/workload_statistics_stylesheets_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "tables_found": {
                    "layout": "layout_sidebar",
                    "components": [
                        { "topbar": "topbar_v1" },
                        { "sidebar": "sidebar_v1" },
                        { "main_content": "tables_found_v1" },
                        { "component_scripts": "tables_found_scripts_v1" },
                        { "component_stylesheets": "tables_found_stylesheets_v1" }
                    ],
                    "template_engine_version": "1"
                }
            },
            { "tables_found_v1": {
                    "file": "tables_found_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "tables_found_scripts_v1": {
                    "file": "scripts/tables_found_scripts_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "tables_found_stylesheets_v1": {
                    "file": "stylesheets/tables_found_stylesheets_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "program_profile": {
                    "layout": "layout_sidebar",
                    "components": [
                        { "topbar": "topbar_v1" },
                        { "sidebar": "sidebar_v1" },
                        { "main_content": "program_profile_v1" },
                        { "component_scripts": "program_profile_scripts_v1" },
                        { "component_stylesheets": "program_profile_stylesheets_v1" }
                    ], "template_engine_version": "1"
                    }
            },
            { "interop_profile_v1": {
                    "file": "interop_profile_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "interop_profile_scripts_v1": {
                    "file": "scripts/interop_profile_scripts_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "interop_profile_stylesheets_v1": {
                    "file": "stylesheets/interop_profile_stylesheets_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "recommendation_profile": {
                    "layout": "layout_sidebar",
                    "components": [
                        { "topbar": "topbar_v1" },
                        { "sidebar": "sidebar_v1" },
                        { "main_content": "recommendation_profile_v1" },
                        { "component_scripts": "recommendation_profile_scripts_v1" },
                        { "component_stylesheets": "recommendation_profile_stylesheets_v1" }
                    ],
                    "template_engine_version": "1"
                }
            },
            { "recommendation_profile_v1": {
                    "file": "recommendation_profile_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "recommendation_profile_scripts_v1": {
                    "file": "scripts/recommendation_profile_scripts_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "recommendation_profile_stylesheets_v1": {
                    "file": "stylesheets/recommendation_profile_stylesheets_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "workflow_profile": {
                    "layout": "layout_sidebar",
                    "components": [
                        { "topbar": "topbar_v1" },
                        { "sidebar": "sidebar_v1" },
                        { "main_content": "workflow_profile_v1" },
                        { "component_scripts": "workflow_profile_scripts_v1" },
                        { "component_stylesheets": "workflow_profile_stylesheets_v1" }
                    ],
                    "template_engine_version": "1"
                }
            },
            { "workflow_profile_v1": {
                    "file": "workflow_profile_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "workflow_profile_scripts_v1": {
                    "file": "scripts/workflow_profile_scripts_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "workflow_profile_stylesheets_v1": {
                    "file": "stylesheets/workflow_profile_stylesheets_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "table_map": {
                    "layout": "layout_sidebar",
                    "components": [
                        { "topbar": "topbar_v1" },
                        { "sidebar": "sidebar_v1" },
                        { "main_content": "table_map_v1" },
                        { "component_scripts": "table_map_scripts_v1" },
                        { "component_stylesheets": "table_map_stylesheets_v1" }
                    ],
                    "template_engine_version": "1"
                }
            },
            { "table_map_v1": {
                    "file": "table_map_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "table_map_scripts_v1": {
                    "file": "scripts/table_map_scripts_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "table_map_stylesheets_v1": {
                    "file": "stylesheets/table_map_stylesheets_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "table_matrix": {
                    "layout": "layout_sidebar",
                    "components": [
                        { "topbar": "topbar_v1" },
                        { "sidebar": "sidebar_v1" },
                        { "main_content": "table_matrix_v1" },
                        { "component_scripts": "table_matrix_scripts_v1" },
                        { "component_stylesheets": "table_matrix_stylesheets_v1" }
                    ],
                    "template_engine_version": "1"
                }
            },
            { "table_matrix_v1": {
                    "file": "table_matrix_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "table_matrix_scripts_v1": {
                    "file": "scripts/table_matrix_scripts_v1.hbs",
                    "template_engine_version": "1"
                }
            },
            { "table_matrix_stylesheets_v1": {
                    "file": "stylesheets/table_matrix_stylesheets_v1.hbs",
                    "template_engine_version": "1"
                }
            }
]

"""
 Arg 1: user name - user name will be appended with numbers...eg. 
        "scale" -> scale@xplain.io1, scale@xplain.io2....
 Arg 2: number of users.
 Arg 3: Input file.
"""
account_name = sys.argv[1]
num_users = int(sys.argv[2])
inp_file = sys.argv[3]
r = redis.StrictRedis(host='10.0.0.211', port=6379, db=0)

mongo_servers = ["server"]
if not os.path.isfile(inp_file):
    print "Input file does not exist"
    exit(0)
inp_splits = inp_file.split()
filename = inp_splits[len(inp_splits)-1]

mongoHost = getMongoServer('xplainIO')
client = MongoClient(host=mongoHost)

credentials = pika.PlainCredentials('xplain', 'xplain')
vhost = 'xplain'

pconn = pika.BlockingConnection(pika.ConnectionParameters('10.0.0.196', 5672, vhost, credentials))
channel = pconn.channel()
channel.queue_declare(queue='ftpupload')
for i in range(0, num_users):
    print
    print
    print "********* processing user ", i
    org = str(uuid.uuid4())
    uid = str(uuid.uuid4())
    uname = account_name + "@xplain.io" + str(i)
    user_dict = { "type" : "local", "level" : "1", "email" : uname,
                  "organizations" : [org],
        "local" : { "password" : "$2a$08$JX93lgZiLoqKCIR5NNod.OGPsdO5AylzjeAG8Ow/p55BzdNikO4Fm" }, "__v" : 0 }

    org_dict = { "guid" : org, "users" : [uname], "__v" : 0 }
    print user_dict
    print
    print "********* processing user ", i
    org = str(uuid.uuid4())
    uid = str(uuid.uuid4())
    uname = account_name + "@xplain.io" + str(i)
    user_dict = { "type" : "local", "level" : "1", "email" : uname,
                  "organizations" : [org],
        "local" : { "password" : "$2a$08$JX93lgZiLoqKCIR5NNod.OGPsdO5AylzjeAG8Ow/p55BzdNikO4Fm" }, "__v" : 0 }

    org_dict = { "guid" : org, "users" : [uname], "__v" : 0 }
    print user_dict
    print
    print org_dict

    #put user and tenant organization
    xplain_db = client.xplainIO
    xplain_db.users.insert(user_dict)
    xplain_db.organizations.insert(org_dict)

    #put file to s3
    timestr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
    s3filepath =  timestr + "/" + filename
    destination = org + "/" + s3filepath

    print "s3filepath : ", s3filepath, " Destination: ",destination
    connection = boto.connect_s3()
    bucket = connection.get_bucket('partner-logs') # substitute your bucket name here
    file_key = Key(bucket)
    file_key.key = destination
    file_key.set_contents_from_filename(filename)

    # create db routing record.
    mongohash = i % len(mongo_servers)
    mserver = mongo_servers[mongohash]
    r.set(org, mserver)
    print "MongoServer : ", mserver

    # Save upload record.
    timestamp = long(time.time()*1000)
    upload_record = {'tenant': org, 'filename': filename,
                'uid': uid, 'timestamp': timestamp}
    org_client = MongoClient(host=getMongoServer(org))
    org_client[org].uploadStats.insert(upload_record)
    #for df in data_file:
    org_client[org].data_files.insert(data_file)
    org_client.close()
    print upload_record

    #Inject event to rabbit.
    msg_dict = {"tenent": org, "filename": s3filepath, "uid": uid
    message = dumps(msg_dict)
    print "Message :", message
    channel.basic_publish(exchange='',
                          routing_key='ftpupload',
                          body=message)
    print "User : ", uname, " created."

pconn.close()
client.close()
