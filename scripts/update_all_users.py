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
            mongo_client[db].data_files.update({'dashboard_v4.layout': 'dashboard_layout_v4'},
                                                 { "dashboard_v4": { 
                                                        "layout": "dashboard_layout_v4", 
                                                        "components": [ 
                                                            { "topbar": "dashboard_topbar_v4" },
                                                            { "insights": "insights_v2" },
                                                            { "entity_rel_diagram_dashboard": "entity_rel_diagram_dashboard_v1" },
                                                            { "discover_design_transform": "discover_design_transform_v2" },
                                                            { "upload_modal": "upload_modal_v2" }, 
                                                            { "component_scripts": "dashboard_scripts_v4" }, 
                                                            { "component_stylesheets": "dashboard_stylesheets_v4" }], 
                                                        "template_engine_version": "1"}})

#run_workflow('mongodb://127.0.0.1')