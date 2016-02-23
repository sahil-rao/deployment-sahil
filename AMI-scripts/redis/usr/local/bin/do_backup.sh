#!/bin/bash 

source /usr/local/bin/navoptenv.sh

datestr=`date -uIseconds`
bucket="xplain-${CLUSTER}"
prefix="${DBSILO}/redis-backups"
s3path="s3://${bucket}/${prefix}/dump${datestr}.rdb"

# Copy redis dump file (.rdb) to s3
aws s3 cp /var/lib/redis/dump.rdb $s3path 

# Ensure that all files with the prefix will expire in 3 days
expire_policy_json='{"Rules":[{"Status":"Enabled","Prefix":'"\"${prefix}"\"',"Expiration":{"Days":3}}]}'
aws s3api put-bucket-lifecycle --bucket $bucket --lifecycle-configuration $expire_policy_json
