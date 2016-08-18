#
# Dockerfile to install compiler jars on top of python service base image.
#
FROM navopt/pyservice
MAINTAINER Samir Pujari "samir@cloudera.com"

RUN apt-get update && apt-get install -y openjdk-7-jdk
ADD Baaz-Compiler.tar.gz /usr/lib
ADD compileserver /etc/logrotate.d/