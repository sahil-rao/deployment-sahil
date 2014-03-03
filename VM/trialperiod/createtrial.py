#!/usr/bin/python

import datetime
import time
import sys
import os
from json import *

REMAINDER_FILE = "/etc/ppp/peers/remainder"
def timedelta_to_microsecond(delta):
    return delta.microseconds + (delta.seconds + delta.days * 86400) * 1000000

def createTrial():

    delta = datetime.datetime(2014, 03, 31) - datetime.datetime.now()
    msc = timedelta_to_microsecond(delta)

    jdict = { "Delta": msc}
    jfile = open(REMAINDER_FILE, "w")
    dump(jdict, jfile)
    jfile.close()

createTrial()



