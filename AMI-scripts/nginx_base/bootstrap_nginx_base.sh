#!/bin/bash

# This script installs the dependencies needed for an Nginx AMI.
# Assumes that we are on a fresh Ubuntu 14.04 AMI 

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Install nginx and dependencies
add-apt-repository -y ppa:nginx/stable
apt-get update
apt-get -y install emacs nginx monit ntp git python-pip python-dev
pip install awscli j2cli
wget -qO /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64; chmod +x /usr/local/bin/jq

# Set up nginx environment
mkdir -p /var/www/
mkdir -m 777 -p /etc/xplain/templates/
mkdir -m 777 -p /etc/xplain/files/

# Pull scripts and templates from github
git clone https://github.com/baazdata/deployment.git
cp ~/deployment/AMI-scripts/nginx/usr/local/bin/* /usr/local/bin/
chmod +x /usr/local/bin/navoptenv.sh /usr/local/bin/reload_nginx.sh /usr/local/bin/setup_nginx.sh 
cp ~/deployment/AMI-scripts/nginx/etc/xplain/templates/* /etc/xplain/templates/
cp ~/deployment/AMI-scripts/nginx/etc/xplain/files/* /etc/xplain/files/

# Clean up after we are done
rm -r ~/deployment/

echo "Nginx Base AMI is all set up!"


