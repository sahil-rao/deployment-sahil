#!/bin/bash

repl_state=`redis-cli info | grep -o -P '(?<=role:)(master|slave)'`
if [ "$repl_state" == "master" ]; then
    echo "yes"
else
    echo "no"
fi
