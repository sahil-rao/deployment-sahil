#!/usr/bin/python

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import smtplib
import time
from pymongo import MongoClient
from flightpath.Provenance import getMongoServer
from Crypto.Cipher import AES
import encdec
import os


def sendEmail(formattedData):
	encdec.decrypt_file('sender.txt.enc')
	with open('sender.txt') as f0:
		fromAddress = f0.readline()
		password = f0.readline()
	os.remove('sender.txt')
	with open('failurerecipients.txt') as f:
		recipients = f.readlines()

	msg = MIMEMultipart('alternative')
	msg['Subject'] = 'Upload Failure Update'
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


def twoMinutesAgo():
	twoMinutesInMilliSeconds = 2 * 60 * 1000
	return time.time() * 1000 - twoMinutesInMilliSeconds


def isGreaterThanTwoMinutes(start, end):
	twoMinutesInMilliSeconds = 2 * 60 * 1000
	duration = end - start
	if(duration > twoMinutesInMilliSeconds):
		return 'Upload took more than two minutes'
	return ''


def hasCountError(document):
	if(document['Compiler']['count'] == 0):
		return 'Compiler has a count of 0'
	if(document['FPProcessing']['count'] == 0):
		return 'FPProcessing has a count of 0'
	if(document['Math']['count'] == 0):
		return 'Math has a count of 0'
	return ''


def findUploadsWithErrors(uploads):
	timeLimit = twoMinutesAgo()
	uploadStatsCursor = uploads.find({"timestamp" : {"$gte" : timeLimit}}, {"timestamp":1, "LastMessageProcessed":1,\
			"Compiler.count":1, "FPProcessing.count":1, "Math.count":1})
	uploadErrors = list()
	for upload in uploadStatsCursor:
		tempUploadErrors = dict()
		if(len(upload) != 6):
			tempUploadErrors['_id'] = upload['_id']
			tempUploadErrors['error'] = 'Does not contain all fields'
			uploadErrors.append(tempUploadErrors)
			continue
		errorMessage = hasCountError(upload)
		if(errorMessage != ''):
			tempUploadErrors['_id'] = upload['_id']
			tempUploadErrors['error'] = errorMessage
			uploadErrors.append(tempUploadErrors)
			continue
		errorMessage = isGreaterThanTwoMinutes(upload['timestamp'], upload['LastMessageProcessed'])
		if(errorMessage != ''):
			tempUploadErrors['_id'] = upload['_id']
			tempUploadErrors['error'] = errorMessage
			uploadErrors.append(tempUploadErrors)
			continue
	return uploadErrors


def formatDataforEmail(uploadErrors):
	htmlStr = '<html><body>' 
	for user in uploadErrors:
		htmlStr += '<table border="2" style="width:300px"><tr><td></td><td>' + user
		htmlStr += '</td></tr><tr><th>MongoID</th> <th>Error Message</th></tr>'
		for upload in uploadErrors[user]:
			htmlStr += '<tr><td>'
			htmlStr += str(upload['_id'])
			htmlStr += '</td> <td>'
			htmlStr += upload['error']
			htmlStr += '</td></tr>'
		htmlStr += '</table></br>'
	htmlStr += '</body></html>'
	return htmlStr

def run():

	try:
		mongo_host = getMongoServer('xplainDb')
	except:
		mongo_host = getMongoServer()

	client = MongoClient(host=mongo_host)
	tenantCursor = client['xplainIO'].organizations.find({},{"_id":0, "guid":1, "users":1})
	uploadInfo = dict()
	for tenantID in tenantCursor:
		tenant = tenantID['guid']
		mongo_host = getMongoServer(tenant)
		client = MongoClient(host=mongo_host)
		db = client[tenant]
		uploadStatsDocs = db.uploadStats
		uploadsOfInterest = findUploadsWithErrors(uploadStatsDocs)
		if len(uploadsOfInterest) > 0:
			uploadInfo[tenantID['users'][0]] = uploadsOfInterest

	if len(uploadInfo) > 0:
		formattedData = formatDataforEmail(uploadInfo)
		sendEmail(formattedData)

run()
