#!/bin/bash

set -eux

export DEBIAN_FRONTEND=noninteractive

apt update
apt upgrade -y
apt autoremove -y

if [ -f "/var/run/reboot-required" ]; then
	echo "rebooting"
	reboot now
	sleep 60
fi
