#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh
exec /usr/local/bin/join_redis_cluster.py \
	  --region $AWS_DEFAULT_REGION \
    --dbsilo $DBSILO
