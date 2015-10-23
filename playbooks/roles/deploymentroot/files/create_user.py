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

    #Register user
    headers = {'content-type': 'application/json'}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        response = requests.post(nodejs_url + 'register', json={'email': email_address}, headers=headers, verify=False)
        if 'successRedirect' not in response.json():
            print response.json()
            return 'fail'
        response = requests.post(nodejs_url + 'uploadUpgrade', json={'email': email_address, 'password': random_password}, headers=headers, verify=False)
        if 'upgradeComplete' not in response.json() or not response.json()['upgradeComplete']:
            print response.json()
            return 'fail'

    #create email HTML message
    env = Environment(loader=FileSystemLoader('/var/www/templates'))
    template = env.get_template('account_creation.html')
    html_string = template.render(password=random_password).encode('utf-8')

    #Send email to user
    from_address = 'no-reply-data@cloudera.com'
    from_password = 'D8eH5C8T'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Welcome to Cloudera Optimizer Beta!'
    msg['From'] = from_address
    msg['To'] = email_address
    email_text = 'Congratulations! You have been accepted into Cloudera Optimizer Beta. Your password is: ' + random_password + '. \nPlease change your password as soon as you log in. Thanks!'
    msg.attach(MIMEText(email_text, 'plain'))
    msg.attach(MIMEText(html_string, 'html'))

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(from_address, from_password)
    server.helo()
    server.sendmail(from_address, email_address, msg.as_string())
    server.quit()

    return 'success'

if __name__ == '__main__':
    print execute(sys.argv[1])
