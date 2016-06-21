#!/bin/sh
export AWS_PROFILE=navopt_prod
packer build redis.json
