#!/bin/bash
 
#####################################
#ERLANG INSTALLATION

if [ $(id -u) != "0" ]; then
echo "You must be the superuser to run this script" >&2
exit 1
fi

apt-get update
 
# Install the build tools (dpkg-dev g++ gcc libc6-dev make)
apt-get -y install build-essential
 
# automatic configure script builder (debianutils m4 perl)
apt-get -y install autoconf
 
# Needed for HiPE (native code) support, but already installed by autoconf
# apt-get -y install m4
 
# Needed for terminal handling (libc-dev libncurses5 libtinfo-dev libtinfo5 ncurses-bin)
apt-get -y install libncurses5-dev
 
# For building with wxWidgets
apt-get -y install libwxgtk2.8-dev libgl1-mesa-dev libglu1-mesa-dev libpng3
 
# For building ssl (libssh-4 libssl-dev zlib1g-dev)
apt-get -y install libssh-dev
 
# ODBC support (libltdl3-dev odbcinst1debian2 unixodbc)
apt-get -y install unixodbc-dev
mkdir -p ~/code/erlang
cd ~/code/erlang
 
if [ -e otp_src_17.1.tar.gz ]; then
echo "'otp_src_17.1.tar.gz' already exists. Skipping download."
else
wget http://www.erlang.org/download/otp_src_17.1.tar.gz
fi
tar -xvzf otp_src_17.1.tar.gz
chmod -R 777 otp_src_17.1
cd otp_src_17.1
./configure
make
make install

####################################
#RABBITMQ INSTALLATION

cat <<EOF > /etc/apt/sources.list.d/rabbitmq.list
deb http://www.rabbitmq.com/debian testing main
EOF

curl http://www.rabbitmq.com/rabbitmq-signing-key-public.asc -o /tmp/rabbitmq-signing-key-public.asc
apt-key add /tmp/rabbitmq-signing-key-public.asc
rm /tmp/rabbitmq-signing-key-public.asc

apt-get -y update
apt-get -y install rabbitmq-server

exit 0
