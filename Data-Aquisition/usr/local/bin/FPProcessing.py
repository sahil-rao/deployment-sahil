#!/usr/bin/python

"""
Parse the Hadoop logs from the given path and populate flightpath
Usage : FPProcessing.py <tenent> <log Directory>
"""
from flightpath.parsing.hadoop.HadoopConnector import *
import sys
from flightpath.MongoConnector import *

logpath = ""
context = ""
if len(sys.argv) < 4:
    print "Error: incomplete Arguments"
    exit(0)

context = sys.argv[1]
logpath = sys.argv[2]

if logpath == "" or context == "":
    print "Error: Parameters incorrect"
    exit(0)

connector = HadoopConnector({'logpath':logpath})
mongoconn = Connector.getConnector(context)
if mongoconn is None:
    mongoconn = MongoConnector({'host':'172.31.2.130', 'context':context, \
                                'create_db_if_not_exist':True})

for ev in connector.events:
    initiator = None
    for en in ev.initiators:
        initiator = en

    if ev.targets is not None:
        for en in ev.targets:
            connector.formRelation(initiator, en, 'WRITE')

    for en in ev.cohorts:
        connector.formRelation(en, initiator, 'READ')

'''
The graph is now created.
'''

for en in connector.entities:
    entity = connector.getEntity(en)
    print "Entity"
    mongoconn.updateEntity(entity)

for rel in connector.relations:
    mongoconn.updateConsociation(rel)

for en in connector.entities:
    mongoconn.getEntity(en)

client = MongoClient(host="172.31.2.130")
db = client[context]

m = db.processedFile
m.insert({"filename":sys.argv[3]})
print "SUCCESS"
