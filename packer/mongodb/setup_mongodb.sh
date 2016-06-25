#!/bin/bash

set -ev

# Ubuntu 14.04, m4.xlarge (hvm)

# AWS EC2 instances sometimes have stale APT caches when starting up... so we wait for AWS to do its magic and refresh them
sleep 10s

# Install basics
apt-get clean; apt-get update
apt-get -y install emacs ntp monit git python-pip python-dev logrotate
pip install awscli pymongo boto 
wget -qO /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64; chmod +x /usr/local/bin/jq

# Install MongoDB 3.0.12; Pin packages
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list
apt-get update
apt-get install -y mongodb-org=3.0.12 mongodb-org-server=3.0.12 mongodb-org-shell=3.0.12 mongodb-org-mongos=3.0.12 mongodb-org-tools=3.0.12
echo "mongodb-org hold" | sudo dpkg --set-selections
echo "mongodb-org-server hold" | sudo dpkg --set-selections
echo "mongodb-org-shell hold" | sudo dpkg --set-selections
echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
echo "mongodb-org-tools hold" | sudo dpkg --set-selections

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

# Install Datadog
sudo apt-get install -y apt-transport-https
sudo sh -c "echo 'deb https://apt.datadoghq.com/ stable main' > /etc/apt/sources.list.d/datadog.list"
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys C7A7DA52
sudo apt-get update
sudo apt-get install -y datadog-agent
cp /tmp/etc/dd-agent/conf.d/* /etc/dd-agent/conf.d
update-rc.d datadog-agent defaults
initctl reload-configuration
