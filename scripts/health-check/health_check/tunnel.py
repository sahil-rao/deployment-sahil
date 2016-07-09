import sshtunnel
import time


class Tunnel(object):
    def __init__(self, bastion, host, port):
        self.bastion = bastion
        self.host = host
        self.port = port

        self.tunnel = sshtunnel.SSHTunnelForwarder(
            bastion,
            remote_bind_address=(host, port),
            mute_exceptions=True)

        self.tunnel.start()
#        self.tunnel.check_local_side_of_tunnels()

#        for i in xrange(1):
#            if self.tunnel.is_use_local_check_up:
#                break
#            else:
#                time.sleep(1)
#        else:
#            self.tunnel.close()

    def close(self):
        self.tunnel.close()

    def __del__(self):
        self.close()

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)

    def __hash__(self):
        return hash(self.host)
