from clusto.scripthelpers import get_clusto_config
from clusto.drivers import *
from subprocess import Popen, PIPE, STDOUT
import clusto

import sys
import re

def ssh_exec(ip, cmd, user='root', stdin=None):
    proc = Popen('ssh -o "PasswordAuthentication no" -o "StrictHostKeyChecking no" -o "CheckHostIP no" -l %s %s "%s"' % (user, ip, cmd), stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
    if stdin:
        proc.stdin.write(stdin)
    proc.wait()
    stdout = proc.stdout.read()
    return proc.returncode, stdout

def main():
    if len(sys.argv) < 2:
        print 'Usage: %s <ipaddress>' % sys.argv[0]
        return

    ip = sys.argv[1]
    #device = IPManager.get_device(ip)
    #if not device:
    #    device = clusto.get_entities(attrs=[{'key': 'ipaddress', 'value': ip}])
    #if not device:
    #    print 'Unable to find a device matching %s' % ip
    #    return
    #device = device[0]
    #print repr(device)


    retcode, output = ssh_exec(ip, 'ip addr show')
    if retcode != 0:
        print output
        return
    
    iplist = []
    iface = None
    output = [x.strip(' \t\r') for x in output.split('\n')]
    for line in output:
        if not line: continue
        if line[0].isdigit():
            iface = line.split(' ')[1].rstrip(':')
        if line.startswith('link/ether'):
            macaddr = line.split(' ')[1]
        if line.startswith('inet '):
            line = line.split(' ')
            ipaddr = line[1]
            ifname = line[-1]
            if ipaddr == '127.0.0.1/8': continue
            iplist.append((ifname, macaddr, ipaddr))

    retcode, output = ssh_exec(ip, 'hostname')
    if retcode != 0:
        print output
        return

    output = output.strip('\r\n')
    fqdn = output
    if output.find('.') != -1:
        output = output.split('.', 1)[0]
    hostname = output

    device = None
    try:
        device = clusto.get_by_name(hostname)
        print 'Found by hostname'
    except LookupError:
        pass

    if not device:
        device = clusto.get_entities(attrs=[{'key': 'fqdn', 'value': fqdn}])
        if device:
            device = device[0]
            print 'Found by fqdn'

    if not device:
        for iface, macaddr, ipaddr in iplist:
            device = IPManager.get_device(ipaddr.split('/', 1)[0])
            if device:
                device = device[0]
                print 'Found by IPManager'
                break

    if not device:
        attrs = []
        for iface, macaddr, ipaddr in iplist:
            attrs.append({'key': 'ipaddress', 'value': ipaddr.split('/', 1)[0]})
        device = clusto.get_entities(attrs=attrs)
        if device:
            device = device[0]
            print 'Found by ipaddress attr'
        else:
            device = None

    if not device:
        print 'Unable to find device in clusto', hostname, ipaddr
        return

    pattern = re.compile('(?P<iftype>[a-z]+)(?P<ifnum>[0-9]+)(?P<other>.*)')
    for iface, macaddr, ipaddr in iplist:
        if iface.find(':') != -1:
            iface = iface.split(':', 1)[0]
        match = pattern.match(iface)
        if not match:
            print 'Unable to parse ifname:', iface
        match = match.groupdict()
        iftype = match['iftype']
        ifnum = int(match['ifnum'])

        if iftype != 'eth': continue

        ipaddr = ipaddr.split('/')[0]
        print repr(ipaddr)
        subnet = IPManager.get_ip_manager(ipaddr)

        if device in subnet.owners(ipaddr):
            continue
        print repr((ipaddr, 'nic-' + iftype, ifnum, macaddr))
        device.bindIPtoPort(ipaddr, 'nic-' + iftype, ifnum)
        device.set_port_attr('nic-' + iftype, ifnum, 'mac-address', macaddr)
    print repr(device)
    clusto.commit()

if __name__ == '__main__':
    config = get_clusto_config()
    clusto.connect(config.get('clusto', 'dsn'))
    clusto.init_clusto()
    main()
