import datetime
import csv
from pprint import pprint
from flightpath.Provenance import getMongoServer


def get_user(db, user_name, user_map):
    '''
    Gets users info.
    Checks in cache first.
    '''
    if user_name in user_map:
        return user_map[user_name]
    user_info = db.users.find_one({'email': user_name})
    user_map[user_name] = user_info
    return user_map[user_name]


def get_uploads(db, tenantid, workload_map, rpt_since_time):
    '''
    Gets uploadStats info.
    Checks in cache first.
    '''
    if tenantid in workload_map:
        return workload_map[tenantid]
    upload_cursor = db.uploadStats.find({'timestamp': {'$gt': rpt_since_time}})
    workload_map[tenantid] = [x for x in upload_cursor]
    return workload_map[tenantid]


def get_logins(db, tenantid, login_map, rpt_since_time):
    '''
    Gets events info.
    Checks in cache first.
    '''
    if tenantid in login_map:
        return login_map[tenantid]
    login_cursor = db.events.find({'timestamp': {'$gt': rpt_since_time}, 'event': 'login'})
    login_map[tenantid] = [x for x in login_cursor]
    return login_map[tenantid]


def execute(tenantid, msg_dict):
    '''
    Loop through all organizations.
    Attribute to a company.
    only count for events after 1468393200000 (7/13/2016 midnight pst)
    uploads --> tenant.uploadStats
    logins --> tenant.events
    queries --> source_platform then use Compiler
    signed_terms --> xplainIO.users
    '''

    xplaindb = getMongoServer('xplainIO')['xplainIO']
    workload_cursor = xplaindb.organizations.find()
    orgs_json = {}
    user_map = {}
    login_map = {}
    workload_map = {}

    TIMESTAMP = 1468393200000

    for workload in workload_cursor:
        tenantid = workload['guid']
        tenantdb = getMongoServer(tenantid)[tenantid]

        logins = get_logins(tenantdb, tenantid, login_map, TIMESTAMP)
        uploads = get_uploads(tenantdb, tenantid, workload_map, TIMESTAMP)

        if (not len(logins)) and (not len(uploads)):
            #print 'No logins nor uploads for tenantid: %s' % tenantid
            continue

        queries = sum([x['processed_queries'] for x in uploads if 'processed_queries' in x])

        for user in workload['users']:
            try:
                domain = user.split('@')[1].split('.')[0]
                website_url = user.split('@')[1]
            except (KeyError, IndexError):
                domain = 'unknown'

            user_info = get_user(xplaindb, user, user_map)

            if domain not in orgs_json:
                orgs_json[domain] = {'name': domain,
                                     'website_url': website_url,
                                     'unique_user_emails': set(),
                                     'users': 0,
                                     'uploads': 0,
                                     'queries': 0,
                                     'workloads': 0,
                                     'signed_terms': 0,
                                     'logins': 0,
                                     'queries': 0}

            if user not in orgs_json[domain]['unique_user_emails']:
                if 'signed_terms' in user_info and user_info['signed_terms']:
                    orgs_json[domain]['signed_terms'] += 1

            orgs_json[domain]['unique_user_emails'].add(user)
            orgs_json[domain]['users'] = len(orgs_json[domain]['unique_user_emails'])
            orgs_json[domain]['uploads'] += len(uploads)
            orgs_json[domain]['logins'] += len(logins)
            orgs_json[domain]['queries'] += queries
            orgs_json[domain]['workloads'] += 1

    return_list = orgs_json.values()
    keys = [u'name', u'signed_terms', u'users', u'uploads',
            u'logins', u'queries', u'workloads', u'website_url']
    '''
    Removes extra keys from the user information dictionary
    '''
    for i, org in enumerate(return_list):
        extras = set(org.keys()) - set(keys)
        if extras:
            for x in extras:
                del return_list[i][x]

    '''
    Write to the people.csv file.
    '''
    with open('user_report.csv', 'wb') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(return_list)

    return orgs_json


if __name__ == '__main__':
    a = execute("not_used", '.*')
    #pprint(a)
