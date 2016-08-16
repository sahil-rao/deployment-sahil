#!/bin/bash

mkdir /Users/samir/git/docker/packages
mkdir /Users/samir/git/docker/packages/pyservices
mkdir /Users/samir/git/docker/packages/javaservices
cd /Users/samir/git/compiler
mkdir baaz_compiler
rm -rf baaz_compiler/*
#mv bin/com Baaz-Hive-Compiler/.
cp target/Baaz-Compiler/*.jar baaz_compiler/
cp target/classes/logback.xml baaz_compiler/
tar -cvf Baaz-Compiler.tar baaz_compiler
gzip Baaz-Compiler.tar
cp Baaz-Compiler.tar.gz /Users/samir/git/docker/packages/javaservices

cd /Users/samir/git/graph
python setup.py bdist 
cd dist
cp flightpath-*.tar.gz /Users/samir/git/docker/packages/pyservices/flightpath-deployment.tar.gz
echo "graph is built"

cd /Users/samir/git/analytics
python setup.py bdist 
cd dist
cp baazmath-*.tar.gz /Users/samir/git/docker/packages/pyservices/Baaz-Analytics.tar.gz
echo "anaytics is built"

cd /Users/samir/git/deployment/Data-Aquisition
tar -cf Baaz-DataAcquisition-Service.tar etc usr
gzip Baaz-DataAcquisition-Service.tar
cp Baaz-DataAcquisition-Service.tar.gz /Users/samir/git/docker/packages/pyservices

cd /Users/samir/git/deployment/Compile-Server
tar -cf Baaz-Compile-Service.tar etc usr
gzip Baaz-Compile-Service.tar 
cp Baaz-Compile-Service.tar.gz /Users/samir/git/docker/packages/pyservices

cd /Users/samir/git/deployment/Math-Server
tar -cf Baaz-Analytics-Service.tar etc usr
gzip Baaz-Analytics-Service.tar 
cp Baaz-Analytics-Service.tar.gz /Users/samir/git/docker/packages/pyservices
echo "deployment is built"