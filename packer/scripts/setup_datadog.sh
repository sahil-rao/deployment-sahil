#!/bin/bash

set -euv

# Install Datadog
sudo apt-get install -y apt-transport-https
sudo sh -c "echo 'deb https://apt.datadoghq.com/ stable main' > /etc/apt/sources.list.d/datadog.list"
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys C7A7DA52
sudo apt-get update
sudo apt-get install -y datadog-agent
cp /tmp/etc/dd-agent/conf.d/* /etc/dd-agent/conf.d/
update-rc.d datadog-agent defaults
initctl reload-configuration
