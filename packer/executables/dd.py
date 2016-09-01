import datadog
import json
import requests

_connected = False
_tags = None


def _connect():
    global _connected, _tags

    if _connected:
        return

    with open('/etc/navoptenv.json') as f:
        env = json.load(f)

    datadog.initialize(api_key=env['datadog_api_key'])
    _connected = True

    ec2_instance = requests.get(
        'http://169.254.169.254/latest/dynamic/instance-identity/document'
    ).json()

    _tags = [
        'region:{}'.format(ec2_instance['region']),
        'instance_id:{}'.format(ec2_instance['instanceId']),
        'availability-zone:{}'.format(ec2_instance['availabilityZone']),

        'application:navopt',
        'env:{}'.format(env['cluster']),
        'dbsilo:{}'.format(env['dbsilo']),
        'service:{}'.format(env['service']),
    ]


def create_event(**kwargs):
    _connect()

    if 'tags' not in kwargs:
        kwargs['tags'] = _tags

    return datadog.api.Event.create(**kwargs)


def report(title, text='', master=None, instances=(), **kwargs):
    print title

    lines = []

    for instance in instances:
        host = instance.private_ip_address

        line = ' * {} state:{}'.format(host, instance.state['Name'])

        if master and host == master.address[0]:
            line += ' (master)'

        lines.append(line)

    instances = '\n'.join(lines)

    if text:
        text = '{}\n{}'.format(text, instances)
    else:
        text = instances

    print text

    return create_event(
        title=title,
        text=text,
        **kwargs)


class Error(Exception):
    def __init__(self, title, text='', alert_type='error', **kwargs):
        super(Error, self).__init__()

        self.title = title
        self.text = text
        self.alert_type = alert_type
        self.kwargs = kwargs

    def __str__(self):
        return self.text

    def report(self):
        report(
            title='Failed joining Redis cluster: {}'.format(self.title),
            text=self.text,
            alert_type=self.alert_type,
            **self.kwargs)
