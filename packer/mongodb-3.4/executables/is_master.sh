#!/bin/bash

is_master=`mongo --eval "db.isMaster().ismaster" --quiet`
if [ "$is_master" == "true" ]; then
    echo "yes"
else
    echo "no"
fi
