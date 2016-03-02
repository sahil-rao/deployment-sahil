#!/bin/bash

# buildpath: path to UI tarball build ( xplain.io.tar.gz)
# configpath: path to UI config json

userdata=`curl --silent http://169.254.169.254/latest/user-data`
grep="grep"
regex='s/.*\:[ \t]*"\{0,1\}\([^,"]*\)"\{0,1\},\{0,1\}/\1/'
sed="sed '${regex}'"



# if [ "${userdata}" != "" ]; then
# 	# basic settings
# 	export BUILD_S3PATH=`eval "echo '${userdata}' | ${grep} '\"buildpath\"' | ${sed}"`
# 	export CONFIG_S3PATH=`eval "echo '${userdata}' | ${grep} '\"configpath\"' | ${sed}"`
# fi

export EC2_AVAILABILITY_ZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`
export AWS_DEFAULT_REGION="`echo \"$EC2_AVAILABILITY_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
export EC2_INSTANCE_ID=`curl --silent http://169.254.169.254/latest/meta-data/instance-id`
export BUILD_S3PATH="s3://baaz-deployment/xplain.io.tar.gz"
export CONFIG_S3PATH="s3://baaz-deployment/config.json"

