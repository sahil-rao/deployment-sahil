from __future__ import absolute_import

import logging
import os
import pipes
import re
import subprocess
from .exponential_decay import exponential_decay

LOG = logging.getLogger(__name__)
DEVNULL = open(os.devnull, 'wb')
BASE_PORTS = 14000


class BaseBastion(object):
    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def tunnel(self, remote_host, remote_port):
        raise NotImplementedError

    def resolve_hostname(self, hostname):
        raise NotImplementedError


class Bastion(BaseBastion):
    def __init__(self, bastion, local_host='localhost'):
        self._bastion = bastion
        self._base_port = BASE_PORTS
        self._local_host = local_host

    def close(self):
        pass

    def tunnel(self, remote_host, remote_port):
        while True:
            local_port = self._base_port
            self._base_port += 1

            if self._base_port >= BASE_PORTS + 100:
                raise Exception('out of ports')

            if _port_is_listening(self._local_host, local_port):
                continue

            cmd = [
                'ssh',
                '-qN',
                '-o', 'ControlMaster=no',
                '-o', 'StrictHostKeyChecking=no',
                '-S', 'none',
                '-L', '{}:{}:{}'.format(local_port, remote_host, remote_port),
                remote_host,
            ]
            LOG.debug('running: %s', ' '.join(cmd))

            process = subprocess.Popen(cmd,
                                       stdout=DEVNULL,
                                       stderr=DEVNULL,
                                       stdin=subprocess.PIPE)

            return ProcessTunnel(process, self._local_host, local_port)

    def resolve_hostname(self, hostname):
        cmd = [
            'ssh',
            '-q',
            '-o', 'StrictHostKeyChecking=no',
            self._bastion,
            'host', pipes.quote(hostname)]
        LOG.debug('running: %s', ' '.join(cmd))

        stdout = subprocess.check_output(cmd).strip()

        m = re.search('^.* has address (.*)$', stdout, re.MULTILINE)
        if m:
            return m.group(1)
        else:
            return None


class NoopBastion(BaseBastion):
    def tunnel(self, remote_host, remote_port):
        return NoopTunnel(remote_host, remote_port)

    def resolve_hostname(self, hostname):
        cmd = ['host', pipes.quote(hostname)]
        LOG.debug('running: %s', ' '.join(cmd))

        stdout = subprocess.check_output(cmd).strip()

        m = re.match('.* has address (.*)$', stdout)
        if m:
            return m.group(1)
        else:
            return None


class BaseTunnel(object):
    def __init__(self, host, port):
        self._opened = False
        self.host = host
        self.port = port

    def open(self):
        LOG.debug('opening %s:%s' % (self.host, self.port))

        if self._opened:
            LOG.debug('%s:%s is already open' % (self.host, self.port))
            return

        LOG.debug('waiting for port %s:%s to start listening' %
                  (self.host, self.port))

        # Wait for the port to be created
        for _ in exponential_decay(10.0):
            if self.check_if_listening():
                break
        else:
            self.close()
            raise Exception('ssh failed to open %s:%s' % (self.host, self.port))

        LOG.debug('ssh tunnel is now listening on port %s' % self.port)

        self._opened = True

    def check_if_listening(self):
        return _port_is_listening(self.host, self.port)

    def close(self):
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class ProcessTunnel(BaseTunnel):
    def __init__(self, process, host, port):
        super(ProcessTunnel, self).__init__(host, port)
        self._process = process
        self._closed = False

    def check_if_listening(self):
        if super(ProcessTunnel, self).check_if_listening():
            return True

        # Check if ssh died
        if self._process.poll() != None:
            raise Exception(
                'ssh died while connecting to port %s' % self.port)

        return False

    def close(self):
        if self._closed:
            False

        status = self._process.poll()

        if status is not None:
            return

        self._process.stdin.close()
        self._process.terminate()

        for _ in exponential_decay(10.0):
            status = self._process.poll()

            if status is not None:
                break
        else:
            LOG.error(
                'ssh failed to shutdown for %s:%s' % (self.host, self.port))
            self._process.kill()

        self._process.wait()
        self._closed = True


class NoopTunnel(BaseTunnel):
    def __init__(self, host, port):
        super(NoopTunnel, self).__init__(host, port)


def _port_is_listening(host, port):
    cmd = ['nc', '-z', pipes.quote(host), pipes.quote(str(port))]
    # LOG.debug('running: %s' % ' '.join(cmd))

    process = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)
    process.communicate()
    return process.returncode == 0
