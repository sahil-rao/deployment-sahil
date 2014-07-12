import pika
import logging
import traceback
import ConfigParser
from json import *
from flightpath.services.XplainBlockingConnection import *

connection = BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

msg_dict = {'tenant':"ea8c1b42-7859-4c0a-b30f-e472b726a36d", 'opcode':"HbaseDDL", "entityid":'1000'}
job_instances = [{"patID":"ce3fcb16-0944-11e4-9805-080027368542"}]
msg_dict['job_instances'] = job_instances
print msg_dict
message = dumps(msg_dict)

channel.basic_publish(exchange='', routing_key='compilerqueue', body=message)