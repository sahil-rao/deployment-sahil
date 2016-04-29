#!/usr/bin/python

"""
Application API to get details for a given SQL query

"""
__author__ = 'Samir Pujari'
__copyright__ = 'Copyright 2014, Xplain.IO Inc.'
__license__ = ''
__version__ = '0.1'
__maintainer__ = 'Samir Pujari'
__email__ = 'samir@xplain.io'

from pymongo import MongoClient
from flightpath.MongoConnector import *
import json
from flightpath.Provenance import getMongoServer
import sys
import pprint
import flightpath.utils as utils
from flightpath.RedisConnector import *
from collections import OrderedDict
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import smtplib

users_skip_list = [
    "parna@cloudera.com",
    "sakinapelli@cloudera.com",
    "samir@cloudera.com",
    "sangeeta@cloudera.com",
    "ewa@cloudera.com",
    "prithviraj.pandian@cloudera.com",
    "ravi@cloudera.com",
    "dmitri@cloudera.com",
    "sean.wensel@cloudera.com",
    "irina@cloudera.com",
    "avsingh@cloudera.com",
    "harshil@cloudera.com",
    "erickt@cloudera.com",
    "laurel@cloudera.com"
]

recipients_list = [
    "data-mgmt@cloudera.com"
]


def formatDataforEmail(userInfoDict, top_users_by_queries, top_users_by_uploads, users_by_domain, top_users_by_logins, top_users_by_logouts):
    htmlStr = '<html><body>'
    htmlStr += '<h1><font color="#660000">User Activity Info for a Week</font></h1>'
    
    htmlStr += '<h3><font color="#0000FF">Top Users by number of queries</font></h3>'
    htmlStr += '<table border="2" style="width:300px">'
    htmlStr += '<tr><th>Users</th> <th>Number of Uploads</th> <th>Number of queries</th></tr>'
    for user in top_users_by_queries:
        htmlStr += '<tr><td>'
        htmlStr += user
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['number_of_uploads'])
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['total_queries'])
        htmlStr += '</td></tr>'
    htmlStr += '</table></br>'
    
    htmlStr += '<h3><font color="#0000FF">Top Users by number of uploads</font></h3>'
    htmlStr += '<table border="2" style="width:300px">'
    htmlStr += '<tr><th>Users</th> <th>Number of Uploads</th> <th>Number of queries</th></tr>'
    for user in top_users_by_uploads:
        htmlStr += '<tr><td>'
        htmlStr += user
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['number_of_uploads'])
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['total_queries'])
        htmlStr += '</td></tr>'
    htmlStr += '</table></br>'

    htmlStr += '<h3><font color="#0000FF">Users Filtered by Domain</font></h3>'
    for domain, user in users_by_domain.iteritems():
        htmlStr += '<h4> <font color="#FF0000">Domain name: ' + domain + '</font></h4>'
        htmlStr += '<table border="2" style="width:300px">'
        htmlStr += '<tr><th>Users</th> <th>Number of Uploads</th> <th>Number of queries</th></tr>'
        for email, data in user.iteritems():
            htmlStr += '<tr><td>'
            htmlStr += email
            htmlStr += '</td> <td>'
            htmlStr += str(user[email]['number_of_uploads'])
            htmlStr += '</td> <td>'
            htmlStr += str(user[email]['total_queries'])
            htmlStr += '</td></tr>'
        htmlStr += '</table></br>'
   
    htmlStr += '<h3><font color="#0000FF">Top Users by number of logins</font></h3>'
    htmlStr += '<table border="2" style="width:300px">'
    htmlStr += '<tr><th>Users</th> <th>Number of Logins</th> <th>Number of Logouts</th> <th>Number of Uploads</th> <th>Number of queries</th> </tr>'
    for user in top_users_by_logins:
        htmlStr += '<tr><td>'
        htmlStr += user
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['number_of_logins'])
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['number_of_logouts'])
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['number_of_uploads'])
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['total_queries'])
        htmlStr += '</td></tr>'
    htmlStr += '</table></br>'

    htmlStr += '<h3><font color="#0000FF">Top Users by number of logouts</font></h3>'
    htmlStr += '<table border="2" style="width:300px">'
    htmlStr += '<tr><th>Users</th> <th>Number of Logouts</th> <th>Number of Logins</th> <th>Number of Uploads</th> <th>Number of queries</th> </tr>'
    for user in top_users_by_logouts:
        htmlStr += '<tr><td>'
        htmlStr += user
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['number_of_logouts'])
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['number_of_logins'])
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['number_of_uploads'])
        htmlStr += '</td> <td>'
        htmlStr += str(userInfoDict[user]['total_queries'])
        htmlStr += '</td></tr>'
    htmlStr += '</table></br>'

    htmlStr += '</body></html>'

    return htmlStr

def sendEmail(formattedData):

    fromAddress = "no-reply-data@cloudera.com" 
    password = "D8eH5C8T"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Weekly User Activity Update'
    msg['From'] = fromAddress
    msg['To'] = ', '.join(recipients_list)
    part2 = MIMEText(formattedData, 'html')
    msg.attach(part2)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(fromAddress, password)
    server.helo()
    server.sendmail(fromAddress, recipients_list, msg.as_string())
    server.quit()

def filter_users_by_domain(user_info):
    filter_domain_dict = dict()
    for key, value in user_info.iteritems():
        user_id, domain = key.split('@')
        if domain not in filter_domain_dict:
            filter_domain_dict[domain] = {}
        filter_domain_dict[domain][key] = value
    return filter_domain_dict

def execute():
    '''
    Returns the details of the query with give entity_id.
    '''
    client = getMongoServer('xplainDb')
    tenantCursor = client['xplainIO'].users.find({},{"_id":0, "organizations":1, "email":1})
    t_dict = {}
    for tenant_data in tenantCursor:
        if 'organizations' not in tenant_data or tenant_data['email'] in users_skip_list:
            continue
        user = tenant_data['email']
        tenants = tenant_data['organizations']
        for tenant in tenants:
            tclient = getMongoServer(tenant)
            db = tclient[tenant]
            uploadStats = db.uploadStats
            upload_cursor = uploadStats.find({ 'tenant': tenant, '$where': 'function ()'+ 
                                             '{ return Date.now() - this.timestamp < (7 * 24 * 60 * 60 * 1000)  }'
                                             }, {"uid":1, "total_queries":1})
            for upload in upload_cursor:
                if 'uid' not in upload:
                    continue
                if user not in t_dict:
                    t_dict[user] = {}
                    t_dict[user]['number_of_logins'] = 0
                    t_dict[user]['number_of_logouts'] = 0
                    '''
                    t_dict[user]['tenants'] = tenants
                    '''
                if 'uid' not in t_dict[user]:
                    t_dict[user]['uid'] = []
                t_dict[user]['uid'].append(upload['uid'])

                if 'total_queries' not in t_dict[user]:
                    t_dict[user]['total_queries'] = 0
                if 'total_queries' in upload:
                    t_dict[user]['total_queries'] += int(upload['total_queries'])
   
                event_cursor = db.events.find({'tenant': tenant, '$where': 'function ()'+ 
                                              '{ return Date.now() - this.timestamp < (7 * 24 * 60 * 60 * 1000)  }'
                                              }, {"event":1})
                for event in event_cursor:
                    if event['event'] == 'login':
                        t_dict[user]['number_of_logins'] += 1 
                    if event['event'] == 'logout':
                        t_dict[user]['number_of_logouts'] += 1
        if user in t_dict:
            t_dict[user]['number_of_uploads'] = len(t_dict[user]['uid'])
            t_dict[user].pop("uid", None)

    #make sure we have some data
    if t_dict:
        top_users_by_queries = sorted(t_dict, key=lambda x: t_dict[x]['total_queries'], reverse=True)
        top_users_by_uploads = sorted(t_dict, key=lambda x: (t_dict[x]['number_of_uploads']), reverse=True)
        top_users_by_logins = sorted(t_dict, key=lambda x: t_dict[x]['number_of_logins'] 
                                     if 'number_of_logins' in t_dict[x] else 0 , reverse=True)
        top_users_by_logouts = sorted(t_dict, key=lambda x: (t_dict[x]['number_of_logouts'] 
                                      if 'number_of_logouts' in t_dict[x] else 0), reverse=True)
        users_by_domain = filter_users_by_domain(t_dict)

        #make sure we have atleast either of sorted data.
        if (top_users_by_queries or top_users_by_uploads or top_users_by_logins or 
            top_users_by_logouts or users_by_domain):
            formattedData = formatDataforEmail(t_dict, top_users_by_queries, top_users_by_uploads, users_by_domain, 
                                               top_users_by_logins, top_users_by_logouts) 
            sendEmail(formattedData)
    return t_dict

if __name__ == '__main__':
    top_uploads = execute()
    print "details", json.dumps(top_uploads, indent=2)
    '''
    top_queries, top_uploads = execute()
    print "Top Queries:", json.dumps(top_queries, indent=2)
    print "Top Uploads:", json.dumps(top_uploads, indent=2)
    '''
