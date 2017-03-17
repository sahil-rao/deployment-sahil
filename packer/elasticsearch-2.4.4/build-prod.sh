#!/bin/sh

set -e

export AWS_PROFILE=navopt_prod

packer build \
	-var 'env=prod' \
	-var 'encrypted=true' \
	-var 'volume_size=100' \
	-var 'volume_type=gp2' \
	-var 'delete_on_termination=false' \
	elasticsearch.json
