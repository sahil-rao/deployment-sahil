#!/bin/bash

LOCKFILE=/var/lock/buildlock
function cleanup() {
  rm $LOCKFILE
  exit 0
}

trap cleanup INT

if [ -f $LOCKFILE ]; then
  echo "Someone else is building!"
  exit 0
fi

touch $LOCKFILE

S3Bucket='baaz-deployment'
#Make sure the build directory does not yet exist
rm -rf build/UI 

cd  build

#Checkout UI
git clone https://github.com/baazdata/UI.git 

cd UI
tar -cvf xplain.io.tar xplain.io
gzip xplain.io.tar
s3cmd sync xplain.io.tar.gz s3://$S3Bucket/

rm $LOCKFILE
