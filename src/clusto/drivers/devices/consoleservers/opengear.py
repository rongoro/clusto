from basicconsoleserver import BasicConsoleServer
from clusto.exceptions import ConnectionException
from clusto.drivers import IPManager

from subprocess import Popen

class OpenGearCM4148(BasicConsoleServer):

    _driver_name = 'opengearcm4148'

    _portmeta = { 'pwr-nema-5' : { 'numports':1, },
                  'nic-eth' : { 'numports':1, },
                  'console-serial' : { 'numports':48, },
                  }

    def connect(self, porttype, num, ssh_user='root'):
        if porttype != 'console-serial':
            raise DriverException("Cannot connect to a non-serial port")

        host = IPManager.get_ips(self)
        if len(host) == 0:
            host = self.name
        else:
            host = host[0]

        proc = Popen(['ssh', '-p', str(num + 3000), '-l', ssh_user, host])
        proc.communicate()
