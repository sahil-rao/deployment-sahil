#!/usr/bin/env python
import sys
import random
import warnings
import smtplib
import ConfigParser
import requests
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from jinja2 import Environment, FileSystemLoader


def execute(email_address):
    #get cluster root ip
    config = ConfigParser.RawConfigParser()
    config.read("/var/Baaz/hosts.cfg")
    nodejs_url = config.get("NodeJS", "domain")
    
    #Generate token
    headers = {'content-type': 'application/json'}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        response = requests.post(nodejs_url + 'generateVerificationCodeForNewUser', json={'email': email_address}, headers=headers, verify=False)
        if 'success' not in response.json():
            print response.json()
            return 'fail'

    return 'success'

if __name__ == '__main__':
    print execute(sys.argv[1])
