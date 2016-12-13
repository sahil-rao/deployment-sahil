# (c) Copyright 2015 Cloudera, Inc. All rights reserved.

"""
Application API delete a user or workload from the system.

"""

import logging
import elasticsearch
import ConfigParser
from flightpath.RedisConnector import deleteTenant
from flightpath.Provenance import getMongoServer, getElasticServer


def execute(tenantid, msg_dict=None):

    """
    - Delete user files locally and from S3
    """
    config = ConfigParser.RawConfigParser()
    config.read("/var/Baaz/hosts.cfg")

    usingAWS = config.getboolean("mode", "usingAWS")
    if usingAWS:
        import boto

        clusterName = config.get("ApplicationConfig", "clusterName")
        boto_conn = boto.connect_s3()

        if clusterName is not None:
            bucket = boto_conn.get_bucket(clusterName)
            path = "partner-logs" + tenantid
        else:
            bucket = boto_conn.get_bucket("partner-logs")
            path = tenantid

        bucketListResultSet = bucket.list(prefix=path)
        result = bucket.delete_keys([key.name for key in bucketListResultSet])

    """
    - Redis: Remove Tenant Data
    """
    deleteTenant(tenantid)


    """
    - ElasticSearch: Remove the index for the Tenant
    """
    try:
        elastichost = getElasticServer(tenantid)
        if elastichost is not None:
            es = elasticsearch.Elasticsearch(hosts=[{'host': elastichost,
                                                     'port': 9200}])
            es.indices.delete(index=tenantid)
    except:
        logging.exception("Cleaning up Elastic search index")

    """
    - Mongo: Drop Tenant collection
    - Mongo: set queries and timestamp to 0 in organizations collection
    - Mongo: remove remove tenant from activeUploadsUIDs collection
    - Mongo: set query_processed and limit_reached to 0 in uploadStats
    """
    client = getMongoServer(tenantid)
    tenantdb = getMongoServer(tenantid)[tenantid]
    xplaindb = getMongoServer('xplainIO')['xplainIO']
    logging.info("Going to purge the tenant")
    client.drop_database(tenantid)
    xplaindb.users.remove({"organizations": tenantid})
    xplaindb.organizations.remove({"guid": tenantid})
    return {"status": "success"}

if __name__ == '__main__':
    tenants_to_delete = []
    for tenantid in tenants_to_delete:
        execute(tenantid)
