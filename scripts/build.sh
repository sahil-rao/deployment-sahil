#!/bin/bash

LOCKFILE=/var/lock/buildlock
function cleanup() {
  rm $LOCKFILE
  exit 1
}

trap cleanup INT

if [ -f $LOCKFILE ]; then
  echo "Someone else is building!"
  exit 1
fi

touch $LOCKFILE

set -e

#check prerequisites
if [ `command -v mvn` ]
then
  echo "Maven is installed"
else
  echo "Installing maven..."
  sudo apt-get install maven
fi

if [ `command -v thrift` ]
then
  echo "thrift is installed"
else
  sudo apt-get -y install ant
  sudo apt-get -y install libboost-dev libboost-test-dev libboost-program-options-dev libevent-dev automake libtool flex bison pkg-config g++ libssl-dev
  sudo apt-get install make
  wget http://mirror.nexcess.net/apache/thrift/0.9.3/thrift-0.9.3.tar.gz
  rm -rf thrift-0.9.3
  tar -xvf thrift-0.9.3.tar.gz
  cd thrift-0.9.3
  ./bootstrap.sh
  ./configure
  sudo make
  sudo make install
  sudo pip install 'thrift==0.9.3'
  cd ..
fi

#check for python thrift libraries
pip show thrift|grep 0.9.3
ispip=`echo $?`
if [ $ispip -ne 0 ]
then
  sudo pip install 'thrift==0.9.3'
else
  echo "thrift python library present.."
fi

thrift -version |grep 0.9.3
is_thrift_ver=`echo $?`
pip show thrift|grep 0.9.3
is_thrift_py_lib_ver=`echo $?`

#check if thrift went through
if [ $is_thrift_ver -ne 0 -o $is_thrift_py_lib_ver -ne 0 ]
then
 echo "ERROR: Thrift/thrift python libraries are either missing or not of correct version"
 exit 1
else
 echo "All thrift dependencies met..."
fi

S3Bucket='baaz-deployment'
#Make sure the build directory does not yet exist
rm -rf build/

#Make sure the build directory does not yet exist
mkdir build

cd build

#Checkout deployment
git clone https://github.com/baazdata/deployment.git

#Checkout analytics
git clone https://github.com/baazdata/analytics.git

#Checkout compiler
git clone https://github.com/baazdata/compiler.git

#Checkout graph
git clone https://github.com/baazdata/graph.git

#Checkout UI
git clone https://github.com/baazdata/UI.git

#Checkout UI-Tests
git clone https://github.com/baazdata/NavOptTest.git

#Checkout documentation
git clone https://github.com/baazdata/documentation.git

#Checkout Application
git clone https://github.com/baazdata/application.git

#add help topics to S3
s3cmd sync documentation/NavOptHelp/ s3://xplain-public/$clusterName/documentation/NavOptHelp/ --delete --acl-public

cd graph
python setup.py bdist
cd dist
s3cmd sync flightpath-*.tar.gz s3://$S3Bucket/flightpath-deployment.tar.gz
echo "Graph is built"

cd NavOptTest
tar -cvf navopttest.tar *
gzip navopttest.tar
s3cmd sync navopttest.tar.gz s3://$S3BUcket/

cd ../../UI/webapp/war
tar -cvf UI.tar *
gzip UI.tar
s3cmd sync UI.tar.gz s3://$S3Bucket/
cd ../..
tar -cvf xplain.io.tar xplain.io
gzip xplain.io.tar
s3cmd sync xplain.io.tar.gz s3://$S3Bucket/
tar -cvf optimizer_api.io.tar optimizer_api
gzip optimizer_api.io.tar
s3cmd sync optimizer_api.io.tar.gz s3://$S3Bucket/
tar -cvf optimizer_admin.io.tar optimizer_admin
gzip optimizer_admin.io.tar
s3cmd sync optimizer_admin.io.tar.gz s3://$S3Bucket/
tar -cvf xplain_dashboard.tar xplain_dashboard
gzip xplain_dashboard.tar
s3cmd sync xplain_dashboard.tar.gz s3://$S3Bucket/
tar -cvf optimizer_admin.io.tar optimizer_admin
gzip optimizer_admin.io.tar
s3cmd sync optimizer_admin.io.tar.gz s3://$S3Bucket/
tar -cvf exec_dashboard.tar exec_dashboard
gzip exec_dashboard.tar
s3cmd sync exec_dashboard.tar.gz s3://$S3Bucket/
tar -cvf xplain_dashboard.tar xplain_dashboard
gzip xplain_dashboard.tar
s3cmd sync xplain_dashboard.tar.gz s3://$S3Bucket/

cd ../compiler
mvn clean
mvn package -DskipTests
if [ $? -eq 0 ]
then
  echo "Compiler is built"
else
  echo "ERROR with compiler build process"
  exit 1
fi
mkdir baaz_compiler
rm -rf baaz_compiler/*
#mv bin/com Baaz-Hive-Compiler/.
cp target/Baaz-Compiler/*.jar baaz_compiler/
cp target/classes/logback.xml baaz_compiler/
tar -cvf Baaz-Compiler.tar baaz_compiler
gzip Baaz-Compiler.tar
s3cmd sync Baaz-Compiler.tar.gz s3://$S3Bucket/

cd ../analytics
python setup.py bdist
cd dist
echo "anaytics is built"
s3cmd sync baazmath-*.tar.gz s3://$S3Bucket/Baaz-Analytics.tar.gz

cd ../../application
python setup.py bdist
cd dist
echo "application is built"
s3cmd sync Baazapp-*.tar.gz s3://$S3Bucket/Baazapp-deployment.tar.gz

cd ../../deployment/Data-Aquisition
tar -cf Baaz-DataAcquisition-Service.tar etc usr
gzip Baaz-DataAcquisition-Service.tar
s3cmd sync Baaz-DataAcquisition-Service.tar.gz s3://$S3Bucket/

cd ../Compile-Server
tar -cf Baaz-Compile-Service.tar etc usr
gzip Baaz-Compile-Service.tar
s3cmd sync Baaz-Compile-Service.tar.gz s3://$S3Bucket/

cd ../Math-Server
tar -cf Baaz-Analytics-Service.tar etc usr
gzip Baaz-Analytics-Service.tar
s3cmd sync Baaz-Analytics-Service.tar.gz s3://$S3Bucket/

rm $LOCKFILE
