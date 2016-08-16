#
# Super simple example of a Dockerfile
#
FROM navopt/pyservice
MAINTAINER Samir Pujari "samir@cloudera.com"

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN apt-get update && apt-get install -y openjdk-7-jdk
ADD Baaz-Compiler.tar.gz /usr/lib
ADD compileserver /etc/logrotate.d/