#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh
hostname="${SERVICE}-master.${ZONE_NAME}"
echo "$hostname"
