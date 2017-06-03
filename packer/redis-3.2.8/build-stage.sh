#!/bin/sh

set -e

export AWS_PROFILE=navopt_stage

packer build \
	-var 'env=stage' \
	-var 'encrypted=false' \
	-var 'volume_size=100' \
	-var 'volume_type=standard' \
	-var 'delete_on_termination=true' \
	redis.json
