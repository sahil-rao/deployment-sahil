#!/bin/bash

echo "Starting build vm process..."

BRANCH_NAME="master"
if [ -z "$1" ]
then
  echo "No branch supplied, using master"
else
  BRANCH_NAME=$1
fi

# Service discovery changes
redis-cli hmset dbsilo:Silo1:info redis 127.0.0.1 mongo 127.0.0.1 elastic 127.0.0.1
redis-cli -p 26379 sentinel monitor redismaster.dbsilo1.vm.xplain.io 127.0.0.1 6379 1
redis-cli -p 26379 sentinel monitor redismaster.Silo1.vm.xplain.io 127.0.0.1 6379 1

#check mvn dependency
if [ `command -v mvn` ]
then
  echo "Maven is installed"
else
  echo "Installing maven..."
  sudo apt-get install maven
fi

#check thrift dependency
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

#install java 8 if needed
if type -p java; then
  _java=java
else
  echo "no java"
fi

if [[ "$_java" ]]; then
    version=$("$_java" -version 2>&1 | awk -F '"' '/version/ {print $2}')
    echo version "$version"
    if [[ "$version" < "1.8" ]]; then
        sudo add-apt-repository ppa:webupd8team/java
        sudo apt update; sudo apt install -y oracle-java8-installer
    else
        echo "java version is up to date"
    fi
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

#check if thrift went through and has correct versions
if [ $is_thrift_ver -ne 0 -o $is_thrift_py_lib_ver -ne 0 ]
then
 echo "ERROR: Thrift/thrift python libraries are either missing or not of correct version"
 exit 1
else
 echo "All thrift dependencies met..."
fi

cd /home/xplain
cp /home/xplain/build/deployment/scripts/vm-gulp-config.js ~/gulp-config.js
npm install
#Build UI with Gulp
sudo gulp full-build --branch $BRANCH_NAME
sudo gulp eslint

#start building process
cd  /home/xplain/build

#Checkout UI
cd /home/xplain/build/UI
git pull
git checkout $BRANCH_NAME
git reset --hard
git pull

#Checkout deployment
cd /home/xplain/build/deployment
git pull
git checkout $BRANCH_NAME
git reset --hard
git pull

#Checkout analytics
cd /home/xplain/build/analytics
git pull
git checkout $BRANCH_NAME
git reset --hard
git pull

#Checkout compiler
cd /home/xplain/build/compiler
git pull
git checkout $BRANCH_NAME
git reset --hard
git pull

#Checkout graph
cd /home/xplain/build/graph
git pull
git checkout $BRANCH_NAME
git reset --hard
git pull

cd /home/xplain/build/graph
rm -rf build dist
python setup.py bdist
cd dist
echo "Graph is built!"

#This now gets handled by gulp script, when there is time so will admin and api
#cd /home/xplain/build/UI
#tar -cvf  xplain.io.tar xplain.io
#gzip -f  xplain.io.tar

tar -cvf  optimizer_admin.tar optimizer_admin
gzip -f  optimizer_admin.tar

tar -cvf  xplain_dashboard.tar xplain_dashboard
gzip -f  xplain_dashboard.tar


cd /home/xplain/build/compiler
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
cp target/Baaz-Compiler-1/*.jar baaz_compiler/
cp target/classes/logback.xml baaz_compiler/
tar -cvf  Baaz-Compiler.tar baaz_compiler
gzip -f  Baaz-Compiler.tar

cd /home/xplain/build/analytics
python setup.py bdist
cd dist
echo "anaytics is built"


cp /home/xplain/build/deployment/scripts/vm-update-new.yml ~/.

cd /home/xplain/build/deployment/Data-Aquisition
tar -cf  Baaz-DataAcquisition-Service.tar etc usr
gzip -f   Baaz-DataAcquisition-Service.tar


cd /home/xplain/build/deployment/Compile-Server
tar -cf  Baaz-Compile-Service.tar etc usr
gzip -f   Baaz-Compile-Service.tar


cd /home/xplain/build/deployment/Math-Server
tar -cf Baaz-Analytics-Service.tar etc usr
gzip -f   Baaz-Analytics-Service.tar

cd /home/xplain/build/compiler
tar -cf Baaz-Basestats-Report.tar reports
gzip -f   Baaz-Basestats-Report.tar


cd /home/xplain

#Make sure the build directory does not yet exist
rm -rf /home/xplain/build/VM-Deploy

#Make sure the build directory does not yet exist
mkdir /home/xplain/build/VM-Deploy

cd  /home/xplain/build/VM-Deploy

cp /home/xplain/build/deployment/VM/clear_tenant.sh .
cp /home/xplain/build/deployment/VM/monitrc .
cp /home/xplain/build/deployment/VM/api_nodejs.conf .
cp /home/xplain/build/deployment/VM/nodejs.conf .
cp /home/xplain/build/deployment/VM/admin_nodejs.conf .
cp /home/xplain/build/deployment/VM/README .
cp /home/xplain/build/deployment/VM/refresh.sh .
cp /home/xplain/build/deployment/VM/vm-update.yml .
cp /home/xplain/build/deployment/VM/setup-update.sh .
cp /home/xplain/build/deployment/VM/xplaincompile.conf .
cp /home/xplain/build/deployment/VM/setupSilo.py .
cp /home/xplain/build/deployment/VM/hosts.cfg .

cp /home/xplain/build/deployment/Data-Aquisition/etc/xplain/application-api.cfg .
cp /home/xplain/build/deployment/Data-Aquisition/etc/xplain/target_platforms.cfg .
cp /home/xplain/build/deployment/Math-Server/etc/xplain/adv_analytics.cfg .
cp /home/xplain/build/deployment/Math-Server/etc/xplain/analytics.cfg .
cp /home/xplain/build/deployment/Math-Server/etc/xplain/rules.cfg .
cp /home/xplain/build/deployment/Math-Server/etc/xplain/rule_workflows.cfg .
cp /home/xplain/build/deployment/Math-Server/etc/init/ruleengineservice.conf .

cp /home/xplain/build/deployment/VM/erlang.cookie.j2 .
cp /home/xplain/build/deployment/VM/installrabbit.sh .
cp /home/xplain/build/deployment/VM/redis.conf .
cp /home/xplain/build/deployment/VM/sentinel.conf .
cp /home/xplain/build/deployment/VM/redis-sentinel.conf .

cp /home/xplain/build/graph/dist/flightpath-*.tar.gz ./flightpath-deployment.tar.gz
cp /home/xplain/build/UI/xplain.io.tar.gz .
cp /home/xplain/build/UI/optimizer_admin.tar.gz .
cp /home/xplain/build/compiler/Baaz-Compiler.tar.gz .
cp /home/xplain/build/analytics/dist/baazmath-*.tar.gz Baaz-Analytics.tar.gz
cp /home/xplain/build/deployment/Data-Aquisition/Baaz-DataAcquisition-Service.tar.gz .
cp /home/xplain/build/deployment/Compile-Server/Baaz-Compile-Service.tar.gz .
cp /home/xplain/build/deployment/Math-Server/Baaz-Analytics-Service.tar.gz .
cp /home/xplain/build/compiler/Baaz-Basestats-Report.tar.gz .

tar -cvf ExplainIO-SingleVM-deploy.tar ./*
gzip ExplainIO-SingleVM-deploy.tar
cp ExplainIO-SingleVM-deploy.tar.gz ~/
cd ~/
tar -zxf ExplainIO-SingleVM-deploy.tar.gz

sudo ansible-playbook vm-update-new.yml --connection=local

python /home/xplain/build/deployment/scripts/add_data_files_to_xplainIO.py

sudo ./refresh.sh
