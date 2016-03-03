#!/bin/bash

source /usr/local/bin/navoptenv.sh

# Make sure we have SSL certificates if ssl is enabled
if [ "x$SSL_MODE" = "xenabled" ] && ([ ! -f /etc/nginx/ssl/xplain_san_cert.crt ] || [ ! -f /etc/nginx/ssl/san_cloudera_com.key ]); then
    echo "SSL enabled; Nginx cannot start without SSL certificates. Please install SSL certificates." 1>&2
    exit 1
fi

# Template config files; j2 pulls from environment variables sourced in navoptenv.sh; pulls latest autoscale configuration
if [ "x$SSL_MODE" = "xenabled" ]; then
    j2 /etc/xplain/templates/nginx_ssl.j2 > /etc/nginx/sites-available/${DOMAIN}
else
    j2 /etc/xplain/templates/nginx_no_ssl.j2 > /etc/nginx/sites-available/${DOMAIN}
fi

# Reload nginx 
/usr/sbin/nginx -s reload
