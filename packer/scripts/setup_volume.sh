#!/bin/bash

set -euv

device=$1
path=$2

if [[ -z "$device" ]]; then
	echo "device argument is required" 1>&2
	exit 1
fi

if [[ -z "$path" ]]; then
	echo "path argument is required" 1>&2
	exit 1
fi

apt-get -y install xfsprogs

# Set up mongo volume
if [ -b $device ]; then
	(echo n; echo p; echo 1; echo ; echo ; echo w;) | fdisk $device
	mkfs.xfs ${device}1
	echo "${device}1      $path xfs noatime,noexec,nodiratime 0 0" >> /etc/fstab
	mkdir -m 000 $path
	mount $path
else
	echo "ebs volume not attached" 1>&2
	exit 1
fi
