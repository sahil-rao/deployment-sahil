#!/bin/bash

# buildpaths: path to build tarball in S3
# configpath: path to a config json in S3

userdata=`curl --silent http://169.254.169.254/latest/user-data`

if [ "${userdata}" != "" ]; then
    export FLIGHTPATH_BUILD_S3PATH=`echo ${userdata} | jq -r '.flightpath_buildpath'`
    export DATA_ACQUISITION_BUILD_S3PATH=`echo ${userdata} | jq -r '.data_acquisition_buildpath'`
    export ANALYTICS_BUILD_S3PATH=`echo ${userdata} | jq -r '.analytics_buildpath'`
    export ANALYTICS_SERVICE_BUILD_S3PATH=`echo ${userdata} | jq -r '.analytics_service_buildpath'`
    export COMPILER_BUILD_S3PATH=`echo ${userdata} | jq -r '.compiler_buildpath'`
    export COMPILE_SERVICE_BUILD_S3PATH=`echo ${userdata} | jq -r '.compile_service_buildpath'`
    export CONFIG_S3PATH=`echo ${userdata} | jq -r '.configpath'`
fi

export EC2_AVAILABILITY_ZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`
export AWS_DEFAULT_REGION="`echo \"$EC2_AVAILABILITY_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
export EC2_INSTANCE_ID=`curl --silent http://169.254.169.254/latest/meta-data/instance-id`


