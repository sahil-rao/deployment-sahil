#!/bin/bash

source /usr/local/bin/navoptenv.sh
/usr/bin/python /usr/local/bin/do_backup.py $EC2_INSTANCE_ID $CLUSTER $DBSILO

if [ $? -eq 0 ]; then
   echo "`date` MongoDB backup succeeded"
else
    errorinfo="`date` DBSILO: ${DBSILO}, CLUSTER: ${CLUSTER}, INSTANCE: ${EC2_INSTANCE_ID}"
    echo "`date` MongoDB backup failed. Failure info: $errorinfo"
    # Send alert event to datadog
    errorjson="{\"title\": \"MongoDB Backup Failed\", \"text\": \"$errorinfo\", \"priority\": \"normal\", \"alert_type\": \"error\"}"
    curl -XPOST -H "Content-type: application/json" -d "$errorjson" -sS "https://app.datadoghq.com/api/v1/events?api_key=${DATADOG_API_KEY}"
fi
