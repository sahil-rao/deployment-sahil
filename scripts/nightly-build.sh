#!/bin/bash

#USAGE="Usage: $0 <build_version>"

#if [ "$#" == "0" ]; then
#    echo "$USAGE"
#    exit 1
#fi

#echo "Git repositories will be tagged with $1\n"

S3Bucket='baaz-deployment'
#Make sure the build directory does not yet exist
rm -rf /home/ubuntu/build 

#Make sure the build directory does not yet exist
mkdir /home/ubuntu/build 

cd  /home/ubuntu/build

#Checkout deployment
git clone https://github.com/baazdata/deployment.git

cd /home/ubuntu/build/deployment

while read line
do
    name=$line
    echo "Current-Build $name"
done < BuildInfo

IFS='.' read -ra ADDR <<< "$name"
major=${ADDR[0]}
minor=${ADDR[1]}
maint=${ADDR[2]}
build=${ADDR[3]}

build=$(($build + 1))

newBuildVersion=$major.$minor.$maint.$build
echo "Next Build $newBuildVersion"

echo $newBuildVersion > BuildInfo

git add BuildInfo
git commit -m "Build $newBuildVersion"
git push

cd /home/ubuntu/build

#Checkout analytics
git clone https://github.com/baazdata/analytics.git

#Checkout compiler
git clone https://github.com/baazdata/compiler.git

#Checkout graph
git clone https://github.com/baazdata/graph.git

#Checkout UI
git clone https://github.com/baazdata/UI.git

#Checkout Application
#git clone https://github.com/baazdata/application.git

cd /home/ubuntu/build/graph
git tag -a $newBuildVersion -m "version $newBuildVersion"
git push --tag
python setup.py bdist 
cd dist
s3cmd sync flightpath-*.tar.gz s3://$S3Bucket/$newBuildVersion/flightpath-deployment.tar.gz
echo "Graph is built"

cd /home/ubuntu/build/UI
git tag -a $newBuildVersion -m "version $newBuildVersion"
git push --tag
tar -cvf xplain.io.tar xplain.io
gzip xplain.io.tar
s3cmd sync xplain.io.tar.gz s3://$S3Bucket/$newBuildVersion/

cd /home/ubuntu/build/compiler
git tag -a $newBuildVersion -m "version $newBuildVersion"
git push --tag
cd /home/ubuntu/build/compiler/BAAZ_COMPILER
#ant clean
#ant build
ant main
echo "Compiler is built"
mkdir baaz_compiler
#mv bin/com Baaz-Hive-Compiler/.
cp bin/baaz_compiler.jar baaz_compiler/
cp lib/*.jar baaz_compiler/
tar -cvf Baaz-Compiler.tar baaz_compiler
gzip Baaz-Compiler.tar
s3cmd sync Baaz-Compiler.tar.gz s3://$S3Bucket/$newBuildVersion/

cd /home/ubuntu/build/analytics
git tag -a $newBuildVersion -m "version $newBuildVersion"
git push --tag
python setup.py bdist 
cd dist
echo "anaytics is built"
s3cmd sync baazmath-*.tar.gz s3://$S3Bucket/$newBuildVersion/Baaz-Analytics.tar.gz

#cd /home/ubuntu/build/application
#git tag -a $newBuildVersion -m "version $newBuildVersion"
#git push --tag
#python setup.py bdist 
#cd dist
#echo "application is built"
#s3cmd sync Baazapp-*.tar.gz s3://$S3Bucket/$newBuildVersion/Baazapp-deployment.tar.gz

cd /home/ubuntu/build/deployment
git tag -a $newBuildVersion -m "version $newBuildVersion"
git push --tag

cd /home/ubuntu/build/deployment/Data-Aquisition
tar -cf Baaz-DataAcquisition-Service.tar etc usr
gzip Baaz-DataAcquisition-Service.tar 
s3cmd sync Baaz-DataAcquisition-Service.tar.gz s3://$S3Bucket/$newBuildVersion/

cd /home/ubuntu/build/deployment/Compile-Server
tar -cf Baaz-Compile-Service.tar etc usr
gzip Baaz-Compile-Service.tar 
s3cmd sync Baaz-Compile-Service.tar.gz s3://$S3Bucket/$newBuildVersion/

cd /home/ubuntu/build/deployment/Math-Server
tar -cf Baaz-Analytics-Service.tar etc usr
gzip Baaz-Analytics-Service.tar 
s3cmd sync Baaz-Analytics-Service.tar.gz s3://$S3Bucket/$newBuildVersion/

cd /home/ubuntu/build/compiler
tar -cf Baaz-Basestats-Report.tar reports 
gzip Baaz-Basestats-Report.tar
s3cmd sync Baaz-Basestats-Report.tar.gz s3://$S3Bucket/$newBuildVersion/
