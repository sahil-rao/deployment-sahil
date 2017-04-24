#!/bin/bash
# service: What service this machine should be part of
# role: Optional role attribute (cache or data)
# cluster: Which cluster this machine belongs to. (alpha, staging, etc)
# datadog_api_key: API Key for datadog

set -eu

if [ -f /etc/navoptenv.json ]; then
	# basic settings
	export APP=`jq -r '.app' /etc/navoptenv.json`
	export SERVICE=`jq -r '.service' /etc/navoptenv.json`
	export ENV=`jq -r '.env' /etc/navoptenv.json`
	export ZONE_ID=`jq -r '.zone_id' /etc/navoptenv.json`
	export ZONE_NAME=`jq -r '.zone_name' /etc/navoptenv.json`
	export ROLE=`jq -r '.role' /etc/navoptenv.json`
	export DATADOG_API_KEY=`jq -r '.datadog_api_key' /etc/navoptenv.json`
	export REDIS_BACKUP_FILE=`jq -r '.redis_backup_file' /etc/navoptenv.json`
	export REDIS_QUORUM_SIZE=`jq -r '.redis_quorum_size' /etc/navoptenv.json`
	export REDIS_BACKUPS_ENABLED=`jq -r '.redis_backups_enabled' /etc/navoptenv.json`
fi

export EC2_AVAILABILITY_ZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`
export AWS_DEFAULT_REGION="`echo \"$EC2_AVAILABILITY_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
export EC2_INSTANCE_ID=`curl --silent http://169.254.169.254/latest/meta-data/instance-id`
