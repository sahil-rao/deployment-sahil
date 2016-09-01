#!/bin/bash

set -euv

/bin/cat <<EOF > /etc/navoptenv.json
{
    "app": "${app}",
    "env": "${env}",
    "service": "${service}",
    "type": "${type}",
    "zone_name": "${zone_name}",
    "datadog_api_key": "${datadog_api_key}",
    "source": "${snapshot_id}"
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
/usr/sbin/service datadog-agent restart
