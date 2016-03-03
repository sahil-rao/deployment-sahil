#!/bin/bash

source /usr/local/bin/navoptenv.sh

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Make sure we have SSL certificates if ssl is enabled
if [ "x$SSL_MODE" = "xenabled" ] && ([ ! -f /etc/nginx/ssl/xplain_san_cert.crt ] || [ ! -f /etc/nginx/ssl/san_cloudera_com.key ]); then
    echo "SSL enabled; Nginx cannot start without SSL certificates. Please install SSL certificates." 1>&2
    exit 1
fi

# Copy HTML files to nginx directory
cp /etc/xplain/files/maintenance_off.html /var/www/maintenance_off.html
cp /etc/xplain/files/404.html /var/www/404.html
cp /etc/xplain/files/502.html /var/www/502.html

# Set up nginx environment
rm /etc/nginx/sites-enabled/default
touch /etc/nginx/sites-available/${DOMAIN}
ln -s /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/${DOMAIN}

# Template config files; j2 pulls from environment variables sourced in navoptenv.sh
if [ "x$SSL_MODE" = "xenabled" ]; then
    j2 /etc/xplain/templates/nginx_ssl.j2 > /etc/nginx/sites-available/${DOMAIN}
else
    j2 /etc/xplain/templates/nginx_no_ssl.j2 > /etc/nginx/sites-available/${DOMAIN}
fi

# Set up crontab that dynamically reconfigures upstreams every second
(crontab -l || true; echo "* * * * * PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /bin/bash /usr/local/bin/reload_nginx.sh >>/var/log/reload_nginx.log 2>&1") 2>&1 | grep -v "no crontab" | sort | uniq | crontab -

# Reload nginx 
/usr/sbin/nginx -s reload

# TODO: setup monit









