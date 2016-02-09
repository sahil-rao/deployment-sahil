#!/usr/bin/python
import ConfigParser
import redis
import json

def add_silo():
    #Parse silo info from json file
    config = ConfigParser.RawConfigParser()
    config.read("/var/Baaz/hosts.cfg")
    redis_ip = config.get("Redis", "server")
    with open("/mnt/prithvi/workspace/newsiloinfo.json") as json_data:
        new_silo_info = json.load(json_data)
    
    r = redis.StrictRedis(host=redis_ip, port=6379, db=0)

    #Add new dbsilo keys to metakey sets
    dbsilo_info_metakey = "dbsilo:metakey:info"
    dbsilo_info_key = "dbsilo:" + new_silo_info["siloinfo"]["siloname"] + ":info"
    r.sadd(dbsilo_info_metakey, dbsilo_info_key)
    dbsilo_tenants_metakey = "dbsilo:metakey:tenants"
    dbsilo_tenants_key = "dbsilo:" + new_silo_info["siloinfo"]["siloname"] + ":tenants"
    r.sadd(dbsilo_tenants_metakey, dbsilo_tenants_key)

    #Add information about silo to redis
    dbsilo_info_data = { "mongo": "mongodb://" + new_silo_info["mongo"]["instances"] + "/",
                         "redis": new_silo_info["redis"]["mastername"],
                         "elastic": new_silo_info["elasticsearch"]["nodes"],
                         "capacitylimit": new_silo_info["siloinfo"]["capacitylimit"],
                         "name": new_silo_info["siloinfo"]["siloname"] }
    r.hmset(dbsilo_info_key, dbsilo_info_data)

if __name__ == "__main__":
    add_silo()
