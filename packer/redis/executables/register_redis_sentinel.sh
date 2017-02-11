#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh
exec /usr/local/bin/register_redis_sentinel.py \
	--region $AWS_DEFAULT_REGION \
	--service $SERVICE \
	--zone-name $ZONE_NAME \
	--quorum-size $REDIS_QUORUM_SIZE
