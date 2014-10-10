#!/usr/bin/python                                                                                                                                                                                                                                                             
import redis

def add_silo():
    r = redis.StrictRedis(host="127.0.0.1", port=6379, db=0)

    #Add new dbsilo keys to metakey sets                                                                                                                                                                                                                                      
    dbsilo_info_metakey = "dbsilo:metakey:info"
    dbsilo_info_key = "dbsilo:Silo1:info"
    r.sadd(dbsilo_info_metakey, dbsilo_info_key)
    dbsilo_tenants_metakey = "dbsilo:metakey:tenants"
    dbsilo_tenants_key = "dbsilo:Silo1:tenants"
    r.sadd(dbsilo_tenants_metakey, dbsilo_tenants_key)

    #Add information about silo to redis                                                                                                                                                                                                                                      
    dbsilo_info_data = { "mongo": "mongodb://127.0.0.1/",
                         "redis": "redismasterSilo1",
                         "elastic": "127.0.0.1",
                         "capacitylimit": "100",
                         "name": "Silo1" }
    r.hmset(dbsilo_info_key, dbsilo_info_data)

if __name__ == "__main__":
    add_silo()
