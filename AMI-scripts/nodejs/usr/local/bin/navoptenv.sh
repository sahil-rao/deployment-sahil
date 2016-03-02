#!/bin/bash

# buildpath: path to UI tarball build ( xplain.io.tar.gz)
# configpath: path to UI config json

userdata=`curl --silent http://169.254.169.254/latest/user-data`

if [ "${userdata}" != "" ]; then
	export BUILD_S3PATH=`echo ${userdata} | jq -r '.buildpath'`
	export CONFIG_S3PATH=`echo ${userdata} | jq -r '.configpath'`
fi

export EC2_AVAILABILITY_ZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`
export AWS_DEFAULT_REGION="`echo \"$EC2_AVAILABILITY_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
export EC2_INSTANCE_ID=`curl --silent http://169.254.169.254/latest/meta-data/instance-id`


