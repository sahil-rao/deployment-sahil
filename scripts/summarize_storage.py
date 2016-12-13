"""
Helper script to verify redis and mongo contents
"""
import pprint
import traceback
import redis
from redis.sentinel import Sentinel
from collections import defaultdict
from flightpath import FPConnector
from flightpath.Provenance import getMongoServer
from collections import defaultdict

REDIS_PORT = 6379
REDIS_SENTINEL_PORT = 26379
REDIS_TENANT_ROUTING_DB = 0
REDIS_DATA_DB = 1

"""
Redis functions
"""
def getRedis(tenantId, port=REDIS_PORT, db=REDIS_DATA_DB, timeout=15):
    redis_master_name = FPConnector.get_redis_master_name(tenantId)
    sentinel_endpoints = []
    for host in FPConnector.get_redis_hosts(tenantId):
        sentinel_endpoints.append((host, REDIS_SENTINEL_PORT))
        sentinel = Sentinel(sentinel_endpoints, socket_timeout=timeout)
    return sentinel.master_for(redis_master_name, db=db)

def groupRedisKeysByPrefix(r):
    group = defaultdict(int)

    for k in r.keys():
        prefix = k.split(":")[0]
        group[prefix] += 1

    return group

"""
MongoDB functions
"""
def getMongo(tenantId):
    return getMongoServer(tenantId)

def getDatabases(mongoClient):
    return mongoClient.database_names()

"""
Utility functions
"""
def prettyPrintDict(o, header):
    max_width = max(len(k) for k in o) + 5
    print "".join(header[0].ljust(max_width)), header[1]

    for k in o:
        print "".join(k.ljust(max_width)), o[k]

def prettyPrintList(o, header):
    print header
    print "\n".join(o)

def prettyPrint(o, header):
    if isinstance(o, dict):
        prettyPrintDict(o, header)
    if isinstance(o, list):
        prettyPrintList(o, header)

if __name__ == '__main__':
    testTenant = "b92ba3f5-a8f4-abb7-8074-d5666bf2dc81"
    r = getRedis(testTenant)
    m = getMongo(testTenant)

    print "Redis tenant info"
    prettyPrint(groupRedisKeysByPrefix(r), ["Prefix", "Keys"])
    prettyPrint(getDatabases(m),"\nMongoDB databases")
    #inspect xplain db
    xplaindb = getMongoServer('xplainIO')['xplainIO']
    print "\nxplaindb.users"
    for users in xplaindb.users.find():
        pprint.pprint(users)
    print "\nxplaindb.shared"
    for shared in xplaindb.shared.find():
        pprint.pprint(shared)
    print "\nxplaindb.organizations"
    for org in xplaindb.organizations.find():
        pprint.pprint(org)

