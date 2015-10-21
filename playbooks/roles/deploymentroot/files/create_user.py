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
    
    #create random password for new user
    word1 = random.choice(open('/usr/share/dict/fourletterwords').readlines())
    word2 = random.choice(open('/usr/share/dict/fourletterwords').readlines())
    num1 = random.randint(100, 999)
    num2 = random.randint(100, 999)
    random_password = (word1 + str(num1) + word2 + str(num2)).replace('\n', '')

    #Register user and generate token
    headers = {'content-type': 'application/json'}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        response = requests.post(nodejs_url + 'register', json={'email': email_address}, headers=headers, verify=False)
        if 'successRedirect' not in response.json():
            print response.json()
            return 'fail'
        response = requests.post(nodejs_url + 'uploadUpgrade', json={'email': email_address, 'password': random_password}, headers=headers, verify=False)
        if 'upgradeComplete' not in response.json() or not response.json()['upgradeComplete']:
            print response.json(
            return 'fail'
        response = requests.post(nodejs_url + 'app/generateVerificationCodeForNewUser/', json={'email': email_address}, headers=headers, verify=False)
        if 'success' not in response.json():
            print response.json()
            return 'fail'

    return 'success'

if __name__ == '__main__':
    print execute(sys.argv[1])
