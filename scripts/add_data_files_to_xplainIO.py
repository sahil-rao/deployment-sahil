# (c) Copyright 2015 Cloudera, Inc. All rights reserved.

from flightpath.Provenance import getMongoServer


def update_xplainio(data_files):
    '''
    Makes sure the data files are present in the xplainIO db in mongo
        this makes sure all the pages in the UI are rendered.
    '''
    xplain = 'xplainIO'
    client = getMongoServer(xplain)
    xplain_db = client[xplain]
    for x in data_files:
        xplain_db.data_files.update({"_id": x["_id"]}, x, upsert=True)


if __name__ == '__main__':
    data_files = [{"_id": 1,
                   "dashboard_layout_v4": {"file": "dashboard_v4.hbs",
                                           "template_engine_version": "1"}},
                  {"_id": 2,
                   "dashboard_v4": {"layout": "dashboard_layout_v4",
                                    "components": [{"topbar": "dashboard_topbar_v4"},
                                                   {"insights": "insights_v2"},
                                                   {"entity_rel_diagram_dashboard": "entity_rel_diagram_dashboard_v1"},
                                                   {"discover_design_transform": "discover_design_transform_v2"},
                                                   {"upload_modal": "upload_modal_v2"},
                                                   {"component_scripts": "dashboard_scripts_v4"},
                                                   {"component_stylesheets": "dashboard_stylesheets_v4"}],
                                    "template_engine_version": "1"}},
                  {"_id": 3,
                   "dashboard_topbar_v4": {"file": "dashboard_topbar_v4.hbs",
                                           "template_engine_version": "1"}},
                  {"_id": 4,
                   "entity_rel_diagram_dashboard_v1": {"file": "entity_rel_diagram_dashboard_v1.hbs",
                                                       "template_engine_version": "1"}},
                  {"_id": 5,
                   "discover_design_transform_v2": {"file": "discover_design_transform_v2.hbs",
                                                    "template_engine_version": "1"}},
                  {"_id": 6,
                   "dashboard_scripts_v4": {"file": "scripts/dashboard_scripts_v4.hbs",
                                            "template_engine_version": "1"}},
                  {"_id": 7,
                   "dashboard_stylesheets_v4": {"file": "stylesheets/dashboard_stylesheets_v4.hbs",
                                                "template_engine_version": "1"}},
                  {"_id": 8,
                   "insights_v2": {"file": "insights_v2.hbs",
                                   "template_engine_version": "1"}},
                  {"_id": 9,
                   "upload_modal_v2": {"file": "upload_modal_v2.hbs",
                                       "template_engine_version": "1"}}
                  ]
    update_xplainio(data_files)
