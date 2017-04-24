#!/bin/bash

set -euv

add-apt-repository ppa:chris-lea/redis-server
apt-get update

apt install -y \
	awscli \
	python \
	python-dev \
	python-pip \
	redis-sentinel \
	redis-server \
	virtualenv

##############################################################################

# Linux configuration for Redis
echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf
sysctl -w vm.overcommit_memory=1
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
sysctl -w net.core.somaxconn=1024

echo "never" > /sys/kernel/mm/transparent_hugepage/enabled

install -o redis -g root -m 755 \
	/tmp/executables/register_host.py \
	/usr/local/bin/register-host

install -o redis -g root -m 755 \
	/tmp/executables/navoptenv.sh \
	/tmp/executables/redis-register-master-hostname \
	/tmp/executables/redis-sentinel-client-reconfig \
	/tmp/executables/redis-server-backup \
	/usr/local/bin/

install -o redis -g redis -m 640 /tmp/etc/redis/redis.conf /etc/redis/redis.conf
install -o redis -g redis -m 640 /tmp/etc/redis/sentinel.conf /etc/redis/sentinel.conf

install -o redis -g redis -m 755 /tmp/executables/redis-server-pre-up /etc/redis/redis-server.pre-up.d/
install -o redis -g redis -m 755 /tmp/executables/redis-server-post-up /etc/redis/redis-server.post-up.d/
install -o redis -g redis -m 755 /tmp/executables/redis-server-pre-down /etc/redis/redis-server.pre-down.d/

install -o redis -g redis -m 755 /tmp/executables/redis-sentinel-post-up /etc/redis/redis-sentinel.post-up.d/

##############################################################################

virtualenv /usr/local/share/redis-mgmt
/usr/local/share/redis-mgmt/bin/pip install -r /tmp/redis-mgmt/requirements.txt
/usr/local/share/redis-mgmt/bin/pip install /tmp/redis-mgmt/

install -o redis -g redis -m 644 /tmp/etc/systemd/redis-backup.service /etc/systemd/system/redis-backup.service
install -o redis -g redis -m 644 /tmp/etc/systemd/redis-backup.timer /etc/systemd/system/redis-backup.timer

install -o root -g root -m 644 /tmp/etc/systemd/redis-register-master-hostname.service /etc/systemd/system/redis-register-master-hostname.service
install -o root -g root -m 644 /tmp/etc/systemd/redis-register-master-hostname.timer /etc/systemd/system/redis-register-master-hostname.timer
