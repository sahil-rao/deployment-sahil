import paramiko
import os


def connect(hostname):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = get_config(hostname)
    client.connect(**kwargs)

    return client


def get_config(hostname):
    config_file = os.path.expanduser('~/.ssh/config')

    d = {'hostname': hostname}

    if os.path.exists(config_file):
        with open(config_file) as f:
            config = paramiko.SSHConfig()
            config.parse(f)
            o = config.lookup(hostname)

            for dst_key, src_key in (
                    ('hostname', 'hostname'),
                    ('username', 'user'),
                    ('key_filename', 'identityfile')):
                try:
                    d[dst_key] = o[src_key]
                except KeyError:
                    pass

    return d
