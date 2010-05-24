from basicappliance import BasicAppliance

class Netscaler(BasicAppliance):
    pass

class Netscaler17000(Netscaler):
    _driver_name = 'netscaler17000'

    _portmeta = { 'pwr-nema-5': { 'numports':2, },
                  'nic-eth': { 'numports': 9, },
                  'nic-xfp': { 'numports': 2, },
                  'console-serial': { 'numports': 1, },
                }

class Netscaler10010(Netscaler):
    _driver_name = 'netscaler10010'

    _portmeta = {   'pwr-nema-5': { 'numports': 2 },
                    'nic-eth': { 'numports': 9 },
                    'console-serial': { 'numports': 1 },
                }
