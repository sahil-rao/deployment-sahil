#
# Super simple example of a Dockerfile
#
FROM ubuntu:14.04
MAINTAINER Samir Pujari "samir@cloudera.com"

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN apt-get update && \
    apt-get install -y python python-pip graphviz libgraphviz-dev pkg-config \
                       ntp python-dev monit

RUN pip install thrift==0.9.3 boto pika==0.9.8 networkx sqlparse \
                elasticsearch httplib2 pygraphviz redis \
                python-logstash binaryornot pymongo rlog mock \
                six --upgrade pbr funcsigs datadog pandas

RUN mkdir /var/Baaz
RUN mkdir /var/log/cloudera && mkdir /var/log/cloudera/navopt
ADD flightpath-deployment.tar.gz /
ADD Baaz-DataAcquisition-Service.tar.gz /
ADD Baaz-Analytics.tar.gz /
ADD Baaz-Analytics-Service.tar.gz /
ADD Baaz-Compile-Service.tar.gz /
