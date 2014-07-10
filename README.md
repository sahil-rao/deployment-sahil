deployment
==========

Deployment


RABBITMQ Notes
===========================

To install rabbitmq on any ubuntu machine:

sudo chmod u+x installrabbit.sh
sudo ./installrabbit.sh

installrabbit.sh is in deployment/scripts

===============================
To cluster:

The erlang cookies of all the rabbitmq nodes must be the same.
These cookies live in /var/lib/rabbitmq/.erlang.cookie
Do not just vi/emacs into the cookies as it will insert a newline and that will make the cookie invalid.
To ensure the cookies are the same, start one node (in disk mode) and copy its cookie.
Then just echo -n into the second node's cookie. Ensure that both cookies are the same.
RabbitMQ will not allow you to copy into it without permissions, so you must change the ownership and permissions to access it.
BUT MAKE SURE TO CHANGE IT BACK!!! RabbitMQ requires that it be the sole owner of the cookie and only it has read permissions (not even write). You can use chmod 0400 for this.

Also, DO NOT TAKE BOTH NODES DOWN AT THE SAME TIME! Bad things will happen.

The ports that need to be open for clustering to work:
PORT 4369: Erlang makes use of a Port Mapper Daemon (epmd) for resolution of node names in a cluster. 
PORT 35197 set by inet_dist_listen_min/max Firewalls must permit traffic in this range to pass between clustered nodes

RabbitMQ Management console:

PORT 15672 for RabbitMQ version 3.x
PORT 55672 for RabbitMQ pre 3.x
PORT 5672 RabbitMQ main port.

