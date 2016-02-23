#!/bin/bash

source /usr/local/bin/navoptenv.sh
/usr/bin/python /usr/local/bin/do_backup.py $EC2_INSTANCE_ID
