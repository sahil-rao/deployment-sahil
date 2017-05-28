#!/usr/bin/python

import os
import time
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import smtplib

def email_report(f):
    if f:
        f.seek(0)
        test_results = f.read()
    else:
        test_results = "NavOpt API Test Failed"
    #TODO: Encrypt this and put into config file
    from_address = 'noreply@baazdata.com'
    password = 'Xplainio123'
    recipients = ['harshil@cloudera.com', 'romain@cloudera.com', 'nandi@cloudera.com', 'parna@cloudera.com']
    #recipients = ['harshil@cloudera.com']
    if not recipients:
        return
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'NavOpt API Hexad Hourly Test Results'
    msg['From'] = from_address
    msg['To'] = ', '.join(recipients)
    msg.attach(MIMEText(test_results, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(from_address, password)
    server.helo()
    server.sendmail(from_address, recipients, msg.as_string())
    server.quit()
    print "Report Emailed"

if __name__ == '__main__':
    if os.path.isfile("test_results.txt"):
        with open("test_results.txt", 'r') as test_report_file:
            email_report(test_report_file)
        os.remove("test_results.txt")
    else:
       #this means test failed
       email_report(None)
