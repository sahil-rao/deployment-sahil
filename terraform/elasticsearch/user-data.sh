#!/bin/bash

set -ev

/bin/cat <<EOF > /etc/navoptenv.json
{
    "dbsilo": "${dbsilo}",
    "service": "${service}",
    "cluster": "${cluster}",
    "datadog_api_key": "${datadog_api_key}",
    "sg_name": "${sg_name}"
}
EOF

/bin/cat <<EOF > /etc/dd-agent/datadog.conf
[Main]

dd_url: https://app.datadoghq.com
api_key: ${datadog_api_key}
use_mount: no

tags: navopt, ${cluster}, dbsilo, redis
EOF
/bin/chown dd-agent /etc/dd-agent/datadog.conf
/usr/sbin/service datadog-agent start

# Create elasticsearch volume
mkfs -t ext3 /dev/xvdf
/bin/mount -t ext3 /dev/xvdf /mnt

service elasticsearch start
