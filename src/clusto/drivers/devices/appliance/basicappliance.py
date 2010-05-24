
from clusto.drivers import Device
from clusto.drivers.devices import PortMixin, IPMixin

class BasicAppliance(IPMixin, PortMixin, Device):
    """
    Basic appliance Driver
    """

    _clusto_type = 'appliance'
    _driver_name = 'basicappliance'

    
    _portmeta = { 'pwr-nema-5' : { 'numports':2, },
                  'nic-eth' : { 'numports':1, },
                  'console-serial' : { 'numports':1, },
                  }
