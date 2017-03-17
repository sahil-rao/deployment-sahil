#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh
hostname=$(/usr/local/bin/get_master_hostname.sh)
masterip=`getent hosts ${hostname} | awk 'NR==1{print $1}'`
echo "$masterip"
