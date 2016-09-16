#!/usr/bin/env python

"""
Application API that retrieves summary information about all design buckets
the user has created.
"""

__author__ = 'Prithviraj Pandian'
__copyright__ = 'Copyright 2016, Cloudera Inc.'
__license__ = ''
__version__ = '0.1'
__maintainer__ = 'Prithviraj Pandian'
__email__ = 'prithviraj.pandian@cloudera.com'

import sys
from pprint import pprint
from flightpath.RedisConnector import RedisConnector
from flightpath.Provenance import getMongoServer


def execute(tenantid, msg_dict):

    rconn = RedisConnector(tenantid)
    mconn = getMongoServer(tenantid)
    db = mconn[tenantid]

    all_buckets = db.interactions.find_one({"items": {"$exists": True}}, {"items": 1})

    if 'bucketName' in msg_dict:
        buckets = all_buckets['items']
        for bucket in buckets:
            if bucket['listName'] == msg_dict['bucketName']:
                all_buckets['items'] = []
                all_buckets['items'].append(bucket)
   
    all_queries_in_buckets = set()
    for bucket in all_buckets['items']:
        if 'queryIds' in bucket:
            all_queries_in_buckets.update(bucket['queryIds'])

    design_bucket_list = []

    for bucket in all_buckets['items']:
        query_eids = []
        if 'queryIds' in bucket:
            query_eids = bucket['queryIds']

        table_read_eids = {rel['start_en'] for rel in rconn.getBatchRelationships('READ', query_eids, reverse=True)}
        table_write_eids = {rel['end_en'] for rel in rconn.getBatchRelationships('WRITE', query_eids, reverse=False)}
        table_eids = table_read_eids | table_write_eids

        num_tables = len(table_eids)
        num_queries = len(query_eids)

        design_bucket_list.append({
            'bucketName': bucket['listName'],
            'description': bucket['desc'] if 'desc' in bucket else None,
            'numQueries': num_queries,
            'numTables': num_tables,
        })

    return design_bucket_list


if __name__ == '__main__':
    pprint(execute(sys.argv[1], {}))
    pprint(execute(sys.argv[1], {'bucketName': 'low'}))
