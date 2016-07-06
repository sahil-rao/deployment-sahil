from __future__ import absolute_import


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
            host_statuses.append(self.check_host(host))

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
            color.BLUE, \
            color.BOLD, \
            "Executing checklist: ", self.description, color.END, color.END
        print "\t" * (tabs-1), \
            " ", len(self.health_checks), \
            "checks to execute in the checklist:"

        healthcheck_statuses = []
        for i, healthcheck in enumerate(self.health_checks):
            status = healthcheck.execute(tabs + 1)
            if isinstance(healthcheck, HealthCheck):
                if status is True:
                    print \
                        "\t" * tabs, \
                        str(i+1) + ")", \
                        color.BOLD, color.GREEN, "PASSED", color.END, \
                        ":", \
                        color.BOLD, healthcheck.description, color.END
                else:
                    print \
                        "\t" * tabs, \
                        str(i+1) + ")", \
                        color.BOLD, color.RED, "FAILED", color.END, \
                        ":", \
                        color.BOLD, healthcheck.description, color.END

                for host in healthcheck.hosts:
                    host_msg = healthcheck.host_msgs.get(host, '')
                    if host_msg:
                        host_msg = '\t- {}'.format(host_msg)

                    if healthcheck.check_host(host):
                        print "\t" * (tabs+1), "PASSED\t" + str(host), host_msg
                    else:
                        print "\t" * (tabs+1), "FAILED\t" + str(host), host_msg

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
