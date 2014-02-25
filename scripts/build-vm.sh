#!/bin/bash

#Make sure the build directory does not yet exist
rm -rf /home/ubuntu/build/VM

#Make sure the build directory does not yet exist
mkdir /home/ubuntu/build/VM

cd  /home/ubuntu/build/VM
cp -r /home/ubuntu/build/deployment/VM/* .

cp /home/ubuntu/build/graph/dist/flightpath-*.tar.gz ./flightpath-deployment.tar.gz
#cp /home/ubuntu/build/UI/webapp/war/UI.tar.gz .
cp /home/ubuntu/build/UI/xplain.io.tar.gz .
cp /home/ubuntu/build/compiler/BAAZ_COMPILER/Baaz-Compiler.tar.gz .
cp /home/ubuntu/build/analytics/dist/baazmath-*.tar.gz Baaz-Analytics.tar.gz
#cp /home/ubuntu/build/application/dist/Baazapp-*.tar.gz Baazapp-deployment.tar.gz
cp /home/ubuntu/build/deployment/Data-Aquisition/Baaz-DataAcquisition-Service.tar.gz .
cp /home/ubuntu/build/deployment/Compile-Server/Baaz-Compile-Service.tar.gz .
cp /home/ubuntu/build/deployment/Math-Server/Baaz-Analytics-Service.tar.gz .
cp /home/ubuntu/build/compiler/Baaz-Basestats-Report.tar.gz .

tar -cvf ExplainIO-SingleVM-deploy.tar ./*
gzip ExplainIO-SingleVM-deploy.tar
