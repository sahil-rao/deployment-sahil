#
# Dockerfile to install compiler jars on top of python service base image.
#
FROM navopt/pyservices
MAINTAINER Samir Pujari "samir@cloudera.com"

# Install Java.
RUN apt-get update && apt-get install -y software-properties-common && \
    echo oracle-java7-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
    add-apt-repository -y ppa:webupd8team/java && \
    apt-get update && \
    apt-get install -y oracle-java7-installer && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/oracle-jdk7-installer

ENV JAVA_HOME /usr/lib/jvm/java-7-oracle

ADD Baaz-Compiler.tar.gz /usr/lib
ADD compileserver /etc/logrotate.d/