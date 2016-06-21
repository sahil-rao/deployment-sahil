#!/bin/bash

# Ubuntu 14.04, m4.xlarge (hvm)

# AWS EC2 instances sometimes have stale APT caches when starting up... so we wait for AWS to do its magic and refresh them
sleep 10s

# Install basics
apt-get clean; apt-get update
apt-get -y install emacs ntp monit git python-pip python-dev
pip install awscli pymongo boto 
wget -qO /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64; chmod +x /usr/local/bin/jq

# Install MongoDB 
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list
apt-get update 
apt-get install -y mongodb-org

# Set up timezone
echo "America/Los_Angeles" | sudo tee /etc/timezone
dpkg-reconfigure --frontend noninteractive tzdata

# Set up environment
mkdir /mnt/volume1
echo -n 'never' > /sys/kernel/mm/transparent_hugepage/enabled
echo -n 'never' > /sys/kernel/mm/transparent_hugepage/defrag

# Move files uploaded by packer file provisioner
cp /tmp/executables/* /usr/local/bin/
cp /tmp/etc/mongod.conf /etc/mongod.conf
cp /tmp/etc/init/mongod.conf /etc/init/mongod.conf
cp /tmp/etc/logrotate.d/mongodb /etc/logrotate.d/mongodb


