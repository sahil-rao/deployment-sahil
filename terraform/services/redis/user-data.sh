#!/bin/bash

set -eu

/bin/cat <<EOF > /etc/navoptenv.json
{
    "app": "${app}",
    "env": "${env}",
    "service": "${service}",
    "type": "${type}",
    "zone_id": "${zone_id}",
    "zone_name": "${zone_name}",
    "datadog_api_key": "${datadog_api_key}",
    "redis_server_port": "${redis_server_port}",
    "redis_sentinel_port": "${redis_sentinel_port}",
    "redis_master_name": "${redis_master_name}",
    "redis_backup_file": "${redis_backup_file}",
    "redis_quorum_size": ${redis_quorum_size},
    "redis_backups_enabled": "${redis_backups_enabled}"
}
EOF

/bin/cat <<EOF > /etc/dd-agent/datadog.conf
[Main]

dd_url: https://app.datadoghq.com
api_key: ${datadog_api_key}
use_mount: no

tags: app:${app}, env:${env}, service:${service}, type:${type}
EOF
/bin/chown dd-agent /etc/dd-agent/datadog.conf

cat << EOF > /etc/awslogs/awscli.conf
[plugins]
cwlogs = cwlogs
region = ${region}
EOF
/bin/chown root.root /etc/awslogs/awscli.conf

set -x

systemctl enable awslogs.service
systemctl enable datadog-agent.service

systemctl enable navoptenv.path
systemctl enable redis-server.service
systemctl enable redis-sentinel.service
systemctl enable redis-server-join-cluster.service
systemctl enable redis-sentinel-join-cluster.service
systemctl enable redis-backup.service
systemctl enable redis-backup.timer
systemctl enable redis-register-master-hostname.service
systemctl enable redis-register-master-hostname.timer

systemctl daemon-reload

systemctl restart awslogs.service
systemctl restart datadog-agent.service
systemctl restart redis-server.service
systemctl restart redis-sentinel.service
systemctl restart redis-server-join-cluster.service
systemctl restart redis-sentinel-join-cluster.service
systemctl restart redis-backup.timer
systemctl restart redis-register-master-hostname.timer

sleep 10

systemctl status awslogs.service
systemctl status datadog-agent.service
systemctl status redis-server.service
systemctl status redis-sentinel.service
systemctl status redis-server-join-cluster.service
systemctl status redis-sentinel-join-cluster.service
systemctl status redis-backup.timer
systemctl status redis-register-master-hostname.timer
