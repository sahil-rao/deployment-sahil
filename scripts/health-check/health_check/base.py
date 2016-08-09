from __future__ import absolute_import

from termcolor import colored
import traceback


class color(object):
    """Terminal codes for colors to make things pretty"""

    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# Subclass this to make a new check
class HealthCheck(object):
    description = ""

    def __init__(self, hosts, description=None):
        self.hosts = hosts
        self.host_msgs = {}

        if description is not None:
            self.description = description

    def execute(self, tabs=1):
        """Return True if healthcheck passed on all hosts"""

        host_statuses = []

        for host in self.hosts:
            try:
                status = self.check_host(host)
            except Exception:
                traceback.print_exc()

                status = False

                try:
                    msg = self.host_msgs[host]
                except KeyError:
                    pass
                else:
                    self.host_msgs[host] = 'Error: {}'.format(msg)

            host_statuses.append(status)

        return all(host_statuses)

    def check_host(self, host):
        """Return True if healthcheck passed no host"""
        raise NotImplementedError

    def close(self):
        pass


def _check_host(health_check, *args, **kwargs):
    return health_check.check_host(*args, **kwargs)


# Executes all healthchecks added to the checklist; Checklists may be composed
class HealthCheckList(object):
    def __init__(self, description):
        self.health_checks = []
        self.description = description

    def add_check(self, healthcheck):
        self.health_checks.append(healthcheck)

    def execute(self, tabs=1):
        print ""
        print \
            "\t" * (tabs-1), \
            colored("Executing checklist: ", 'blue', attrs=['bold']), \
            self.description, color.END, color.END

        print "\t" * (tabs-1), \
            " ", len(self.health_checks), \
            "checks to execute in the checklist:"

        healthcheck_statuses = []
        for i, healthcheck in enumerate(self.health_checks):
            if isinstance(healthcheck, HealthCheck):
                status, status_msgs = self._check_hosts(healthcheck)

                print '{} {})'.format("\t" * tabs, i + 1),

                if status:
                    print colored('PASSED', 'green', attrs=['bold']),
                else:
                    print colored('FAILED', 'red', attrs=['bold']),

                print ':', color.BOLD, healthcheck.description, color.END

                for status_msg in status_msgs:
                    print "\t" * (tabs+1), status_msg
            else:
                status = healthcheck.execute(tabs + 1)

            healthcheck_statuses.append(status)

        status = all(healthcheck_statuses)

        if status is True:
            print \
                "\t" * (tabs-1), \
                color.GREEN, color.BOLD, "PASSED", color.END, \
                "Checklist:", \
                color.UNDERLINE + self.description + color.END
        else:
            print "\t" * (tabs-1), \
                color.RED, color.BOLD, "FAILED", color.END, \
                "Checklist:", \
                color.UNDERLINE + self.description + color.END

        return status

    def close(self):
        for health_check in self.health_checks:
            health_check.close()

    def _check_hosts(self, healthcheck):
        status = True
        status_msgs = []

        max_len = max(len(str(host)) for host in healthcheck.hosts)

        for host in healthcheck.hosts:
            hostname = str(host).ljust(max_len)

            msg = ''

            try:
                result = healthcheck.check_host(host)
            except Exception:
                traceback.print_exc()
                status = False

                msg += colored('EXCEPTION', 'red', attrs=['bold'])
            else:
                if result:
                    msg += colored('PASSED', 'green', attrs=['bold'])
                else:
                    status = False
                    msg += colored('FAILED', 'red', attrs=['bold'])

            msg += ' {}'.format(hostname)

            host_msg = healthcheck.host_msgs.get(host, '')
            if host_msg:
                msg += ' - {}'.format(host_msg)

            status_msgs.append(msg)

        return status, status_msgs
