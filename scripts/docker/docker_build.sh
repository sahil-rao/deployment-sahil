#!/bin/bash

echo "Starting build process..."

BRANCH_NAME="master"
S3Bucket='baaz-deployment'
if [ -z "$1" ]
then
  echo "No branch supplied, using master"
else
  BRANCH_NAME=$1
  S3Bucket="baaz-deployment/$BRANCH_NAME"
fi

CUR_LOC=$(pwd)
if cd $CUR_LOC/build; then echo "build folder exists"; else mkdir $CUR_LOC/build; fi

#pulling all repos
array=("deployment" "analytics" "compiler" "UI" "graph" "documentation")
for REPO in "${array[@]}"
do
    :
    echo $REPO
    if cd $CUR_LOC/build/$REPO
    then
        git pull
        git checkout $BRANCH_NAME
        git reset --hard
        git pull
    else git clone https://github.com/baazdata/$REPO.git --branch $BRANCH_NAME --single-branch
    fi
done

rm -r $CUR_LOC/docker
cp -r $CUR_LOC/build/deployment/scripts/docker/ $CUR_LOC/.

#Build and tar the compiler
cd $CUR_LOC/build/compiler
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
cp target/Baaz-Compiler/*.jar baaz_compiler/
cp target/classes/logback.xml baaz_compiler/
tar -cvf Baaz-Compiler.tar baaz_compiler
gzip -f Baaz-Compiler.tar
cp Baaz-Compiler.tar.gz $CUR_LOC/docker/javaservices

#Build and Package all the rest of the backoffice.
cd $CUR_LOC/build/graph
python setup.py bdist 
cd dist
cp flightpath-*.tar.gz $CUR_LOC/docker/pyservices/flightpath-deployment.tar.gz
echo "graph is built"

cd $CUR_LOC/build/analytics
python setup.py bdist 
cd dist
cp baazmath-*.tar.gz $CUR_LOC/docker/pyservices/Baaz-Analytics.tar.gz
echo "anaytics is built"

cd $CUR_LOC/build/deployment/Data-Aquisition
tar -cf Baaz-DataAcquisition-Service.tar etc usr
gzip -f Baaz-DataAcquisition-Service.tar
cp Baaz-DataAcquisition-Service.tar.gz $CUR_LOC/docker/pyservices

cd $CUR_LOC/build/deployment/Compile-Server
tar -cf Baaz-Compile-Service.tar etc usr
gzip -f Baaz-Compile-Service.tar 
cp Baaz-Compile-Service.tar.gz $CUR_LOC/docker/pyservices

cd $CUR_LOC/build/deployment/Math-Server
tar -cf Baaz-Analytics-Service.tar etc usr
gzip -f Baaz-Analytics-Service.tar 
cp Baaz-Analytics-Service.tar.gz $CUR_LOC/docker/pyservices

cd $CUR_LOC/docker/pyservices
docker build -t navopt/pyservice .

cd $CUR_LOC/docker/javaservices
docker build -t navopt/combinedservice .

echo "Saving docker images"
docker save -o $CUR_LOC/pyservice navopt/pyservice
docker save -o $CUR_LOC/combinedservice navopt/combinedservice

echo "Copying to s3"
aws s3 cp $CUR_LOC/pyservice s3://$S3Bucket/
aws s3 cp $CUR_LOC/combinedservice s3://$S3Bucket/
echo "deployment is built"