from socket import gethostbyname

from clusto.scripthelpers import init_script
from clusto.drivers import *
import clusto

def get_factory(name, layout=None):
    if not layout:
        rack = clusto.get_by_name(name)
        layout = rack.attr_value(key='racklayout')
    return LAYOUTS[str(layout)](name, rack.parents(clusto_types=['datacenter']))

class RackFactory(object):
    def bind_dns_ip_to_osport(self, obj, osport, porttype=None, portnum=None, domain='digg.internal'):
        ip = gethostbyname('%s.%s' % (obj.name, domain))
        obj.bind_ip_to_osport(ip, osport, porttype=porttype, portnum=portnum)

class Digg201001RackFactory(RackFactory):
    LAYOUT_NAME = '201001'

    SWITCHPORT_TO_RU = {
        1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11,
        12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20,
        21: 21, 22: 22, 23: 23,
        24: 25, 25: 26, 26: 27, 27: 28, 28: 29, 29: 30, 30: 31
    }
    SWITCHPORT_TO_PWR = {
        1: 'bb1', 2: 'bb2', 3: 'bb3', 4: 'bb4', 5: 'bb5', 6: 'bb6', 7: 'bb7',
        8: 'bb8', 9: 'ba1', 10: 'ba2', 11: 'ba3', 12: 'ba4', 13: 'ba5',
        14: 'ba6', 15: 'ba7', 16: 'ba8', 17: 'ab1', 18: 'ab2', 19: 'ab3',
        20: 'ab4', 21: 'ab5', 22: 'ab6', 23: 'ab7', 24: 'aa1', 25: 'aa2',
        26: 'aa3', 27: 'aa4', 28: 'aa5', 29: 'aa6', 30: 'aa7'
    }

    def __init__(self, name, datacenter):
        self.datacenter = datacenter
        self.rack = clusto.get_or_create(name, APCRack)
        self.switch = clusto.get_or_create(name + '-sw1', Cisco4948)
        self.console = clusto.get_or_create(name + '-ts1', OpenGearCM4148)
        self.power = clusto.get_or_create(name + '-pwr1', PowerTowerXM)

    def connect_ports(self):
        self.rack.set_attr(key='racklayout', value=self.LAYOUT_NAME)

        if not self.rack in self.datacenter:
            self.datacenter.insert(self.rack)

        if not self.power in self.rack:
            self.rack.insert(self.power, 41)
        if self.power.port_free('nic-eth', 1):
            self.power.connect_ports('nic-eth', 1, self.switch, 44)
        if self.power.port_free('console-serial', 1):
            self.power.connect_ports('console-serial', 1, self.console, 44)

        if not self.switch in self.rack:
            self.rack.insert(self.switch, 36)
        if self.switch.port_free('pwr-nema-5', 1):
            self.switch.connect_ports('pwr-nema-5', 1, self.power, 'aa8')
        if self.switch.port_free('console-serial', 1):
            self.switch.connect_ports('console-serial', 1, self.console, 48)

        if not self.console in self.rack:
            self.rack.insert(self.console, 34)
        if self.console.port_free('pwr-nema-5', 1):
            self.console.connect_ports('pwr-nema-5', 1, self.power, 'ab8')
        if self.console.port_free('nic-eth', 1):
            self.console.connect_ports('nic-eth', 1, self.switch, 43)

        self.bind_dns_ip_to_osport(self.switch, 'Vlan442')
        self.bind_dns_ip_to_osport(self.console, 'nic0', porttype='nic-eth', portnum=1)
        self.bind_dns_ip_to_osport(self.power, 'nic0', porttype='nic-eth', portnum=1)

    def add_server(self, server, switchport):
        if not server in self.rack:
            self.rack.insert(server, self.SWITCHPORT_TO_RU[switchport])
        if server.port_free('nic-eth', 1):
            server.connect_ports('nic-eth', 1, self.switch, switchport)
        if server.port_free('pwr-nema-5', 1):
            server.connect_ports('pwr-nema-5', 1, self.power, self.SWITCHPORT_TO_PWR[switchport])
        if server.port_free('console-serial', 1):
            server.connect_ports('console-serial', 1, self.console, switchport)

class Digg5555RackFactory(RackFactory):
    LAYOUT_NAME = '5555'

    SWITCHPORT_TO_RU = {
        1:1, 2:2, 3:3, 4:4, 5:5,
        6:7, 7:8, 8:9, 9:10, 10:11,
        11:13, 12:14, 13:15, 14:16, 15:17,
        16:19, 17:20, 18:21, 19:22, 20:23,

        21:1, 22:2, 23:3, 24:4, 25:5,
        26:7, 27:8, 28:9, 29:10, 30:11,
        31:13, 32:14, 33:15, 34:16, 35:17,
        36:19, 37:20, 38:21, 39:22, 40:23,
    }

    SWITCHPORT_TO_PWR = {
        1: 'bb1', 2: 'bb2', 3: 'bb3', 4: 'bb4', 5: 'bb5',
        6: 'ba1', 7: 'ba2', 8: 'ba3', 9: 'ba4', 10: 'ba5',
        11: 'ab1', 12: 'ab2', 13: 'ab3', 14: 'ab4', 15: 'ab5',
        16: 'aa1', 17: 'aa2', 18: 'aa3', 19: 'aa4', 20: 'aa5',
    }

    def __init__(self, name, datacenter):
        self.datacenter = datacenter
        self.rack = clusto.get_or_create(name, APCRack)
        self.switch = clusto.get_or_create(name + '-sw1', Cisco4948)
        self.console = clusto.get_or_create(name + '-ts1', OpenGearCM4148)
        self.power = clusto.get_or_create(name + '-pwr1', PowerTowerXM)

    def connect_ports(self):
        self.rack.set_attr(key='racklayout', value=self.LAYOUT_NAME)

        if not self.rack in self.datacenter:
            self.datacenter.insert(self.rack)

        if not self.power in self.rack:
            self.rack.insert(self.power, 29)
        if self.power.port_free('nic-eth', 1):
            self.power.connect_ports('nic-eth', 1, self.switch, 44)
        if self.power.port_free('console-serial', 1):
            self.power.connect_ports('console-serial', 1, self.console, 44)

        if not self.switch in self.rack:
            self.rack.insert(self.switch, 31)
        if self.switch.port_free('pwr-nema-5', 1):
            self.switch.connect_ports('pwr-nema-5', 1, self.power, 'aa8')
        if self.switch.port_free('console-serial', 1):
            self.switch.connect_ports('console-serial', 1, self.console, 48)

        if not self.console in self.rack:
            self.rack.insert(self.console, 30)
        if self.console.port_free('pwr-nema-5', 1):
            self.console.connect_ports('pwr-nema-5', 1, self.power, 'ab8')
        if self.console.port_free('nic-eth', 1):
            self.console.connect_ports('nic-eth', 1, self.switch, 43)

        self.bind_dns_ip_to_osport(self.switch, 'Vlan442')
        self.bind_dns_ip_to_osport(self.console, 'nic0', porttype='nic-eth', portnum=1)
        self.bind_dns_ip_to_osport(self.power, 'nic0', porttype='nic-eth', portnum=1)

    def add_server(self, server, switchport):
        if switchport > 20:
            switchport -= 20

        if not server in self.rack:
            self.rack.insert(server, self.SWITCHPORT_TO_RU[switchport])
        if server.port_free('nic-eth', 1):
            server.connect_ports('nic-eth', 1, self.switch, switchport)
        if server.port_free('nic-eth', 2):
            server.connect_ports('nic-eth', 2, self.switch, switchport + 20)
        if server.port_free('pwr-nema-5', 1):
            server.connect_ports('pwr-nema-5', 1, self.power, self.SWITCHPORT_TO_PWR[switchport])
        if server.port_free('console-serial', 1):
            server.connect_ports('console-serial', 1, self.console, switchport)

class Digg4444RackFactory(Digg5555RackFactory):
    LAYOUT_NAME = '4444'


LAYOUTS = {}

for factory in [Digg4444RackFactory, Digg5555RackFactory, Digg201001RackFactory]:
    LAYOUTS[factory.LAYOUT_NAME] = factory
