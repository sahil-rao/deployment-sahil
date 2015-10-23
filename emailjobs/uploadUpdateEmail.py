#!/usr/bin/python

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import smtplib
import time
from pymongo import MongoClient
from flightpath.Provenance import getMongoServer
from Crypto.Cipher import AES
import os
import ConfigParser
import encdec


def twelveHoursAgo():
	twelveHoursInMilliSeconds = 12 * 60 * 60 * 1000
	return time.time() * 1000 - twelveHoursInMilliSeconds


def getMatchingDocuments(entities):
	timeLimit = twelveHoursAgo()
	uploadStatsCursor = entities.find({"timestamp":{"$gte":timeLimit}})
	uploadStatsArray = list()
	for uploadStats in uploadStatsCursor:
		uploadStatsTempDict = dict()
		if 'timestamp' in uploadStats:
			uploadStatsTempDict['time'] = time.ctime((int(uploadStats['timestamp'])/1000))

                if "total_queries" in uploadStats:
			uploadStatsTempDict['queriesUploaded'] = uploadStats['total_queries']
		else:
			uploadStatsTempDict['queriesUploaded'] = 0

                if "filename" in uploadStats:
			uploadStatsTempDict['filename'] = uploadStats['filename'].split('/')[2]
		else:
			uploadStatsTempDict['filename'] = ""

		uploadStatsArray.append(uploadStatsTempDict)
	return uploadStatsArray



def formatDataforEmail(uploadInfoDict):
	htmlStr = '<html><body>' 
	for user in uploadInfoDict:
		htmlStr += '<table border="2" style="width:300px"><tr><td></td><td>' + user
		htmlStr += '</td><td></td></tr><tr><th>File</th> <th>Queries Uploaded</th> <th>Time</th></tr>'
		for upload in uploadInfoDict[user]:
			htmlStr += '<tr><td>'
			htmlStr += upload['filename']
			htmlStr += '</td> <td>'
			htmlStr += str(upload['queriesUploaded'])
			htmlStr += '</td> <td>'
			htmlStr += upload['time']
			htmlStr += '</td></tr>'
		htmlStr += '</table></br>'
	htmlStr += '</body></html>'
	return htmlStr



def sendEmail(formattedData):
	config = ConfigParser.RawConfigParser ()
	config.read("/var/Baaz/emails.cfg")
	encdec.decrypt_file('/var/Baaz/sender.txt.enc')
	with open('/var/Baaz/sender.txt') as f0:
		fromAddress = f0.readline()
		password = f0.readline()
	os.remove('/var/Baaz/sender.txt')
	recipients = config.get('updateRecipients', 'recipient')
	cluster = config.get('cluster', 'name')
	recipients.replace(' ', '')
	recipients.replace('\n', '')
	recipients = recipients.split(",")

	msg = MIMEMultipart('alternative')
	msg['Subject'] = '12 Hour Activity Update for ' + cluster
	msg['From'] = fromAddress
	msg['To'] = ", ".join(recipients)
	plainTextBody = 'The following are the uploads of users in the last 12 hours: '
	part1 = MIMEText(plainTextBody, 'plain')
	part2 = MIMEText(formattedData, 'html')
	msg.attach(part1)
	msg.attach(part2)

	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(fromAddress, password)
	server.helo()
	server.sendmail(fromAddress, recipients, msg.as_string())
	server.quit()

def run():

    client = getMongoServer('xplainDb')

    print "Starting new run on uploadUpdateEmail"
    tenantCursor = client['xplainIO'].organizations.find({},{"_id":0, "guid":1, "users":1})
    uploadInfo = dict()
    for tenantID in tenantCursor:
    	tenant = tenantID['guid']
    	client = getMongoServer(tenant)
    	db = client[tenant]
    	uploadStatsDocs = db.uploadStats
    	uploadsOfInterest = getMatchingDocuments(uploadStatsDocs)
    	if len(uploadsOfInterest) > 0:
        	print tenant, " # of uploads of interest :", len(uploadsOfInterest)
    		uploadInfo[tenantID['users'][0]] = uploadsOfInterest
    
    if len(uploadInfo) > 0:
	    formattedData = formatDataforEmail(uploadInfo)
            print "Sending upload stats Email" 
	    sendEmail(formattedData)


run()
