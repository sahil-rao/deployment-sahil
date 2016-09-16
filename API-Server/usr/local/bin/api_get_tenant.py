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

def execute(email, msg_dict=None):
    '''
    Returns the details of the query with give entity_id.
    '''
    if 'email' is None:
        return

    xplaindb = getMongoServer('xplainIO')['xplainIO']
    t_dict = {}

    entry = xplaindb.users.find_one({"email":email}, {"lastSelectedWorkload":1})
    if entry:
        t_dict['tenant'] = entry['lastSelectedWorkload']

    return t_dict

if __name__ == '__main__':
    pprint.pprint(execute(sys.argv[1], {}))
