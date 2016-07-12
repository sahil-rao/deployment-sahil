from . import ssh
import sshtunnel
import time
import pipes


class Tunnel(object):
    def __init__(self, bastion, host, port):
        self.bastion = bastion
        self.host = host
        self.port = port

        # Only create the tunnel if the process is up.
        with ssh.connect(bastion) as client:
            command = 'nc -z {} {}'.format(
                pipes.quote(host),
                pipes.quote(str(port)))

            stdin, stdout, stderr = client.exec_command(command)

            if stdout.channel.recv_exit_status() == 0:
                self.tunnel = sshtunnel.SSHTunnelForwarder(
                    bastion,
                    remote_bind_address=(host, port),
                    mute_exceptions=True)

                self.tunnel.start()
            else:
                self.tunnel = None

    def close(self):
        if self.tunnel is not None:
            self.tunnel.close()

    #def __del__(self):
    #    self.close()

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)


    def __repr__(self):
        return '{}({!r}, {!r}, {!r})'.format(
            self.__class__.__name__,
            self.bastion,
            self.host,
            self.port)

    def __hash__(self):
        return hash(self.host)

    def __cmp__(self, other):
        return cmp(
            (self.host, self.port),
            (other.host, other.port))
