from __future__ import absolute_import

from health_check.base import HealthCheck
import functools
import multiprocessing
import os
import paramiko


class DiskUsageCheck(HealthCheck):
    description = "Disk usage on all drives is < 80%"

    def __init__(self, bastion, *args, **kwargs):
        super(DiskUsageCheck, self).__init__(*args, **kwargs)

        pool = multiprocessing.Pool(5)

        self.host_mounts = {}
        for host, mounts in pool.map(
                functools.partial(_check_host, bastion),
                self.hosts):
            self.host_mounts[host] = mounts

    def check_host(self, host):
        for mount, percent_full in self.host_mounts[host].iteritems():
            self.host_msgs[host] = '{}%'.format(percent_full)

            if percent_full > 80:
                return False

        return True


def _check_host(bastion, host):
    config_file = os.path.expanduser('~/.ssh/config')

    if os.path.exists(config_file):
        with open(config_file) as f:
            config = paramiko.SSHConfig()
            config.parse(f)
            o = config.lookup(bastion)
            kwargs = {
                    'hostname': o['hostname'],
                    'username': o['user'],
                    'key_filename': o['identityfile']
            }
    else:
        kwargs = {'hostname': bastion}

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(**kwargs)
    stdin, stdout, stderr = client.exec_command(
        "ssh {} df -hP | "
        "awk 'NR>1{{print $1,$5}}' | "
        "sed -e's/%//g'".format(host)
    )

    mounts = {}

    for line in stdout.readlines():
        mount, percent_full = line.strip().split()
        mounts[mount] = int(percent_full)

    return host, mounts
