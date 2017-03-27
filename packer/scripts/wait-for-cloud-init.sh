#!/bin/bash

set -euv

while [ ! -f /var/lib/cloud/instance/boot-finished ]; do
	echo 'Waiting for cloud-init...'
	sleep 1
done
