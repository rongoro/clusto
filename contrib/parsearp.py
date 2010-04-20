from discovery import discover_interfaces, get_snmp_hostname, get_ssh_hostname
from subprocess import Popen, PIPE
from xml.etree import ElementTree
import re

def snmp_interfaces(ip, community='digg1t'):
    p = Popen(['scli', '-c', 'show interface details ^eth[0-9]+$', '-x', ip, community], stdout=PIPE)
    xmldata = p.stdout.read()
    xmldata = xmldata.split('\n', 1)[1].strip('\r\n')
    if not xmldata:
        return {}

    xmltree = ElementTree.fromstring(xmldata)
    ifaces = {}

    for tree in xmltree.getiterator('interface'):
        iface = {}
        iface['name'] = tree.findtext('name')
        iface['hwaddr'] = tree.findtext('address')
        ifaces[tree.get('index')] = iface

    p = Popen(['scli', '-c', 'show ip addresses', '-x', ip, community], stdout=PIPE)
    xmldata = p.stdout.read().split('\n', 1)[1].strip('\r\n')
    if xmldata:
        xmltree = ElementTree.fromstring(xmldata)
        for node in xmltree.getiterator('address'):
            index = node.get('interface')
            if not index in ifaces: continue
            ifaces[index]['inet addr'] = node.get('address')

    result = {}
    for index in ifaces:
        name = ifaces[index]['name']
        del ifaces[index]['name']
        result[name] = ifaces[index]
    if not 'inet addr' in result['eth0']:
        result['eth0']['inet addr'] = ip
    return result

def parse_arping(filename):
    for line in file(filename, 'r'):
        mac, ip = line.rstrip('\r\n').split(' ', 1)
        yield (mac, ip)

def discover_hosts(hosts):
    ifpattern = re.compile('^eth[0-9]+$')


    for mac, ip in hosts:
        ifaces = snmp_interfaces(ip)
        name = get_snmp_hostname(ip)
        if not name:
            name = get_ssh_hostname(ip)
        if not name:
            print 'Unable to determine hostname for', ip
            continue

        if not ifaces:
            print 'Unable to discover interfaces on %s (%s)' % (ip, mac)
            continue

        ifaces = [(x, ifaces[x].get('inet addr', None), ifaces[x]['hwaddr'].lower()) for x in ifaces if ifpattern.match(x)]
        ifaces.sort(key=lambda x: x[0])

        if name:
            names = [name]
        else:
            names = []
        yield (ifaces, names, '')

def main():
    for ifaces, names, comment in discover_hosts(parse_arping('arping.txt')):
        print repr((ifaces, names))

if __name__ == '__main__':
    main()
