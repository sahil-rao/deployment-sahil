#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh
exec /usr/local/bin/register_redis_sentinel.py \
    --region $AWS_DEFAULT_REGION \
    --dbsilo $DBSILO \
    --zone $ZONE_NAME
