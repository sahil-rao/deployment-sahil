#!/bin/bash

set -euv

# Install basics
pip install j2cli
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

# Make the elasticsearch volume owned by the elasticsearch user
chown elasticsearch.elasticsearch /var/lib/elasticsearch

# Install elasticsearch AWS plugin
/usr/share/elasticsearch/bin/plugin install cloud-aws --batch

# Install elasticsearch curator to manage backups (snapshots)
pip install elasticsearch-curator==3.4.1

# Touch log files
touch /var/log/register_host.log; chown elasticsearch.root /var/log/register_host.log
touch /var/log/take_snapshot.log; chown elasticsearch.root /var/log/take_snapshot.log

# Move files uploaded by packer file provisioner
cp /tmp/executables/* /usr/local/bin/
cp /tmp/etc/init.d/elasticsearch /etc/init.d/
cp /tmp/etc/logrotate.d/elasticsearch /etc/logrotate.d/elasticsearch
cp /tmp/templates/elasticsearch.j2 /usr/share/elasticsearch/
cp /tmp/etc/cron.d/elasticsearch /etc/cron.d/elasticsearch

# Elasticsearch service to start on boot
update-rc.d elasticsearch defaults 95 10
