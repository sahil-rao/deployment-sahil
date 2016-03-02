# This script sets up the base NodeJS AMI from a existing Bitnami AMI, "bitnami-nodejs-0.10.23-0-linux-ubuntu-12.04.3-x86_64-ebs-2-ami-e8c3fbad-3-ami-47fbee02" (ami-a8b9a1ed)

CONF_DIR=/var/Baaz
TEMPLATE_DIR=/etc/xplain
N_PREFIX=/opt/bitnami/nodejs

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Install dependencies
apt-get update
apt-get -y install emacs python-pip python-dev ntp monit npm
pip install awscli j2cli
wget -qO /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64; chmod +x /usr/local/bin/jq
npm install -g n npm
export N_PREFIX; n stable

# Set up environment
mkdir -m 777 $CONF_DIR
mkdir -m 777 $TEMPLATE_DIR
mkdir -m 777 -p /etc/xplain/config_templates/

# Pull scripts and templates from github
git clone https://github.com/baazdata/deployment.git
cp deployment/nodejs/usr/local/bin/* /usr/local/bin/
cp deployment/nodejs/etc/init/* /etc/init/
cp deployment/nodejs/etc/xplain/config_templates/* /etc/xplain/config_templates/

