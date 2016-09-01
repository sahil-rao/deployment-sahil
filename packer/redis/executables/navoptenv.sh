#!/bin/bash
# service: redis
# dbsilo : DBSilo machine should be part of
# role: Optional role attribute (cache or data)
# cluster: Which cluster this machine belongs to. (alpha, staging, etc)
# datadog_api_key: API Key for datadog

set -eu

userdata=`cat /etc/navoptenv.json`

if [ "${userdata}" != "" ]; then
	# basic settings
	export SERVICE=`echo ${userdata} | /usr/local/bin/jq -r '.service'`
	export DBSILO=`echo ${userdata} | /usr/local/bin/jq -r '.dbsilo'`
	export CLUSTER=`echo ${userdata} | /usr/local/bin/jq -r '.cluster'`
	export ZONE_NAME=`echo ${userdata} | /usr/local/bin/jq -r '.zone_name'`
	export REDIS_QUORUM_SIZE=`echo ${userdata} | /usr/local/bin/jq -r '.redis_quorum_size'`
	export ROLE=`echo ${userdata} | /usr/local/bin/jq -r '.role'`
	export DATADOG_API_KEY=`echo ${userdata} | /usr/local/bin/jq -r '.datadog_api_key'`
	export BACKUP_FILE=`echo ${userdata} | /usr/local/bin/jq -r '.backup_file'`
fi

export EC2_AVAILABILITY_ZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`
export AWS_DEFAULT_REGION="`echo \"$EC2_AVAILABILITY_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
export EC2_INSTANCE_ID=`curl --silent http://169.254.169.254/latest/meta-data/instance-id`
