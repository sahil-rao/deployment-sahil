#!/bin/bash

set -eu

/usr/local/bin/wait_for_redis_to_load.sh
/usr/local/bin/join_redis_cluster.sh
/usr/local/bin/register_host.sh
