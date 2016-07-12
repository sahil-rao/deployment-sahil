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
        for mount, percent_full in self.host_mounts[host].iteritems():
            self.host_msgs[host] = '{}%'.format(percent_full)

            if percent_full > 80:
                return False

        return True


def _check_host(bastion, host):
    with ssh.connect(bastion) as client:
        stdin, stdout, stderr = client.exec_command(
            "ssh {} df -hP | "
            "awk 'NR>1{{print $1,$5}}' | "
            "sed -e's/%//g'".format(pipes.quote(host))
        )

        mounts = {}

        for line in stdout.readlines():
            mount, percent_full = line.strip().split()
            mounts[mount] = int(percent_full)

        return host, mounts
