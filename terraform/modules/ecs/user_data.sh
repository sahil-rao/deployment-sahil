#!/bin/bash -eux

task_def="dd-agent-task"

cat <<EOF > /etc/ecs/ecs.config
ECS_CLUSTER=${cluster_name}
ECS_AVAILABLE_LOGGING_DRIVERS=["json-file","awslogs"]
EOF

start ecs

yum install -y aws-cli jq

instance_arn=$(curl -s http://localhost:51678/v1/metadata | \
               jq -r '. | .ContainerInstanceArn' | \
               awk -F/ '{print $NF}' )
az=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
region=$${az:0:$${#az} - 1}

cat <<EOF >> /etc/rc.local
cluster=${cluster_name}
az=$az
region=$region
aws ecs start-task \
        --cluster ${cluster_name} \
        --task-definition $task_def \
        --container-instances $instance_arn \
        --region $region
EOF
