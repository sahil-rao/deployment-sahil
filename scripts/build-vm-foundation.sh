#!/bin/bash

#Make sure the build directory does not yet exist
rm -rf /home/ubuntu/build/VM-Foundation

#Make sure the build directory does not yet exist
mkdir /home/ubuntu/build/VM-Foundation

cd  /home/ubuntu/build/VM-Foundation
cp /home/ubuntu/build/deployment/VM/hosts .
cp /home/ubuntu/build/deployment/VM/hosts.cfg .
cp /home/ubuntu/build/deployment/VM/ga.cfg . 
cp /home/ubuntu/build/deployment/VM/setup-foundation.sh .
cp /home/ubuntu/build/deployment/VM/vm-foundation.yml .
cp /home/ubuntu/build/deployment/VM/nodejs.conf .
cp /home/ubuntu/build/deployment/VM/xplain_admin.conf .
cp /home/ubuntu/build/deployment/VM/Splash.png .
cp /home/ubuntu/build/deployment/VM/hive.conf . 
cp /home/ubuntu/build/deployment/VM/hive-site.xml . 
cp /home/ubuntu/build/deployment/VM/mysql-connector-java-5.1.30-bin.jar .

tar -cvf ExplainIO-Foundation.tar ./*
gzip ExplainIO-Foundation.tar
