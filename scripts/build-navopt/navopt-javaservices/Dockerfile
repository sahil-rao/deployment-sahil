#
# Dockerfile to install compiler jars on top of python service base image.
#
FROM navopt-pyservices
MAINTAINER Samir Pujari "samir@cloudera.com"

# Install Java.
RUN apt-get update && apt-get install -y software-properties-common && \
    echo oracle-java7-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
    add-apt-repository -y ppa:webupd8team/java && \
    apt-get update && \
    apt-get install -y oracle-java8-installer && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/oracle-jdk8-installer

ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

ADD target/Baaz-Compiler.tar.gz /usr/lib
ADD navopt-javaservices/compileserver /etc/logrotate.d/
