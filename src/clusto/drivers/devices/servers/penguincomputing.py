"""
Drivers for Penguin Computing Servers
"""

from basicserver import BasicServer

class PenguinServer(BasicServer):
    _driver_name = "penguinserver"

class PenguinServer2U(PenguinServer):
    _driver_name = "penguinserver2u"
    _portmeta = {'pwr-nema-5': {'numports': 2},
                 'nic-eth': {'numports': 2},
                 'console-serial': {'numports': 1}}
    rack_units = 2
