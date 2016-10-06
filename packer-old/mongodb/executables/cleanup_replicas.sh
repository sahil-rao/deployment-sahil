#!/bin/bash

source /usr/local/bin/navoptenv.sh
/usr/bin/python /usr/local/bin/cleanup_replicas.py $CLUSTER $DBSILO $SERVICE
result=$?
date="`date`"

if [ $result -eq 0 ]; then
    echo "${date} Replica set health check passed"
# Exit code of 3 means that a replica set member has been removed
elif [ $result -eq 3 ]; then
    echo "${date} Replica set health check failed"
    echo "${date} Removed an unhealthy replica set member"
    errorinfo="${date} DBSILO: ${DBSILO}, CLUSTER: ${CLUSTER}, REPORTING INSTANCE: ${EC2_INSTANCE_ID}"
    # Send alert event to datadog
    errorjson="{\"title\": \"MongoDB Unhealthy Replica Set Member Removed\", \"text\": \"$errorinfo\", \"priority\": \"normal\", \"alert_type\": \"error\"}"
    curl -XPOST -H "Content-type: application/json" -d "$errorjson" -sS "https://app.datadoghq.com/api/v1/events?api_key=${DATADOG_API_KEY}"
elif [ $result -eq 4 ]; then
    echo "${date} Replica set health check failed"
    errorinfo="${date} DBSILO: ${DBSILO}, CLUSTER: ${CLUSTER}, REPORTING INSTANCE: ${EC2_INSTANCE_ID}"
    # Send alert event to datadog
    errorjson="{\"title\": \"MongoDB Unhealthy Replica Set Member Detected\", \"text\": \"$errorinfo\", \"priority\": \"normal\", \"alert_type\": \"error\"}"
    curl -XPOST -H "Content-type: application/json" -d "$errorjson" -sS "https://app.datadoghq.com/api/v1/events?api_key=${DATADOG_API_KEY}"
else
    echo "${date} Error with replica set health check"
fi
