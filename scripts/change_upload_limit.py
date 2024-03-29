# (c) Copyright 2017 Cloudera, Inc. All rights reserved.

"""
Script to change upload limits for all existing organizations in Mongo
"""

from flightpath.Provenance import getMongoServer

DEFAULT_UPLOAD_LIMIT = 150000


def execute():
    '''
    Sets upload limits to a given value for all organizations in the xplainIO db
    '''
    client = getMongoServer('xplainIO')

    db = client['xplainIO']

    orgs_curr = db.organizations.find({}, {"_id": 0})
    orgs = [org for org in orgs_curr]

    for org in orgs:
        if 'upLimit' in org:
            if type(org['upLimit']) == int:
                if org['upLimit'] >= DEFAULT_UPLOAD_LIMIT:
                    continue
        print org
        db.organizations.update_one({'guid': org['guid']},
                                    {'$set': {"upLimit": DEFAULT_UPLOAD_LIMIT}})

if __name__ == '__main__':
    execute()
