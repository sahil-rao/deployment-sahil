#!/bin/bash

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

. /usr/local/bin/navoptenv.sh

# If this file exists, we have successfully loaded from a s3 backup on startup
BACKUP_LOADED_COOKIE="/var/lib/redis/backup-loaded-cookie"

# If a backup file is provided in the userdata json  on startup, load from the backup
if [ "x$REDIS_BACKUP_FILE" != "xnull" ] && [ "x$REDIS_BACKUP_FILE" != "x" ] && [ ! -f "$BACKUP_LOADED_COOKIE" ]; then
		/usr/local/bin/aws s3 cp $REDIS_BACKUP_FILE /var/lib/redis/dump.rdb
		# We don't want to load the same backup file on subsequent restarts
		touch $BACKUP_LOADED_COOKIE
		chmod 400 $BACKUP_LOADED_COOKIE
fi
