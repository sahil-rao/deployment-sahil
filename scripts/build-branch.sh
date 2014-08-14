#!/bin/bash

S3Bucket="baaz-deployment/$1"
#Make sure the build directory does not yet exist
rm -rf /home/ubuntu/build 

#Make sure the build directory does not yet exist
mkdir /home/ubuntu/build 

cd  /home/ubuntu/build

#Checkout deployment
git clone -b $1 https://github.com/baazdata/deployment.git
#cd /home/ubuntu/build/deployment
#git pull --rebase

#Checkout analytics
git clone -b $1 https://github.com/baazdata/analytics.git
#cd /home/ubuntu/build/analytics
#git pull --rebase

#Checkout compiler
git clone -b $1 https://github.com/baazdata/compiler.git
#cd /home/ubuntu/build/compiler
#git pull --rebase

#Checkout graph
git clone -b $1 https://github.com/baazdata/graph.git
#cd /home/ubuntu/build/graph
#git pull --rebase

#Checkout UI
git clone -b $1 https://github.com/baazdata/UI.git
#cd /home/ubuntu/build/UI
#git pull --rebase

#Checkout Application
git clone https://github.com/baazdata/application.git
#cd /home/ubuntu/build/application
#git pull --rebase

cd /home/ubuntu/build/graph
python setup.py bdist 
cd dist
s3cmd sync flightpath-*.tar.gz s3://$S3Bucket/flightpath-deployment.tar.gz
echo "Graph is built"

cd /home/ubuntu/build/UI/webapp/war
tar -cvf UI.tar *
gzip UI.tar
s3cmd sync UI.tar.gz s3://$S3Bucket/
cd /home/ubuntu/build/UI
tar -cvf xplain.io.tar xplain.io
gzip xplain.io.tar
s3cmd sync xplain.io.tar.gz s3://$S3Bucket/

cd /home/ubuntu/build/compiler/BAAZ_COMPILER
ant main
echo "Compiler is built"
mkdir baaz_compiler
#mv bin/com Baaz-Hive-Compiler/.
cp bin/baaz_compiler.jar baaz_compiler/
cp lib/*.jar baaz_compiler/
tar -cvf Baaz-Compiler.tar baaz_compiler
gzip Baaz-Compiler.tar
s3cmd sync Baaz-Compiler.tar.gz s3://$S3Bucket/

cd /home/ubuntu/build/analytics
python setup.py bdist 
cd dist
echo "anaytics is built"
s3cmd sync baazmath-*.tar.gz s3://$S3Bucket/Baaz-Analytics.tar.gz

cd /home/ubuntu/build/application
python setup.py bdist 
cd dist
echo "application is built"
s3cmd sync Baazapp-*.tar.gz s3://$S3Bucket/Baazapp-deployment.tar.gz

cd /home/ubuntu/build/deployment/Data-Aquisition
tar -cf Baaz-DataAcquisition-Service.tar etc usr
gzip Baaz-DataAcquisition-Service.tar 
s3cmd sync Baaz-DataAcquisition-Service.tar.gz s3://$S3Bucket/

cd /home/ubuntu/build/deployment/Compile-Server
tar -cf Baaz-Compile-Service.tar etc usr
gzip Baaz-Compile-Service.tar 
s3cmd sync Baaz-Compile-Service.tar.gz s3://$S3Bucket/

cd /home/ubuntu/build/deployment/Math-Server
tar -cf Baaz-Analytics-Service.tar etc usr
gzip Baaz-Analytics-Service.tar 
s3cmd sync Baaz-Analytics-Service.tar.gz s3://$S3Bucket/

cd /home/ubuntu/build/compiler
tar -cf Baaz-Basestats-Report.tar reports 
gzip Baaz-Basestats-Report.tar
s3cmd sync Baaz-Basestats-Report.tar.gz s3://$S3Bucket/
