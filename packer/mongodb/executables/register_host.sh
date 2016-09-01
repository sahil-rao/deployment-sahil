#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh

is_master=$(/usr/local/bin/is_master.sh)

# If we are the master, we also want to register ourselves as such, and launch our slaves if we have none
if [ "x$is_master" = "xyes" ]; then
    /usr/bin/python /usr/local/bin/register_host.py \
        --region $AWS_DEFAULT_REGION \
        --service $SERVICE \
        --zone $ZONE_NAME \
        --master
fi
