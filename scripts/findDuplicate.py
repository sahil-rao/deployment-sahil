#!/usr/bin/python

from pymongo import *
from flightpath.MongoConnector import *
from flightpath.RedisConnector import *
from flightpath.Provenance import getMongoServer

def findDuplicatePattern(tenant):
	client = getMongoServer(tenant)

	db = client[tenant]
	patternsCollection = db.accessPatterns
	patternCursor = patternsCollection.find({}, {'jg':1})
	allPatterns = set()
	duplicates = set()
	for pattern in patternCursor:
		if pattern['jg'] not in allPatterns:
			allPatterns.add(pattern['jg'])
		else:
			duplicates.add(pattern['jg'])
	print duplicates


def findDuplicateJG(tenant):
	mongoHost = getMongoServer(tenant)
	client = MongoClient(host=mongoHost)
	db = client[tenant]
	entities = db.entities
	jgCursor = entities.find({"etype":"SQL_JOIN_GROUP"}, {'eid':1})
	allJGs = set()
	duplicates = set()
	for jg in jgCursor:
		if jg['eid'] not in allJGs:
			allJGs.add(jg['eid'])
		else:
			duplicates.add(jg['eid'])
	print duplicates


def printJGeids(tenant):
    mongoHost = getMongoServer(tenant)
    client = MongoClient(host=mongoHost)
    db = client[tenant]
    entities = db.entities
    jgCursor = entities.find({"etype":"SQL_JOIN_GROUP"})
    for jg in jgCursor:
        print jg["eid"]

findDuplicatePattern('67f66a44-91ae-00b7-e797-2ef969791d6a')