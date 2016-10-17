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

pip install \
	awscli \
	boto \
	boto3 \
	datadog \
	requests
