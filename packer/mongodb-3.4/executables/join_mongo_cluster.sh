#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh
exec /usr/local/bin/join_mongo_cluster.py \
	--region $AWS_DEFAULT_REGION \
	--service $SERVICE \
	--replica-set $REPLICA_SET
