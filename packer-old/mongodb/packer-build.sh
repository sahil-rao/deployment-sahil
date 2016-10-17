#!/bin/sh

set -e

export AWS_PROFILE=navopt_prod
packer build mongodb.json
