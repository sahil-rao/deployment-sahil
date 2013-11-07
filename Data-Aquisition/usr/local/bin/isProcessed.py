#!/usr/bin/python

""" Checks if the given file has already been processed and checkpointed.
Usage: isProcessed.py <tenent> <file name>
"""
import sys
from pymongo import *

if len(sys.argv) < 2:
    print 0
    exit(0)

tenent=sys.argv[1]

client = MongoClient(host="172.31.2.130")
db = client[tenent]

m = db.processedFile
print m.find({"filename":sys.argv[2]}).count()


