#!/bin/bash

set -eu

source /usr/local/bin/navoptenv.sh

CONF_DIR=$1

# Generate config yml file from Jinja2 template; Picks up env vars from navoptenv.sh
/usr/local/bin/j2 /usr/share/elasticsearch/elasticsearch.j2 > "${CONF_DIR}/elasticsearch.yml"
