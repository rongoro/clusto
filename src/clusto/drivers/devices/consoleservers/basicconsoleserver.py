
from clusto.drivers import Device
from clusto.drivers.devices import PortMixin, IPMixin

class BasicConsoleServer(IPMixin, PortMixin, Device):
    """
    Basic console server Driver
    """

    _clusto_type = 'consoleserver'
    _driver_name = 'basicconsoleserver'

    
    _portmeta = { 'pwr-nema-5' : { 'numports':1, },
                  'nic-eth' : { 'numports':1, },
                  'console-serial' : { 'numports':24, },
                  }

    def connect(self, port, num):
        raise NotImplemented
