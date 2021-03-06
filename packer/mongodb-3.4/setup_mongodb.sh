#!/bin/bash

set -euv

# Install MongoDB 3.4.2; Pin packages
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list
apt-get update
apt-get install -y mongodb-org=3.4.2 mongodb-org-server=3.4.2 mongodb-org-shell=3.4.2 mongodb-org-mongos=3.4.2 mongodb-org-tools=3.4.2
echo "mongodb-org hold" | sudo dpkg --set-selections
echo "mongodb-org-server hold" | sudo dpkg --set-selections
echo "mongodb-org-shell hold" | sudo dpkg --set-selections
echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
echo "mongodb-org-tools hold" | sudo dpkg --set-selections

# Setup the basics
pip install pymongo
wget -qO /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64; chmod +x /usr/local/bin/jq

# Move files uploaded by packer file provisioner
cp /tmp/executables/* /usr/local/bin/
cp /tmp/etc/mongod.conf /etc/mongod.conf
cp /tmp/etc/init/mongod.conf /etc/init/mongod.conf
cp /tmp/etc/logrotate.d/mongodb /etc/logrotate.d/mongodb
cp /tmp/etc/cron.d/mongodb /etc/cron.d/mongodb
