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