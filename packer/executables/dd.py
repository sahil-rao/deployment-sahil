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
