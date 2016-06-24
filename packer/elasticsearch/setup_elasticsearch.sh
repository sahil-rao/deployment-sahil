#!/bin/bash

set -ev

# Ubuntu 14.04, m3.xlarge (hvm)

# AWS EC2 instances sometimes have stale APT caches when starting up... so we wait for AWS to do its magic and refresh them
sleep 10s

# Install basics
apt-get clean; apt-get update
apt-get -y install emacs ntp monit git python-pip python-dev logrotate
pip install awscli boto j2cli 
wget -qO /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64; chmod +x /usr/local/bin/jq

# Oracle Java 8 installation
add-apt-repository -y ppa:webupd8team/java; apt-get update
echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections
apt-get install -y oracle-java8-installer
apt-get install -y oracle-java8-set-default

# Install elasticsearch
wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://packages.elastic.co/elasticsearch/2.x/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list
apt-get update && apt-get -y install elasticsearch

# Install elasticsearch AWS plugin
/usr/share/elasticsearch/bin/plugin install cloud-aws --batch

# Install elasticsearch curator to manage backups (snapshots)
pip install elasticsearch-curator==3.4.1

# Set timezone as PST
echo "America/Los_Angeles" | sudo tee /etc/timezone
dpkg-reconfigure --frontend noninteractive tzdata

# Touch log files
touch /var/log/register_host.log; chown elasticsearch.root /var/log/register_host.log
touch /var/log/take_snapshot.log; chown elasticsearch.root /var/log/take_snapshot.log

# Move files uploaded by packer file provisioner
cp /tmp/executables/* /usr/local/bin/
cp /tmp/etc/init.d/elasticsearch /etc/init.d/
cp /tmp/etc/logrotate.d/elasticsearch /etc/logrotate.d/elasticsearch
cp /tmp/templates/elasticsearch.j2 /usr/share/elasticsearch/

# Elasticsearch service to start on boot
update-rc.d elasticsearch defaults 95 10

# Set up crontabs for Route53 registration and backups
(crontab -l || true; echo "* * * * * /bin/bash /usr/local/bin/register_host.sh >>/var/log/register_host.log 2>&1") 2>&1 | grep -v "no crontab" | sort | uniq | crontab -
(crontab -l || true; echo "*/30 * * * * /bin/bash /usr/local/bin/take_snapshot.sh >>/var/log/take_snapshot.log 2>&1") 2>&1 | grep -v "no crontab" | sort | uniq | crontab -

# Install Datadog
apt-get install -y apt-transport-https
sh -c "echo 'deb https://apt.datadoghq.com/ stable main' > /etc/apt/sources.list.d/datadog.list"
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys C7A7DA52
apt-get update
apt-get install -y datadog-agent
cp /tmp/etc/dd-agent/conf.d/* /etc/dd-agent/conf.d
update-rc.d datadog-agent defaults
initctl reload-configuration
