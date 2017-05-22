#!/bin/bash

set -euv

# Ubuntu 14.04, m4.xlarge (hvm)

# AWS EC2 instances sometimes have stale APT caches when starting up... so we
# wait for AWS to do its magic and refresh them
sleep 10s
apt-get clean; apt-get update

apt-get -y install \
	emacs \
	git \
	logrotate \
	monit \
	ntp \
	python \
	python-dev \
	python-pip \
	vim

pip install --upgrade pip
pip install awscli-cwlogs==1.4.0
pip install awscli==1.9.8
pip install boto==2.45.0
pip install boto3==1.4.4
pip install datadog==0.15.0
pip install requests==2.2.1
