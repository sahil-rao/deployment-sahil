#!/bin/sh

set -eu

# Wait for user data script to create /etc/navoptenv.json
count=1
while [ ! -f /etc/navoptenv.json ]; do
	if [ $count -gt 300 ]; then
		echo "Out of wait for /etv/navoptenv.json"
		exit 1
	else
		sleep 1
		count=$((count+1))
	fi
done
