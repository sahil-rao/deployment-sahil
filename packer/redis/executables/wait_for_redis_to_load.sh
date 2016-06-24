#!/bin/sh

set -e

# Wait for redis to finish loading
count=1
while true; do
  is_loading=`redis-cli info | grep -o -P '(?<=loading:)(0|1)'`
  if [ "x$is_loading" = "x0" ]; then
    break
  else
    echo "`date`: [$count] Waiting for redis to finish loading" 1>&2
    sleep 1
    count=$((count+1))
  fi
done
