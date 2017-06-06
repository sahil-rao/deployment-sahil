#
# Dockerfile to install all required libraries needed for python services.
#
FROM ubuntu:14.04
MAINTAINER Samir Pujari "samir@cloudera.com"

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN apt-get update && \
    apt-get install -y python python-pip graphviz libgraphviz-dev pkg-config \
                       ntp python-dev monit emacs

RUN pip install -U pip

RUN pip install thrift==0.9.3 boto pika==0.9.8 networkx sqlparse \
                elasticsearch httplib2 pygraphviz redis \
                python-logstash binaryornot pymongo rlog mock \
                six --upgrade pbr funcsigs datadog pandas j2cli py_zipkin scipy

RUN mkdir /var/Baaz
RUN mkdir /var/log/cloudera && mkdir /var/log/cloudera/navopt
ADD target/flightpath-deployment.tar.gz /
ADD target/Baaz-DataAcquisition-Service.tar.gz /
ADD target/Baaz-API-Service.tar.gz /
ADD target/Baaz-Analytics.tar.gz /
ADD target/Baaz-Analytics-Service.tar.gz /
ADD target/Baaz-Compile-Service.tar.gz /
ADD navopt-pyservices/hosts.j2 /
ADD navopt-pyservices/logback.j2 /
ADD navopt-pyservices/config.json /
ADD navopt-pyservices/start.sh /
CMD ./start.sh
