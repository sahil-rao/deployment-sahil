# Set up crontabs for Route53 registration and backups
* * * * * root /bin/bash /usr/local/bin/register_host.sh >>/var/log/register_host.log 2>&1

# Set up hourly backup crontab
*/30 * * * * root /bin/bash /usr/local/bin/take_snapshot.sh >>/var/log/take_snapshot.log 2>&1
