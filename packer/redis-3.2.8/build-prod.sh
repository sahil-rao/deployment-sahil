#!/bin/sh

set -e

export AWS_PROFILE=navopt_prod

packer build \
	-var 'env=prod' \
	-var 'encrypted=true' \
	-var 'volume_size=100' \
	-var 'volume_type=io1' \
	-var 'iops=1000' \
	-var 'delete_on_termination=false' \
	redis.json
