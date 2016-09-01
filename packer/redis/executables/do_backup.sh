#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh

datestr=`date -uIseconds`
bucket="xplain-${CLUSTER}"
prefix="${DBSILO}/redis-backups"
s3path="s3://${bucket}/${prefix}/dump${datestr}.rdb"

# Copy redis dump file (.rdb) to s3
/usr/local/bin/aws s3 cp /var/lib/redis/dump.rdb $s3path

if [ $? -eq 0 ]; then
   echo "`date` Redis backup succeeded"
else
    errorinfo="`date` DBSILO: ${DBSILO}, CLUSTER: ${CLUSTER}, INSTANCE: ${EC2_INSTANCE_ID}"
    echo "`date` Redis backup failed. Failure info: $errorinfo"
    # Send alert event to datadog
    curl -XPOST -H "Content-type: application/json" -d@- -sS "https://app.datadoghq.com/api/v1/events?api_key=${DATADOG_API_KEY}" <<EOF
{
	"title": "[NavOpt] [$CLUSTER] $DBSILO Redis Backup Failed",
	"text": "$errorinfo",
	"priority": "normal",
	"alert_type": "error",
	"tags": ["account:navopt", "dbsilo:$DBSILO", "cluster:$CLUSTER", "service:redis"]
}
EOF
fi

# Ensure that all files with the prefix will expire in 14 days
expire_policy_json='{"Rules":[{"Status":"Enabled","Prefix":'"\"${prefix}"\"',"Expiration":{"Days":14}}]}'
/usr/local/bin/aws s3api put-bucket-lifecycle --bucket $bucket --lifecycle-configuration $expire_policy_json
