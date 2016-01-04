#!/bin/bash

sudo echo "Strating build vm proces..."

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

#start building process
cd  /home/xplain/build

#Checkout deployment
cd /home/xplain/build/deployment
git pull
git checkout $1
git reset --hard
git pull

#Checkout analytics
cd /home/xplain/build/analytics
git pull
git checkout $1
git reset --hard
git pull

#Checkout compiler
cd /home/xplain/build/compiler
git pull
git checkout $1
git reset --hard
git pull

#Checkout graph
cd /home/xplain/build/graph
git pull
git checkout $1
git reset --hard
git pull

#Checkout UI
cd /home/xplain/build/UI
git pull
git checkout $1
git reset --hard
git pull

cd /home/xplain/build/graph
rm -rf build dist
python setup.py bdist 
cd dist
echo "Graph is built!"

cd /home/xplain/build/UI
tar -cvf  xplain.io.tar xplain.io
gzip -f  xplain.io.tar

tar -cvf  xplain_admin.tar xplain_admin
gzip -f  xplain_admin.tar

tar -cvf  xplain_dashboard.tar xplain_dashboard
gzip -f  xplain_dashboard.tar


cd /home/xplain/build/compiler
mvn package -DskipTests
if [ $? -eq 0 ]
then
  echo "Compiler is built"
else 
  echo "ERROR with compiler build process"
  exit 1
fi
mkdir baaz_compiler
#mv bin/com Baaz-Hive-Compiler/.
cp target/Baaz-Compiler/*.jar baaz_compiler/
tar -cvf  Baaz-Compiler.tar baaz_compiler
gzip -f  Baaz-Compiler.tar

cd /home/xplain/build/analytics
python setup.py bdist 
cd dist
echo "anaytics is built"


cp /home/xplain/build/deployment/scripts/vm-update-new.sh ~

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
cp /home/xplain/build/deployment/VM/xplain_admin.conf .
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

cp /home/xplain/build/deployment/VM/erlang.cookie.j2 .
cp /home/xplain/build/deployment/VM/installrabbit.sh .
cp /home/xplain/build/deployment/VM/redis.conf .
cp /home/xplain/build/deployment/VM/sentinel.conf .
cp /home/xplain/build/deployment/VM/redis-sentinel.conf .

cp /home/xplain/build/graph/dist/flightpath-*.tar.gz ./flightpath-deployment.tar.gz
cp /home/xplain/build/UI/xplain.io.tar.gz .
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

sudo ./refresh.sh
