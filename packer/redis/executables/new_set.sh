#!/bin/bash

source /usr/local/bin/navoptenv.sh

PORT=6379
TIMEOUT=5

hostname=$(/usr/local/bin/get_master_hostname.sh)
masterip=`getent hosts ${hostname} | awk 'NR==1{print $1}'`

if [ ! -z "$masterip" ]; then
    nc -w $TIMEOUT -z $masterip $PORT
    if [ $? -eq 0 ]; then
	repl_state=`redis-cli -h $masterip -p $PORT info | grep -o -P '(?<=role:)(master|slave)'`
	if [ "$repl_state" == "master" ]; then
	    echo "no"
	else
	    echo "yes"
	fi
    else
	echo "yes"
    fi
else
    echo "yes"
fi

