#!/bin/bash

source /usr/local/bin/navoptenv.sh

is_master=$(/usr/local/bin/is_master.sh)
/usr/bin/python /usr/local/bin/register_host.py $CLUSTER $DBSILO $SERVICE

# If we are the master, we also want to register ourselves as such, and launch our slaves if we have none
if [ "x$is_master" = "xyes" ]; then
    /usr/bin/python /usr/local/bin/register_host.py $CLUSTER $DBSILO $SERVICE "master"
    /usr/bin/python /usr/local/bin/launch_slaves.py
fi

   
