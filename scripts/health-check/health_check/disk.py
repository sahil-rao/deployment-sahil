from __future__ import absolute_import

from health_check.base import HealthCheck
import os
import paramiko


class DiskUsageCheck(HealthCheck):
    def __init__(self, bastion, *args, **kwargs):
        super(DiskUsageCheck, self).__init__(*args, **kwargs)

        self.bastion = bastion
        self.description = "Disk usage on all drives is < 80%"

    def check_host(self, host):
        config_file = os.path.expanduser('~/.ssh/config')

        if os.path.exists(config_file):
            with open(config_file) as f:
                config = paramiko.SSHConfig()
                config.parse(f)
                o = config.lookup(self.bastion)
                kwargs = {
                        'hostname': o['hostname'],
                        'username': o['user'],
                        'key_filename': o['identityfile']
                }
        else:
            kwargs = {'hostname': self.bastion}

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(**kwargs)
        stdin, stdout, stderr = client.exec_command(
                "ssh {} df -hP | awk 'NR>1{{print $1,$5}}' | sed -e's/%//g'".format(host)
        )

        for line in stdout.readlines():
            drive, percent_full = line.strip().split()
            self.host_msgs[host] = '{}%'.format(percent_full)

            if int(percent_full) > 80:
                return False

        return True
