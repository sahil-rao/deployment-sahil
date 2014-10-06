#!/usr/bin/python

import time
from pymongo import MongoClient
from flightpath.Provenance import getMongoServer
from flightpath.services.RabbitMQConnectionManager import *
import os
import ConfigParser
from json import *
import uuid

def twentyFourHoursAgo():
	twelveHoursInMilliSeconds = 24 * 60 * 60 * 1000
	return time.time() * 1000 - twelveHoursInMilliSeconds

def get_rabbit_servers():
    '''
    This function uses the hosts (/var/Baaz/hosts.cfg) file to get the IP
    addresses or hosts to connect to. The hosts file stores the
    rabbit information in a concatendated string list of all the 
    hosts and  port number
    '''
    rabbit_servers = {}
    config = ConfigParser.RawConfigParser()
    config.read("/var/Baaz/hosts.cfg")
    rawStr = config.get("RabbitMQ", "server")
    host_list = rawStr.split(",")
    for host_index in range(0,len(host_list)):
        host_info = host_list[host_index].split(":")
        rabbit_servers[host_index] = {}
        rabbit_servers[host_index]['host'] = host_info[0]
        try:
            rabbit_servers[host_index]['port'] = int(host_info[1])
        except:
            rabbit_servers[host_index]['port'] = None
    return rabbit_servers

class XplainRPC(object):
    def __init__(self):
        rabbitservers = get_rabbit_servers()
        credentials = pika.PlainCredentials('xplain', 'xplain')
        vhost = 'xplain'

        for r_server in rabbitservers:
            try:
                self.connection = BlockingConnection(pika.ConnectionParameters(rabbitservers[r_server]['host'],
                                                                      rabbitservers[r_server]['port'],
                                                                      vhost, credentials))
                break
            except:
                pass

        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='', routing_key='appservicequeue',
            properties=pika.BasicProperties(reply_to = self.callback_queue, correlation_id = self.corr_id,),
            body=n)
        while self.response is None:
            self.connection.process_data_events()
        return loads(self.response)

def run():

    try:
        mongo_host = getMongoServer('xplainDb')
    except:
        mongo_host = getMongoServer()

    config = ConfigParser.RawConfigParser ()
    config.read("/var/Baaz/hosts.cfg")

    rpc = XplainRPC()
    client = MongoClient(host=mongo_host)
    timelimit = twentyFourHoursAgo()
    tenantCursor = client['xplainIO'].organizations.find({"isDemo":True, "lastTimeStamp": { "$lt": timelimit}},{"_id":0, "guid":1, "lastTimeStamp":1, "users":1})
    for tenantID in tenantCursor:
    	tenant = tenantID['guid']

    	msg_dict = {}
    	msg_dict['tenant'] = tenant
    	msg_dict["opcode"] = "DeleteTenant"
    	rpc.call(dumps(msg_dict))

run()

