#!/bin/bash

set -eux

sudo apt-get install -y \
	python-urllib3 \
	python-openssl \
	python-pyasn1 \
	apt-transport-https \
	awscli

curl -sSL https://repo.saltstack.com/apt/ubuntu/14.04/amd64/latest/SALTSTACK-GPG-KEY.pub | sudo apt-key add -
echo "deb http://repo.saltstack.com/apt/ubuntu/14.04/amd64/latest trusty main" | sudo tee -a /etc/apt/sources.list.d/salt.list

sudo apt-get update && apt-get -y install salt-minion

sudo mkdir -p /srv/salt
sudo chmod 0755 /srv/salt

cp /tmp/etc/cron.d/salt-pull-config-apply /etc/cron.d/
