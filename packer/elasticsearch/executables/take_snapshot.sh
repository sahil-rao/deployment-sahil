#!/bin/bash

set -eu

REPOSITORY_NAME="s3_repo"
SNAPSHOT_PREFIX="curator-gen-"

# Ensure repository has been created; operation is idempotent
curl -XPUT "localhost:9200/_snapshot/${REPOSITORY_NAME}" -d '{ "type": "s3"}'

# Take snapshot of all indices
/usr/local/bin/curator \
	--host localhost \
	snapshot \
	--prefix $SNAPSHOT_PREFIX \
	--repository $REPOSITORY_NAME \
	indices \
	--all-indices

# Delete snapshots older than 3 days
/usr/local/bin/curator \
	--host localhost \
	delete snapshots \
	--prefix $SNAPSHOT_PREFIX \
	--repository $REPOSITORY_NAME \
	--older-than 3 \
	--time-unit days \
	--timestring "%Y%m%d%H%M%S"
