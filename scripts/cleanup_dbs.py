# (c) Copyright 2015 Cloudera, Inc. All rights reserved.

from flightpath import FPConnector
from flightpath.Provenance import getMongoServer


def remove_org(client, org):
    print "dropping org: %s" % (org)
    xplain_db = client['xplainIO']
    try:
        xplain_db.users.update({'archived': org},
                               {'$pull': {'archived': org}})
        client.drop_database(org)
        xplain_db.organizations.remove({'guid': org})

        temp_client = getMongoServer(org)
        temp_client.drop_database(org)
        FPConnector.delete_tenant_from_silo(org)
    except:
        print "error dropping org: %s" % (org)
    return True


def execute(email):
    xplain = 'xplainIO'
    client = getMongoServer(xplain)

    xplain_db = client['xplainIO']

    mongo_params = {'archived': 1, '_id': 0, 'email': 1}
    if email and email is not None:
        user_cur = xplain_db.users.find({'email': email}, mongo_params)
    else:
        user_cur = xplain_db.users.find({}, mongo_params)

    # bring the items into memory
    user_list = [x for x in user_cur]
    for user_obj in user_list:
        archived = []
        if 'archived' in user_obj:
            archived = user_obj['archived']

        for org in archived:
            remove_org(client, org)

if __name__ == '__main__':
    execute(None)
