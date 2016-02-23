#!/bin/bash
# service: mongodb 
# DBSilo : DBSilo name. This will also be the replicaset name.
# source: Which volume or snapshot-id the machine should boot up with 
# cluster: Which cluster this machine belongs to.

userdata=`curl --silent http://169.254.169.254/latest/user-data`
grep="grep"
regex='s/.*\:[ \t]*"\{0,1\}\([^,"]*\)"\{0,1\},\{0,1\}/\1/'
sed="sed '${regex}'"

if [ "${userdata}" != "" ]; then
	# basic settings
	export SERVICE=`eval "echo '${userdata}' | ${grep} '\"service\"' | ${sed}"`
	export DBSILO=`eval "echo '${userdata}' | ${grep} '\"DBSilo\"' | ${sed}"`
	export CLUSTER=`eval "echo '${userdata}' | ${grep} '\"cluster\"' | ${sed}"`
	export SET_SRC=`eval "echo '${userdata}' | ${grep} '\"source\"' | ${sed}"`
fi

export EC2_AVAILABILITY_ZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`
export AWS_DEFAULT_REGION=${EC2_AVAILABILITY_ZONE:0:${#EC2_AVAILABILITY_ZONE}-1}
export EC2_INSTANCE_ID=`curl --silent http://169.254.169.254/latest/meta-data/instance-id`
export SET_SIZE=256
