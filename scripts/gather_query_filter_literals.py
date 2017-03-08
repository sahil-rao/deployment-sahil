# (c) Copyright 2017 Cloudera, Inc. All rights reserved.

import sys
import json
from flightpath.Provenance import getMongoServer


def execute(tenantid, context):
    '''
    Generates a CSV report of all queries that have multiple
    multiple semantically duplicate instances.
    '''

    client = getMongoServer(tenantid)
    db = client[tenantid]

    out_list = []
    query_types = ['SQL_QUERY', 'SQL_SUBQUERY', 'SQL_INLINE_VIEW']
    q_cur = db.entities.find({'etype': {'$in': query_types}}, {'_id': 0})
    for q in q_cur:
        comp = q['compiler_to_use']
        profile = q['profile']['Compiler'][comp]
        if 'whereColExpr' in profile:
            out_list.append(profile['whereColExpr'])
    return {'output': json.dumps(out_list)}

if __name__ == '__main__':
    tenantid = sys.argv[1]
    x = execute(tenantid, {})
    print x
