import datetime
import time
import sys
import os
from json import *

REMAINDER_FILE = "/etc/ppp/peers/remainder"
def trialDaysRemaining():
    if not os.path.isfile(REMAINDER_FILE):
        return False

    """
    Get remaining Delta.
    """
    jfile = open(REMAINDER_FILE, "r")
    newdict = load(jfile)
    remain_delta = datetime.timedelta(microseconds=newdict["Delta"])
    jfile.close()
    return remain_delta.days
def timedelta_to_microsecond(delta):
    return delta.microseconds + (delta.seconds + delta.days * 86400) * 1000000

def isTrialOn():
    if not os.path.isfile(REMAINDER_FILE):
        return False

    """
    Get remaining Delta.
    """
    jfile = open(REMAINDER_FILE, "r")
    newdict = load(jfile)
    remain_delta = datetime.timedelta(microseconds=newdict["Delta"])
    #print remain_delta
    jfile.close()

    if remain_delta.days < 0:
        return False

    """
    Now check if the remaining delta is less that current delta.
    That mean we have gone back in time. If this is the case, then deduct one
    day.
    """
    delta = datetime.datetime(2014, 03, 31) - datetime.datetime.now()
    if delta.days < 0: 
        return False;

    #print "delta is ", delta
    #if remain_delta < delta:
    #    remain_delta = remain_delta - datetime.timedelta(days=1)

    if remain_delta > delta:
        remain_delta = delta
    msc = timedelta_to_microsecond(remain_delta)

    jdict = { "Delta": msc}
    jfile = open(REMAINDER_FILE, "w")
    dump(jdict, jfile)
    jfile.close()
    return True






