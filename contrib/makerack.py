#!/usr/bin/env python
from clusto.scripthelpers import init_script
from clusto.drivers import *
from socket import gethostbyname
from optparse import OptionParser
import clusto
import sys
import re

POWER_PORTMAP = {
    1: 'bb1', 2: 'bb2', 3: 'bb3', 4: 'bb4', 5: 'bb5',
    6: 'ba1', 7: 'ba2', 8: 'ba3', 9: 'ba4', 10: 'ba5',
    11: 'ab1', 12: 'ab2', 13: 'ab3', 14: 'ab4', 15: 'ab5',
    16: 'aa1', 17: 'aa2', 18: 'aa3', 19: 'aa4', 20: 'aa5',
}

SWITCH_TYPES = {
    'cisco2960': Cisco2960,
    'cisco3560': Cisco3560,
    'cisco4948': Cisco4948,
}

def ensure_vlan(vlanid, network, netmask):
    name = 'vlan-%i' % vlanid
    try:
        manager = clusto.get_by_name(name)
    except LookupError:
        manager = IPManager(name, baseip=network, netmask=netmask)
        manager.set_attr('vlan', vlanid)
    return manager

def bind_dns_ip_to_osport(obj, osport, porttype=None, portnum=None, domain='digg.internal'):
    ip = gethostbyname('%s.%s' % (obj.name, domain))
    obj.bind_ip_to_osport(ip, osport, porttype=porttype, portnum=portnum)

if __name__ == '__main__':
    op = OptionParser(usage='usage: %prog [options] <rack name>')
    op.add_option('-s', '--switch',
        action='store', type='string', dest='switchtype', default='cisco4948',
        help='Switch type in rack. (%s)' % ', '.join(SWITCH_TYPES.keys()))
    op, args = op.parse_args()

    if len(args) < 1:
        print 'Rack name is required'
        sys.exit(0)

    match = re.match('^([a-z0-9]+)-([0-9]+)$', args[0])
    if not match:
        print 'Invalid rack name (eg. sjc1-000)'
        sys.exit(0)

    init_script()

    clusto.begin_transaction()

    # Make sure we can allocate server names
    try:
        servernames = clusto.get_by_name('servernames')
    except LookupError:
        servernames = SimpleEntityNameManager('servernames', basename='s', digits=4)
        servernames.next = 1000

    # Make sure all the IPManager instances exist
    ensure_vlan(243, '10.2.128.0', '255.255.252.0')
    ensure_vlan(242, '10.2.0.0', '255.255.252.0')
    ensure_vlan(442, '10.0.0.0', '255.255.252.0')
    try:
        vpnsubnet = clusto.get_by_name('vpnsubnet')
    except LookupError:
        vpnsubnet = IPManager('vpnsubnet', baseip='10.2.16.0', netmask='255.255.248.0')
    try:
        dmzsubnet = clusto.get_by_name('subnet-dmz1')
    except LookupError:
        dmzsubnet = IPManager('subnet-dmz1', baseip='64.191.203.32', netmask='255.255.255.224')
    
    rackname = args[0]
    datacenter, racknum = match.groups()

    # Create all the basic stuff
    datacenter = clusto.get_or_create(datacenter, EquinixDatacenter)
    rack = clusto.get_or_create(rackname, APCRack)
    switch = clusto.get_or_create(rackname + '-sw1', SWITCH_TYPES[op.switchtype])
    power = clusto.get_or_create(rackname + '-pwr1', PowerTowerXM)
    console = clusto.get_or_create(rackname + '-ts1', OpenGearCM4148)
    servernames = clusto.get_or_create('servernames', SimpleEntityNameManager)

    if not rack in datacenter:
        datacenter.insert(rack)

    # Wire up the power strip
    if not power in rack:
        rack.insert(power, 29)
    if power.port_free('nic-eth', 1):
        power.connect_ports('nic-eth', 1, switch, 44)
    if power.port_free('console-serial', 1):
        power.connect_ports('console-serial', 1, console, 44)

    # Wire up the switch
    if not switch in rack:
        rack.insert(switch, 31)
    if switch.port_free('pwr-nema-5', 1):
        switch.connect_ports('pwr-nema-5', 1, power, 'aa8')
    if switch.port_free('console-serial', 1):
        switch.connect_ports('console-serial', 1, console, 48)

    # Wire up the console server
    if not console in rack:
        rack.insert(console, 30)
    if console.port_free('pwr-nema-5', 1):
        console.connect_ports('pwr-nema-5', 1, power, 'ab8')
    if console.port_free('nic-eth', 1):
        console.connect_ports('nic-eth', 1, switch, 43)

    # Assign IPs to basic devices
    bind_dns_ip_to_osport(switch, 'Vlan442')
    bind_dns_ip_to_osport(console, 'nic0', porttype='nic-eth', portnum=1)
    bind_dns_ip_to_osport(power, 'nic0', porttype='nic-eth', portnum=1)

    clusto.commit()

    sys.exit(0)

    # Create 20 servers, skipping every 6th
    for ru in range(1, 24):
        if (ru % 6) == 0: continue

        server = rack.get_device_in(ru)
        if not server:
            server = servernames.allocate(PenguinServer)

        if not server in rack:
            rack.insert(server, ru)

        portnum = ru - (ru / 6)
        if server.port_free('pwr-nema-5', 1):
            server.connect_ports('pwr-nema-5', 1, power, POWER_PORTMAP[portnum])
        if server.port_free('console-serial', 1):
            server.connect_ports('console-serial', 1, console, portnum)
        if server.port_free('nic-eth', 1):
            server.connect_ports('nic-eth', 1, switch, portnum)
        if server.port_free('nic-eth', 2):
            server.connect_ports('nic-eth', 2, switch, portnum + 20)
