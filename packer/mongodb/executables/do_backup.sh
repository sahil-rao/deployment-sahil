#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh

/usr/bin/python /usr/local/bin/do_backup.py \
	--region $AWS_DEFAULT_REGION \
	--env $ENV \
	--service $SERVICE \
	--instance-id $EC2_INSTANCE_ID
