#!/bin/sh

set -e

export AWS_PROFILE=navopt_dev

packer build \
	-var 'env=dev' \
	-var 'encrypted=false' \
	-var 'volume_size=100' \
	-var 'volume_type=standard' \
	-var 'delete_on_termination=true' \
	elasticsearch.json
