#!/bin/bash

set -ev

# Ubuntu 14.04, r3.2xlarge (hvm)

# AWS EC2 instances sometimes have stale APT caches when starting up... so we wait for AWS to do its magic and refresh them
sleep 10s

# Install basics
apt-get clean; apt-get update
apt-get -y install emacs ntp monit git python-pip python-dev logrotate
pip install awscli boto
wget -qO /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64; chmod +x /usr/local/bin/jq

# Install Redis
apt-get install -y redis-server

# Remove System V redis-server job (we will replace it with an upstart job)
service redis-server stop
update-rc.d -f redis-server remove
rm /etc/init.d/redis-server

# Set up timezone
echo "America/Los_Angeles" | sudo tee /etc/timezone
dpkg-reconfigure --frontend noninteractive tzdata

# Linux configuration for Redis
echo "vm.overcommit_memory = 1" > /etc/sysctl.conf
echo "never" > /sys/kernel/mm/transparent_hugepage/enabled

# Touch log files
touch /var/log/register_host.log; chown redis.redis /var/log/register_host.log
touch /var/log/do_backup.log; chown redis.redis /var/log/do_backup.log

# Move files uploaded by packer file provisioner
cp /tmp/executables/* /usr/local/bin/
mkdir -p /etc/redis/local
cp /tmp/etc/redis/local/redis.conf /tmp/etc/redis/local/sentinel.conf /etc/redis/local/
chown -R redis.redis /etc/redis/local
cp /tmp/etc/init/redis-server.conf /tmp/etc/init/redis-sentinel.conf /etc/init/
cp /tmp/etc/logrotate.d/redis /etc/logrotate.d/redis

# Install Datadog
sudo apt-get install -y apt-transport-https
sudo sh -c "echo 'deb https://apt.datadoghq.com/ stable main' > /etc/apt/sources.list.d/datadog.list"
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys C7A7DA52
sudo apt-get update
sudo apt-get install -y datadog-agent
cp /tmp/etc/dd-agent/conf.d/* /etc/dd-agent/conf.d
update-rc.d datadog-agent defaults
initctl reload-configuration
