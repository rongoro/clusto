#!/usr/bin/env python
from clusto.scripthelpers import init_script
from clusto.drivers import IPManager, VMManager
import clusto

import sys
import re

def format_line(key, value, pad=20):
    if isinstance(value, list):
        value = ', '.join(value)
    key += ':'
    print key.ljust(pad, ' '), value

def device_info(obj):
    print 'Name:'.ljust(20, ' '), obj.name
    print 'Type:'.ljust(20, ' '), obj.type

    ip = IPManager.get_ips(obj)
    if ip:
        format_line('IP', ip)
    parents = obj.parents()
    if parents:
        format_line('Parents', [x.name for x in parents])
    contents = obj.contents()
    if contents:
        format_line('Contents', [x.name for x in contents])
    if obj.type == 'virtualserver':
        hv = VMManager.resources(obj)
        if hv:
            format_line('Hypervisor', [x.value.name for x in hv])

    print '\n',

    serial = obj.attr_values(key='system', subkey='serial')
    if serial:
        format_line('Serial', [x.rstrip('\r\n') for x in serial if x])
    memory = obj.attr_value(key='system', subkey='memory')
    if memory:
        format_line('Memory', '%i GB' % (memory / 1000))
    disk = obj.attr_value(key='system', subkey='disk')
    if disk:
        format_line('Disk', '%i GB (%i)' % (disk, len(obj.attrs(key='disk', subkey='size'))))
    cpucount = obj.attr_value(key='system', subkey='cpucount')
    if cpucount:
        format_line('CPU Cores', cpucount)
    desc = obj.attr_values(key='description')
    if desc:
        format_line('Description', '\n                    '.join(desc))

    ifaces = [('nic-eth(%i)' % x.number).ljust(20, ' ') + ' %s = %s' % (x.subkey, x.value) for x in obj.attrs(key='port-nic-eth') if x.subkey.find('mac') != -1]
    if ifaces:
        print '\n', '\n'.join(ifaces)

def main():
    if len(sys.argv) < 2:
        print 'Usage: %s <name, ip, or mac>' % sys.argv[0]
        return

    query = sys.argv[1]
    
    result = clusto.get(query)
    if not result:
        sys.stderr.write('Object not found\n')
        return -1

    for obj in result:
        device_info(obj)
    return 0

if __name__ == '__main__':
    init_script()
    ret = main()
    if not ret:
        sys.exit(0)
    else:
        sys.exit(ret)
