FROM ubuntu:14.04
MAINTAINER Erick Tryzelaar "erickt@cloudera.com"

RUN \
	apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y software-properties-common && \
	echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
	add-apt-repository -y ppa:webupd8team/java && \
	apt-get update && \
	apt-get install -y oracle-java8-installer

RUN apt-get -y install \
	ant \
	automake \
	bison \
	flex \
	g++ \
	git \
	libboost-dev \
	libboost-program-options-dev \
	libboost-test-dev \
	libevent-dev \
	libssl-dev \
	libtool \
	make \
	maven \
	pkg-config \
	python-dev \
	python-pip

ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

# Install thrift
RUN \
  wget http://mirror.nexcess.net/apache/thrift/0.9.3/thrift-0.9.3.tar.gz && \
  tar -xvf thrift-0.9.3.tar.gz && \
  cd thrift-0.9.3 && \
  ./configure && \
  make -j`grep -c '^processor' /proc/cpuinfo` --load-average=`grep -c '^processor' /proc/cpuinfo` && \
  make install && \
	cd .. && \
	rm -r thrift-0.9.3.tar.gz thrift-0.9.3 && \
	pip install thrift==0.9.3

WORKDIR /build
