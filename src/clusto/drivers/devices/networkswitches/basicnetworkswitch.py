
from clusto.drivers.base import Device
from clusto.drivers.devices.common import PortMixin, IPMixin

class BasicNetworkSwitch(IPMixin, PortMixin, Device):
    """
    Basic network switch driver
    """

    _clusto_type = 'networkswitch'
    _driver_name = 'basicnetworkswitch'


    _portmeta = {'pwr-nema-5' : {'numports':1},
                 'nic-eth' : {'numports':24}}


