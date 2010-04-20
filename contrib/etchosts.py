from discovery import discover_interfaces
import clusto
from clusto.scripthelpers import init_script
from clusto.exceptions import ResourceException
from clusto.drivers import PenguinServer, IPManager

import parsearp

from pprint import pprint
import re

def parse_hosts(filename):
    for line in file(filename, 'r'):
        line = line.rstrip('\r\n')
        line = line.replace('\t', ' ')
        if not line: continue
        line = [x for x in line.split(' ') if x]

        entry = []
        comment = ''
        while line:
            x = line[0]
            if x.startswith('#'):
                comment = ' '.join(line)
                break
            entry.append(x)
            line.remove(x)

        if not entry: continue

        ip = entry[0]
        names = entry[1:]
        yield (ip, names, comment.lstrip('# '))

def filter_hosts(hosts):
    pattern = re.compile('^(s|lun)[0-9]{4}$')
    for ip, names, comment in hosts:
        if not ip.startswith('10.2.'): continue
        if not [x for x in names if pattern.match(x)]: continue
        yield (ip, names, comment)

def discover_hosts(hosts):
    ifpattern = re.compile('^eth[0-9]+$')

    for ip, names, comment in hosts:
        server = None
        ifaces = discover_interfaces(ip)

        if not ifaces:
            print 'Unable to discover interfaces on %s (%s)' % (ip, comment)
            continue

        ifaces = [(x, ifaces[x].get('inet addr', None), ifaces[x]['hwaddr'].lower()) for x in ifaces if ifpattern.match(x)]
        ifaces.sort(key=lambda x: x[0])
        yield (ifaces, names, comment)

def main():
    #for ifaces, names, comment in discover_hosts(filter_hosts(parse_hosts('hosts'))):
    for ifaces, names, comment in parsearp.discover_hosts(parsearp.parse_arping('arping.txt')):
        print repr((ifaces, names, comment))

        clusto.begin_transaction()
        server = None
        for name in names:
            try:
                server = clusto.get_by_name(name)
            except: pass
            if server:
                print 'Found a server object named', server.name
                break

        if not server:
            for ifname, ip, mac in ifaces:
                servers = clusto.get_entities(attrs=[{
                    'key': 'port-nic-eth',
                    'subkey': 'mac',
                    'value': mac,
                }])
                if servers:
                    server = servers[0]
                    print 'Found a server object with MAC', mac, server.name
                    break

        if not server:
            print 'Creating a new server object:', names[0]
            server = PenguinServer(names[0])

        if len(ifaces) != 2:
            print server.name, 'has too many interfaces!'
            continue

        for i, iface in enumerate(ifaces):
            ifnum = i + 1
            ifname, ip, mac = iface
            if ip:
                try:
                    ipman = IPManager.get_ip_manager(ip)
                    server.bind_ip_to_osport(ip, ifname, porttype='nic-eth', portnum=ifnum, ipman=ipman)
                except ResourceException:
                    print 'Unable to bind IP: No IPManager for', ip
            server.set_port_attr('nic-eth', ifnum, 'mac', mac)

        if comment:
            server.set_attr(key='description', subkey='etchosts', value=comment)
        clusto.commit()

if __name__ == '__main__':
    init_script()
    main()
