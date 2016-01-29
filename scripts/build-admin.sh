#!/bin/bash
#check prerequisites
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
rm -rf /home/ubuntu/build/UI 

#Make sure the build directory does not yet exist
mkdir /home/ubuntu/build/UI

cd  /home/ubuntu/build

#Checkout UI
#git clone -b dbsilo https://github.com/baazdata/UI.git 
git clone https://github.com/baazdata/UI.git 
#cd /home/ubuntu/build/UI
#git pull --rebase

cd /home/ubuntu/build/UI/webapp/war
tar -cvf UI.tar *
gzip UI.tar
s3cmd sync UI.tar.gz s3://$S3Bucket/
cd /home/ubuntu/build/UI
tar -cvf optimizer_admin.io.tar optimizer_admin
gzip optimizer_admin.io.tar
s3cmd sync optimizer_admin.io.tar.gz s3://$S3Bucket/


rm $LOCKFILE
