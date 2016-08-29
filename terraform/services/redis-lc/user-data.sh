#!/bin/bash

set -euv

/bin/cat <<EOF > /etc/navoptenv.json
{
    "application": "${application}",
    "env": "${env}",
    "service": "${service}",
    "zone_name": "${zone_name}",
    "datadog_api_key": "${datadog_api_key}",
    "backup_file": "${backup_file}",
    "redis_quorum_size": "${redis_quorum_size}"
}
EOF

/bin/cat <<EOF > /etc/dd-agent/datadog.conf
[Main]

dd_url: https://app.datadoghq.com
api_key: ${datadog_api_key}
use_mount: no

tags: app:${application}, env:${env}, service:${service}
EOF

/bin/chown dd-agent /etc/dd-agent/datadog.conf
/usr/sbin/service datadog-agent start
/usr/sbin/service redis-server restart
