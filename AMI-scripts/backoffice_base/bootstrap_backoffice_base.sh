# This script sets up the base Backoffice AMI from a Ubuntu 14.04 AMI

CONF_DIR=/var/Baaz
TEMPLATE_DIR=/etc/xplain
MOUNT_POINT=/mnt/volume1

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Install package dependencies
apt-get update
apt-get -y install emacs ntp monit git gcc
apt-get -y install python-pip python-dev python-setuptools
apt-get -y install graphviz libgraphviz-dev pkg-config

# Java JDK 7 installation
add-apt-repository -y ppa:webupd8team/java; apt-get update
echo oracle-java7-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections
apt-get install -y oracle-jdk7-installer
export JAVA_HOME="/usr/lib/jvm/java-7-oracle"
chmod 666 /etc/environment
echo "JAVA_HOME=\"/usr/lib/jvm/java-7-oracle\"" >> /etc/environment

# Install misc CLI tools
pip install awscli j2cli
wget -qO /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64; chmod +x /usr/local/bin/jq

# Set up environment
mkdir -m 777 -p $CONF_DIR
mkdir -m 777 -p $TEMPLATE_DIR
mkdir -m 777 -p $MOUNT_POINT
mkdir -m 777 -p $TEMPLATE_DIR/config_templates/

# Set up timezone
echo "America/Los_Angeles" | sudo tee /etc/timezone
dpkg-reconfigure --frontend noninteractive tzdata

# Pull scripts, templates, files from github
git clone https://github.com/baazdata/deployment.git
cp ~/deployment/AMI-scripts/backoffice/usr/local/bin/* /usr/local/bin/
cp ~/deployment/AMI-scripts/backoffice/etc/init/* /etc/init/
cp ~/deployment/AMI-scripts/backoffice/etc/xplain/config_templates/* /etc/xplain/config_templates/
cp ~/deployment/AMI-scripts/backoffice/etc/xplain/requirements.txt /etc/xplain/requirements.txt
cp ~/deployment/AMI-scripts/backoffice/etc/xplain/monit/* /etc/xplain/monit/

# Install python packages
pip install -r /etc/xplain/requirements.txt

# Clean up after we are done
rm -r ~/deployment/

echo "Backoffice Base AMI is all set up!"
