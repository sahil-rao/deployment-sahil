# This script sets up the base NodeJS AMI from a existing Bitnami AMI, "bitnami-nodejs-0.10.23-0-linux-ubuntu-12.04.3-x86_64-ebs-2-ami-e8c3fbad-3-ami-47fbee02" (ami-a8b9a1ed)

CONF_DIR=/var/Baaz

# Make sure only root can run our script

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

apt-get update
apt-get -y install emacs python-pip ntp monit
pip install awscli
mkdir -m 777 $CONF_DIR
