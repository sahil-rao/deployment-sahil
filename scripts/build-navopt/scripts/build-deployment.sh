#!/bin/bash

set -eux

BRANCH=$1

git -C /gitcache/deployment archive $BRANCH | tar -x

echo "--- building data aquisition..."
cd Data-Aquisition
tar -zcvf /target/Baaz-DataAcquisition-Service.tar.gz etc usr
cd ..

echo "--- building compile server..."
cd Compile-Server
tar -zcvf /target/Baaz-Compile-Service.tar.gz etc usr
cd ..

echo "--- building math server..."
cd Math-Server
tar -zcvf /target/Baaz-Analytics-Service.tar.gz etc usr
cd ..

echo "--- building api server..."
cd API-Server
tar -zcvf /target/Baaz-API-Service.tar.gz etc usr
cd ..


echo "--- building telemetry consumer..."
cd TeleMetry-Consumer
echo "--- building compiler..."
mvn install

echo "--- archiving compiler..."
mkdir teleMetry

cp target/lib/*.jar teleMetry/
cp target/*.jar teleMetry/
cp target/classes/logback.xml teleMetry/
tar -zcvf /target/Baaz-TeleMetry.tar.gz etc usr teleMetry
cd ..