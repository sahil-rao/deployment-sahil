from .base import HealthCheck


class AWSNameHealthCheck(HealthCheck):
    description = "Instances have the same name"

    def __init__(self, instances):
        hostnames = [instance.private_ip_address for instance in instances]
        super(AWSNameHealthCheck, self).__init__(hostnames)

        self.instances = dict(
            (instance.private_ip_address, instance)
            for instance in instances
        )

    def check_host(self, host):
        name = self.get_tag(host, 'Name')
        self.host_msgs[host] = name
        return all(name == self.get_tag(host, 'Name') for host in self.hosts)

    def get_tag(self, host, key):
        instance = self.instances[host]

        for tag in instance.tags:
            if tag['Key'] == key:
                return tag['Value']

        return None
