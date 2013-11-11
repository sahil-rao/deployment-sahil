#!/usr/bin/python

import boto
from boto.s3.key import Key
import sys

splits = sys.argv[1].split()

tenent = splits[7].strip('",[]')
filename = splits[12].strip('",[]')

source = "/mnt/volume1/" + tenent + filename
destination = tenent + "/" + filename.rsplit("/", 1)[1]

print source, destination
connection = boto.connect_s3()
bucket = connection.get_bucket('partner-logs') # substitute your bucket name here
file_key = Key(bucket)
file_key.key = destination

file_key.set_contents_from_filename(source)

print "File upload done"
