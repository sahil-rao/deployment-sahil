#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh

exec /usr/bin/python /usr/local/bin/cleanup_replicas.py
