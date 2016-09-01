#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh
hostname="${SERVICE}master.${DBSILO}.${CLUSTER}.${ZONE_NAME}"
echo "$hostname"
