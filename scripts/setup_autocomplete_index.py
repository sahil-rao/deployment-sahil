"""
Helper script to create auto complete entities in Redis
"""
import re

from flightpath import FPConnector, RedisConnector
from flightpath.Provenance import getMongoServer


def valid_uuid(uuid):
    regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuid)
    return bool(match)


def get_all_tenants():
    r = FPConnector.get_routing_redis()
    dbsilo_tenants = r.smembers(FPConnector.dbsilo_tenants_metakey)
    all_tenants = set()
    for e in dbsilo_tenants:
        tenants = r.smembers(e)
        for tenant in tenants:
            if valid_uuid(tenant):
                all_tenants.add(tenant)
                
    return all_tenants


def process_tenants(tenants):
    for tenant in tenants:
        db = getMongoServer(tenant)[tenant]
        redis_conn = RedisConnector.RedisConnector(tenant)

        tables = db.entities.find({"etype": "SQL_TABLE"},
                                  {"name": 1, "eid": 1})

        print "Processing tenant " + tenant
        created = 0
        for table in tables:
            #print "Creating AutoComplete entity ({}, {}, {})".format(table['eid'],"SQL_TABLE", table['name']) 
            redis_conn.createAutocompleteEntity(table['eid'], "SQL_TABLE", table['name'])
            created = created + 1
        print "Created {} entities".format(created)

all_tenants = get_all_tenants()
process_tenants(all_tenants)
