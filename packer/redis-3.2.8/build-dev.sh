#!/bin/sh

set -e

export AWS_PROFILE=navopt_dev

packer build \
	--on-error=ask \
	-var 'env=dev' \
	-var 'encrypted=false' \
	-var 'volume_size=60' \
	-var 'volume_type=standard' \
	-var 'delete_on_termination=true' \
	redis.json
