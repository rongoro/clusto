
from basicnetworkswitch import BasicNetworkSwitch

class Cisco2960(BasicNetworkSwitch):
    _driver_name = 'cisco2960'

    _portmeta = {
        'pwr-nema-5': {'numports': 1},
        'console-serial': {'numports': 1},
        'nic-eth': {'numports': 48},
    }

class Cisco3560(BasicNetworkSwitch):
    _driver_name = 'cisco3560'

    _portmeta = {
        'pwr-nema-5': {'numports': 1},
        'console-serial': {'numports': 1},
        'nic-eth': {'numports': 48},
        'nic-fiber10g': {'numports': 4},
    }

class Cisco4948(BasicNetworkSwitch):
    _driver_name = 'cisco4948'

    _portmeta = {
        'pwr-nema-5': {'numports': 1},
        'console-serial': {'numports': 1},
        'nic-eth': {'numports': 48},
        'nic-fiber10g': {'numports': 2},
    }
