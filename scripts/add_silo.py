#!/usr/bin/python
import redis

def add_silo():

    new_silo_info = {
        "mongo": {
            "nodes": "172.31.19.214,172.31.32.144,172.31.32.145"
        },
        "redis": {
            "nodes": "172.31.37.232,172.31.30.247,172.31.3.43"
        },
        "elasticsearch": {
            "nodes": "172.31.45.98,172.31.20.234,172.31.15.114"
        },
        "siloinfo": {
            "siloname": "dbsilo3",
            "capacitylimit": 1000
        }
    }

    redis_ip = "172.31.31.43"
    r = redis.StrictRedis(host=redis_ip, port=6379, db=0)

    #Add new dbsilo keys to metakey sets
    dbsilo_info_metakey = "dbsilo:metakey:info"
    dbsilo_info_key = "dbsilo:" + new_silo_info["siloinfo"]["siloname"] + ":info"
    r.sadd(dbsilo_info_metakey, dbsilo_info_key)
    dbsilo_tenants_metakey = "dbsilo:metakey:tenants"
    dbsilo_tenants_key = "dbsilo:" + new_silo_info["siloinfo"]["siloname"] + ":tenants"
    r.sadd(dbsilo_tenants_metakey, dbsilo_tenants_key)

    #Add information about silo to redis
    dbsilo_info_data = { "mongo": new_silo_info["mongo"]["nodes"],
                         "redis": new_silo_info["redis"]["nodes"],
                         "elastic": new_silo_info["elasticsearch"]["nodes"],
                         "capacitylimit": new_silo_info["siloinfo"]["capacitylimit"],
                         "name": new_silo_info["siloinfo"]["siloname"] }
    r.hmset(dbsilo_info_key, dbsilo_info_data)

if __name__ == "__main__":
    add_silo()
