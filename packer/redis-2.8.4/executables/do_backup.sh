#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh

if [ "$REDIS_BACKUPS_ENABLED" != "true" ]; then
	echo "backups not enabled"
	exit
fi

datestr=`date -uIseconds`
bucket="navopt-backups-${ENV}"
prefix="redis-backups/${SERVICE}"
s3path="s3://${bucket}/${prefix}/dump-${datestr}.rdb"

# Copy redis dump file (.rdb) to s3
/usr/local/bin/aws s3 cp /var/lib/redis/dump.rdb $s3path

if [ $? -eq 0 ]; then
   echo "`date` Redis backup succeeded"
else
    errorinfo="`date` service: ${SERVICE}, env: ${ENV}, INSTANCE: ${EC2_INSTANCE_ID}"
    echo "`date` Redis backup failed. Failure info: $errorinfo"
    # Send alert event to datadog
    curl -XPOST -H "Content-type: application/json" -d@- -sS "https://app.datadoghq.com/api/v1/events?api_key=${DATADOG_API_KEY}" <<EOF
{
	"title": "[$APP] [$ENV] $SERVICE backup failed",
	"text": "$errorinfo",
	"priority": "normal",
	"alert_type": "error",
	"tags": ["app:$APP", "env:$ENV", "service:$SERVICE"]
}
EOF
fi
