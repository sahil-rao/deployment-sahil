from flightpath.Provenance import getMongoServer
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *

def run_workflow(mongo_url):

    mongo_client = MongoClient(mongo_url)

    for db in mongo_client.database_names():
        if "data_files" not in mongo_client[db].collection_names():
            continue

        if mongo_client[db].data_files.find_one({"dashboard_topbar_v4.file" : "dashboard_topbar_v4_demo.hbs"}) is not None:
            print "Upgrading " + db
            mongo_client[db].data_files.update({"dashboard_topbar_v4.file" : "dashboard_topbar_v4_demo.hbs"}, {'$set' : {"dashboard_topbar_v4.file":"dashboard_topbar_v4.hbs"}})

#run_workflow('mongodb://127.0.0.1')