#!/bin/bash

# LIST OF POSSIBLE PARAMS FROM USERDATA JSON
# ------------------------------------------
# autoscale_group_name: Autoscaling group of NodeJS servers that will be the upstreams for this nginx
# old_domain: Domain to redirect to new domain (eg xplain.io domains)
# domain: Name of domain that this instance will be attached to (eg optimizer.cloudera.com)
# ssl: "enabled" or "disabled"
# port: port that NodeJS servers will listen on. In the future, we can make this an array (eg each machine has multiple nodejs instances listening on multiple ports)

userdata=`curl --silent http://169.254.169.254/latest/user-data`

if [ "${userdata}" != "" ]; then
    export AUTOSCALE_GROUP=`echo ${userdata} | jq -r '.autoscale_group_name'`
    export OLD_DOMAIN=`echo ${userdata} | jq -r '.old_domain'`
    export DOMAIN=`echo ${userdata} | jq -r '.domain'`
    export SSL_MODE=`echo ${userdata} | jq -r '.ssl'`
    export NODEJS_PORT=`echo ${userdata} | jq -r '.port'`
fi

export EC2_AVAILABILITY_ZONE=`curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone`
export AWS_DEFAULT_REGION="`echo \"$EC2_AVAILABILITY_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
export EC2_INSTANCE_ID=`curl --silent http://169.254.169.254/latest/meta-data/instance-id`

NODEJS_INSTANCE_IDS=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name $AUTOSCALE_GROUP --query AutoScalingGroups[].Instances[].InstanceId --output text)
# String of tab-separated IP addresses
export NODEJS_IP_ADDRESSES=$(aws ec2 describe-instances --instance-ids $INSTANCE_IDS --query Reservations[].Instances[].PrivateIpAddress --output text) 


