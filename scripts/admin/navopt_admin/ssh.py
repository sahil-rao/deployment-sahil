from __future__ import absolute_import

import logging
import os
import shutil
import subprocess
import tempfile

LOG = logging.getLogger(__name__)
DEVNULL = open(os.devnull, 'wb')
BASE_PORTS = 14000


class Bastion(object):
    def __init__(self, bastion, local_host='localhost'):
        self._bastion = bastion
        self._base_port = BASE_PORTS
        self._local_host = local_host

        self._tempdir = tempfile.mkdtemp()
        self._control_socket = os.path.join(self._tempdir, 'control_socket')

        cmd = [
            'ssh',
            self._bastion,
            '-qNf',
            '-MS', self._control_socket,
            '-o', 'ControlPersist=30s',
        ]

        LOG.debug('running: %s', ' '.join(cmd))

        subprocess.check_call(cmd)

    def close(self):
        self._ssh_cmd('exit')

        if self._tempdir:
            shutil.rmtree(self._tempdir)

    def __del__(self):
        if hasattr(self, '_control_socket'):
            self.close()

    def tunnel(self, remote_host, remote_port):
        while True:
            local_port = self._base_port
            self._base_port += 1

            if self._base_port >= BASE_PORTS + 100:
                raise Exception('out of ports')

            forwards = [
                '-L', '{}:{}:{}:{}'.format(
                    self._local_host,
                    local_port,
                    remote_host,
                    remote_port,
                ),
            ]

            try:
                self._ssh_cmd('forward', *forwards)
            except subprocess.CalledProcessError:
                pass
            else:
                return Tunnel(self, forwards, self._local_host, local_port)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _ssh_cmd(self, *args):
        if self._control_socket and os.path.exists(self._control_socket):
            cmd = [
                'ssh',
                '-q',
                '-S', self._control_socket,
                '-O',
            ]
            cmd.extend(args)
            cmd.append('x')

            LOG.debug('running: %s', ' '.join(cmd))

            subprocess.check_call(cmd, stdout=DEVNULL, stderr=DEVNULL)


class Tunnel(object):
    def __init__(self, bastion, forwards, local_host, local_port):
        self._bastion = bastion
        self._forwards = forwards
        self.local_host = local_host
        self.local_port = local_port

    def close(self):
        self._bastion._ssh_cmd('cancel', *self._forwards)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
