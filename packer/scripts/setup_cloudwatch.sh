#!/bin/bash

set -euv

# Install awslogs
sudo apt-get update
sudo apt-get -y install python-pip
cp /tmp/etc/cloudwatch/* /home/ubuntu
sudo python /home/ubuntu/awslogs-agent-setup.py --region us-west-2 -c /home/ubuntu/awslogs.conf -n
sudo service awslogs stop
sudo service awslogs start
