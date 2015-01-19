#!/bin/bash

#Make sure the build directory does not yet exist
rm -rf /home/ubuntu/build/VM-Deploy

#Make sure the build directory does not yet exist
mkdir /home/ubuntu/build/VM-Deploy

cd  /home/ubuntu/build/VM-Deploy

cp /home/ubuntu/build/deployment/VM/apache-hive-0.13.0-SNAPSHOT-bin.tar.gz .
cp /home/ubuntu/build/deployment/VM/clear_tenant.sh .
cp /home/ubuntu/build/deployment/VM/monitrc .
cp /home/ubuntu/build/deployment/VM/nodejs.conf .
cp /home/ubuntu/build/deployment/VM/xplain_admin.conf .
cp /home/ubuntu/build/deployment/VM/README .
cp /home/ubuntu/build/deployment/VM/refresh.sh .
cp /home/ubuntu/build/deployment/VM/vm-update.yml .
cp /home/ubuntu/build/deployment/VM/setup-update.sh .
cp /home/ubuntu/build/deployment/VM/xplaincompile.conf .
cp /home/ubuntu/build/deployment/VM/setupSilo.py .
cp /home/ubuntu/build/deployment/VM/hosts.cfg .

cp /home/ubuntu/build/deployment/Data-Aquisition/etc/xplain/application-api.cfg .
cp /home/ubuntu/build/deployment/Math-Server/etc/xplain/adv_analytics.cfg .
cp /home/ubuntu/build/deployment/Math-Server/etc/xplain/analytics.cfg .

cp /home/ubuntu/build/deployment/VM/erlang.cookie.j2 .
cp /home/ubuntu/build/deployment/VM/installrabbit.sh .
cp /home/ubuntu/build/deployment/VM/redis.conf .
cp /home/ubuntu/build/deployment/VM/sentinel.conf .
cp /home/ubuntu/build/deployment/VM/redis-sentinel.conf .

cp /home/ubuntu/build/graph/dist/flightpath-*.tar.gz ./flightpath-deployment.tar.gz
cp /home/ubuntu/build/UI/xplain.io.tar.gz .
cp /home/ubuntu/build/compiler/BAAZ_COMPILER/Baaz-Compiler.tar.gz .
cp /home/ubuntu/build/analytics/dist/baazmath-*.tar.gz Baaz-Analytics.tar.gz
cp /home/ubuntu/build/deployment/Data-Aquisition/Baaz-DataAcquisition-Service.tar.gz .
cp /home/ubuntu/build/deployment/Compile-Server/Baaz-Compile-Service.tar.gz .
cp /home/ubuntu/build/deployment/Math-Server/Baaz-Analytics-Service.tar.gz .
cp /home/ubuntu/build/compiler/Baaz-Basestats-Report.tar.gz .

tar -cvf ExplainIO-SingleVM-deploy.tar ./*
gzip ExplainIO-SingleVM-deploy.tar