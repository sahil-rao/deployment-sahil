from __future__ import absolute_import

from . import ssh
from .base import HealthCheck
import functools
import multiprocessing.pool
import pipes


class DiskUsageCheck(HealthCheck):
    description = "Disk usage on all drives is < 80%"

    def __init__(self, bastion, *args, **kwargs):
        super(DiskUsageCheck, self).__init__(*args, **kwargs)

        pool = multiprocessing.pool.ThreadPool(5)

        try:
            self.host_mounts = {}
            for host, mounts in pool.map(
                    functools.partial(_check_host, bastion),
                    self.hosts):
                self.host_mounts[host] = mounts
        finally:
            pool.close()
            pool.join()

    def check_host(self, host):
        result = True
        max_full = None

        for mount, percent_full in self.host_mounts[host].iteritems():
            max_full = max(max_full or 0, percent_full)
            if percent_full > 80:
                result = False

        if max_full is None:
            self.host_msgs[host] = 'no mount disk usage?'
            return False

        self.host_msgs[host] = '{}%'.format(max_full)

        return result


def _check_host(bastion, host):
    with ssh.connect(bastion) as client:
        cmd = "ssh {} df -hP | " \
            "awk 'NR>1{{print $1,$5}}' | " \
            "sed -e's/%//g'".format(pipes.quote(host))

        stdin, stdout, stderr = client.exec_command(cmd)

        stdout_lines = stdout.readlines()

        mounts = {}

        for line in stdout_lines:
            mount, percent_full = line.strip().split()
            mounts[mount] = int(percent_full)

        return host, mounts
