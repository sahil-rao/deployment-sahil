from flightpath.RedisConnector import *
from pymongo import MongoClient
from flightpath.Provenance import getMongoServer
import json

def run_workflow(tenants, params):
    '''
    Identifies the difference between the passed in entities.
    '''
    tenants_dict = {}
    for tenantid in tenants:
        entities = getMongoServer(tenantid)[tenantid].entities
        #rconn = RedisConnector(tenantid)

        md5_set = set()
        queries = entities.find({'etype':"SQL_QUERY", 'parse_success': True}, {'md5':1})

        for query in queries:
            md5_set.add(query['md5'])
        tenants_dict[tenantid] = {'md5_set':md5_set}

    print '%s %s'%(tenants[0],tenants_dict[tenants[0]]['md5_set'] - tenants_dict[tenants[1]]['md5_set'])
    print '%s %s'%(tenants[1],tenants_dict[tenants[1]]['md5_set'] - tenants_dict[tenants[0]]['md5_set'])
    return tenants_dict

if __name__ == '__main__':
    run_workflow(['e3277a29-3ccf-d134-ddf7-f23d6db7c822', 'b0e0af8c-56ed-7e3b-e5e9-3780803be23a'],{})
