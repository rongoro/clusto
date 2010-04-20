from clusto.drivers import BasicDatacenter, BasicRack, BasicServer, BasicVirtualServer, BasicNetworkSwitch, PowerTowerXM, IPManager, OpenGearCM4148
from clusto.scripthelpers import get_clusto_config
import clusto

from traceback import format_exc
from subprocess import Popen, PIPE, STDOUT
from xml.etree import ElementTree
from os.path import exists
from pprint import pprint
import yaml
import socket
import sys
import re

from discovery import *

def get_environment(dc, rack, switch):
    dc = get_or_create(BasicDatacenter, dc)
    rack = get_or_create(BasicRack, rack)
    switch = get_or_create(BasicNetworkSwitch, switch)
    pwr = get_or_create(PowerTowerXM, '%s-pwr1' % rack.name)
    ts = get_or_create(OpenGearCM4148, '%s-ts1' % rack.name)

    if not rack in dc:
        dc.insert(rack)
    if not switch in rack:
        rack.insert(switch, 31)
    if not pwr in rack:
        rack.insert(pwr, (28, 29))
    if not ts in rack:
        rack.insert(ts, 30)

    if switch.port_free('pwr-nema-5', 0):
        switch.connect_ports('pwr-nema-5', 0, pwr, '.aa8')
    if ts.port_free('pwr-nema-5', 0):
        ts.connect_ports('pwr-nema-5', 0, pwr, '.ab8')

    clusto.commit()

    simple_ipbind(switch)
    simple_ipbind(ts)

    return (dc, rack, switch, pwr, ts)

def import_ipmac(name, macaddr, ipaddr, portnum):
    '''
    Insert or update a server in clusto
    '''

    # Get the basic datacenter, rack, and switch objects
    portnum = int(portnum)
    n = name.split('-', 3)
    switch_name = '-'.join(n)
    rack_name = '-'.join(n[:-1])
    dc_name = n[:-2][0]

    dc, rack, switch, pwr, ts = get_environment(dc_name, rack_name, switch_name)

    # Find the server's hostname and query clusto for it. If the server does not
    # exist, create it. Returns None if something went wrong.
    if not ipaddr:
        return
    server = get_server(ipaddr)

    if not server:
        return

    pprint(server)

    if server.driver == 'basicvirtualserver':
        if not server.has_attr('switchport'):
            server.add_attr('switchport', '%s,%s' % (rack.name, portnum))
            clusto.commit()
        return

    if not server in rack:
        rack.insert(server, SWITCHPORT_TO_RU[portnum])

    ru = rack.get_rack_and_u(server)['RU'][0]
    if server.port_free('pwr-nema-5', 0):
        server.connect_ports('pwr-nema-5', 0, pwr, RU_TO_PWRPORT[ru])
    if server.port_free('console-serial', 0):
        server.connect_ports('console-serial', 0, ts, RU_TO_SWITCHPORT[ru])

    if portnum < 21:
        ifnum = 0
    else:
        ifnum = 1

    if not server.port_free('nic-eth', ifnum):
        if not server.get_connected('nic-eth', ifnum) == switch:
            server.disconnect_port('nic-eth', ifnum)
            server.connect_ports('nic-eth', ifnum, switch, portnum)
    else:
        server.connect_ports('nic-eth', ifnum, switch, portnum)

    ifaces = discover_interfaces(ipaddr)
    for name in ifaces:
        if name == 'lo':
            continue
        n = ifaces[name]
        if not 'inet addr' in n:
            continue

        match = re.match('(?P<porttype>[a-z]+)(?P<num>[0-9]*)', name)
        if not match:
            print 'Unable to comprehend port name: %s' % name
            continue

        match = match.groupdict()
        if not match['num']:
            num = 0
        else:
            num = int(match['num'])
        porttype = match['porttype']

        #subnet.allocate(server, n['inet addr'])
        subnet = IPManager.get_ip_manager(n['inet addr'])
        if not server in subnet.owners(n['inet addr']):
            server.bindIPtoPort(n['inet addr'], 'nic-%s' % porttype, num)
        server.set_port_attr('nic-%s' % porttype, num, 'mac-address', n['hwaddr'])

    if not 'uniqueid' in server.attr_keys():
        for key, value in get_facts(ipaddr):
            if key == 'fqdn': continue
            server.add_attr(key, value)

    clusto.commit()

def bind_vservers():
    for vserver in clusto.get_entities(clustodrivers=(BasicVirtualServer,)):
        switchport = vserver.attrs('switchport')
        if not switchport: continue
        print 'Binding', repr(vserver)
        switchport = switchport[0]
        rack_name, portnum = switchport.value.rsplit(',', 1)
        portnum = int(portnum)
        rack = clusto.get_by_name(rack_name)
        switch = clusto.get_by_name(rack_name + '-sw1')
        print repr(switch)
        for device in rack.contents():
            if device.driver == 'basicserver':
                server = device
                conn = server.port_info['nic-eth'][0]
                if conn['connection'] == switch and conn['otherportnum'] == portnum:
                    if not vserver in server:
                        server.insert(vserver)
                    print 'Bound %s to %s' % (vserver.name, server.name)

def main():
    if len(sys.argv) > 1:
        if not exists(sys.argv[1]):
            print 'File %s does not exist.' % sys.argv[1]
            return
        fd = file(sys.argv[1], 'r')
    else:
        fd = sys.stdin

    for line in fd.readlines():
        switch, macaddr, ipaddr, port = line.rstrip('\n').split(';', 3)
        print switch
        try:
            import_ipmac(switch, macaddr, ipaddr, port)
        except:
            print format_exc()
    #bind_vservers()
    #pprint(clusto.get_entities())

if __name__ == '__main__':
    config = get_clusto_config()
    clusto.connect(config.get('clusto', 'dsn'))
    clusto.init_clusto()
    main()
