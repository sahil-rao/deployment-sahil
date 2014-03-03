#!/usr/bin/python

from ConfigParser import RawConfigParser
from flightpath.trialperiod import *
import socket, fcntl, struct

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915, struct.pack('256s', ifname[:15]))[20:24])
    
if not os.path.isfile("/var/Baaz/runtime.cfg"):
    exit(0)

config = RawConfigParser()
config.read("/var/Baaz/runtime.cfg")

days = trialDaysRemaining()
config.set("Trial", "days", days)
ipaddress = None
ipaddress = get_ip_address("eth0")
if ipaddress is not None:
    config.set("Trial", "Address", ipaddress)

jfile = open("/var/Baaz/runtime.cfg", "w")
config.write(jfile)
jfile.close()
exit(0)

