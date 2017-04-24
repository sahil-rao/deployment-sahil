#!/bin/bash

set -euv

# Install cloudwatch logs into it's own virtualenv to isolate it from the rest
# of the system.
apt install -y \
	jq \
	python \
	python-dev \
	python-pip \
	virtualenv

virtualenv /usr/local/share/awslogs
/usr/local/share/awslogs/bin/pip install awscli awscli-cwlogs

install -o root -g root -m 755 -d /var/lib/awslogs /etc/awslogs /etc/awslogs/config

##############################################################################

cat << EOF > /etc/awslogs/awslogs.conf
[general]
state_file = /var/awslogs/state/agent-state
EOF

##############################################################################

cat << EOF > /etc/awslogs/config/auth.conf
[/var/log/auth.log]
datetime_format = %b %d %H:%M:%S
multi_line_start_pattern = %b %d %H:%M:%S
file = /var/log/auth.log
buffer_duration = 5000
log_stream_name = {instance_id}
initial_position = start_of_file
log_group_name = /var/log/auth.log
EOF

cat << EOF > /etc/awslogs/config/syslog.conf
[/var/log/syslog]
datetime_format = %b %d %H:%M:%S
multi_line_start_pattern = %b %d %H:%M:%S
file = /var/log/syslog
buffer_duration = 5000
log_stream_name = {instance_id}
initial_position = start_of_file
log_group_name = /var/log/syslog
EOF

##############################################################################

cat << EOF > /lib/systemd/system/awslogs.service
[Unit]
Description=AWS CloudWatch Log Collector
Wants=cloud-final.service
After=cloud-final.service

[Service]
ExecStart=/usr/local/share/awslogs/bin/aws logs push --config-file /etc/awslogs/awslogs.conf --additional-configs-dir /etc/awslogs/config
Restart=always
WorkingDirectory=/var/lib/awslogs
User=root
PrivateTmp=true
PrivateDevices=true
ProtectSystem=full
ProtectHome=true
Environment=AWS_CONFIG_FILE=/etc/awslogs/awscli.conf
Nice=4

[Install]
WantedBy=multi-user.target
EOF
