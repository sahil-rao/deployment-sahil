FROM ubuntu:16.04
MAINTAINER Erick Tryzelaar "erickt@cloudera.com"

RUN \
        apt-get update && \
        apt-get upgrade -y && \
        apt-get install -y software-properties-common && \
        echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
        add-apt-repository -y ppa:webupd8team/java && \
        apt-get update && \
        apt-get install -y oracle-java8-installer

RUN apt-get update && \
  apt-get -y install \
        ant \
        automake \
        bison \
        curl \
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

RUN set -ex \
  && for key in \
    9554F04D7259F04124DE6B476D5A82AC7E37093B \
    94AE36675C464D64BAFA68DD7434390BDBE9B9C5 \
    0034A06D9D9B0064CE8ADF6BF1747F4AD2306D93 \
    FD3A5288F042B6850C66B31F09FE44734EB7990E \
    71DCFD284A79C3B38668286BC97EC7A07EDE3FC1 \
    DD8F2338BAE7501E3DD5AC78C273792F7D83545D \
    B9AE9905FFD7803F25714661B63B535A4C206CA9 \
    C4F0DFFF4E8C1A8236409D08E73BC641CC11F4C8 \
    56730D5401028683275BD23C23EFEFE93C4CFFFE \
  ; do \
    gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$key"; \
  done

ENV NPM_CONFIG_LOGLEVEL info
ENV NODE_VERSION 6.10.0

RUN curl -SLO "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.xz" \
  && curl -SLO "https://nodejs.org/dist/v$NODE_VERSION/SHASUMS256.txt.asc" \
  && gpg --batch --decrypt --output SHASUMS256.txt SHASUMS256.txt.asc \
  && grep " node-v$NODE_VERSION-linux-x64.tar.xz\$" SHASUMS256.txt | sha256sum -c - \
  && tar -xJf "node-v$NODE_VERSION-linux-x64.tar.xz" -C /usr/local --strip-components=1 \
  && rm "node-v$NODE_VERSION-linux-x64.tar.xz" SHASUMS256.txt.asc SHASUMS256.txt \
  && ln -s /usr/local/bin/node /usr/local/bin/nodejs

RUN npm cache clean && \
                npm install -g gulp-cli

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

RUN locale-gen en_US.UTF-8

RUN apt-get -y install libcurl4-openssl-dev

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

WORKDIR /build
