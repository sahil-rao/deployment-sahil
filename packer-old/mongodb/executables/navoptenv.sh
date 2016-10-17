#!/bin/bash
# service: mongodb 
# dbsilo : DBSilo name. This will also be the replicaset name.
# source: Which volume or snapshot-id the machine should boot up with 
# cluster: Which cluster this machine belongs to.
# datadog_api_key: API Key for datadog

userdata=`cat /etc/navoptenv.json`

if [ "${userdata}" != "" ]; then
	# basic settings
	export SERVICE=`echo ${userdata} | /usr/local/bin/jq -r '.service'`
	export DBSILO=`echo ${userdata} | /usr/local/bin/jq -r '.dbsilo'`
	export CLUSTER=`echo ${userdata} | /usr/local/bin/jq -r '.cluster'`
	export SET_SRC=`echo ${userdata} | /usr/local/bin/jq -r '.source'`
	export DATADOG_API_KEY=`echo ${userdata} | /usr/local/bin/jq -r '.datadog_api_key'`
fi

export EC2_AVAILABILITY_ZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`
export AWS_DEFAULT_REGION="`echo \"$EC2_AVAILABILITY_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
export EC2_INSTANCE_ID=`curl --silent http://169.254.169.254/latest/meta-data/instance-id`
export SET_SIZE=256
