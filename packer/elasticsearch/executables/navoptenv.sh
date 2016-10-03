#!/bin/bash
# service: Service machine should be part of
# cluster: Which cluster this machine belongs to. (alpha, staging, etc)
# datadog_api_key: API Key for datadog

set -eu

if [ -f /etc/navoptenv.json ]; then
	# basic settings
	export APP=`/usr/local/bin/jq -r '.app' /etc/navoptenv.json`
	export SERVICE=`/usr/local/bin/jq -r '.service' /etc/navoptenv.json`
	export ENV=`/usr/local/bin/jq -r '.env' /etc/navoptenv.json`
	export ZONE_NAME=`/usr/local/bin/jq -r '.zone_name' /etc/navoptenv.json`
	export DATADOG_API_KEY=`/usr/local/bin/jq -r '.datadog_api_key' /etc/navoptenv.json`
	export SECURITY_GROUP_NAME=`/usr/local/bin/jq -r '.sg_name' /etc/navoptenv.json`
fi

export EC2_AVAILABILITY_ZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`
export AWS_DEFAULT_REGION="`echo \"$EC2_AVAILABILITY_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
export EC2_INSTANCE_ID=`curl --silent http://169.254.169.254/latest/meta-data/instance-id`
