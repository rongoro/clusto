import clusto
from clusto.scripthelpers import init_script
from discovery import SWITCHPORT_TO_RU
from loadipmac import SWITCHPORT_TO_PWRPORT
from sysinfo import discover_hardware
import sys

from clusto.drivers import PenguinServer

init_script()

sys.stdout.write('Server name: ')
name = sys.stdin.readline().rstrip('\r\n')
sys.stdout.write('Rack: ')
rack = sys.stdin.readline().rstrip('\r\n')
sys.stdout.write('Switch port: ')
port = int(sys.stdin.readline().rstrip('\r\n'))
ru = SWITCHPORT_TO_RU[port]
sys.stdout.write('IP: ')
ip = sys.stdin.readline().rstrip('\r\n')

server = None
try:
    server = clusto.get_by_name(name)
except:
    pass
if server:
    print server.name, 'already exists!'
    sys.exit(0)

clusto.begin_transaction()

server = PenguinServer(name)

if ip:
    server.bind_ip_to_osport(ip, 'eth0')

rack = clusto.get_by_name(rack)
rack.insert(server, ru)

switch = clusto.get_by_name(rack.name + '-sw1')
power = clusto.get_by_name(rack.name + '-pwr1')
console = clusto.get_by_name(rack.name + '-ts1')
server.connect_ports('nic-eth', 1, switch, port)
server.connect_ports('nic-eth', 2, switch, port + 20)
server.connect_ports('pwr-nema-5', 1, power, SWITCHPORT_TO_PWRPORT[port])
server.connect_ports('console-serial', 1, console, port)

clusto.commit()

print 'Created', server.name

if not ip:
    sys.exit(0)
info = discover_hardware(ip)
if not info:
    print 'Unable to discover via SSH'
    sys.exit(0)

clusto.begin_transaction()

for itemtype in info:
    if itemtype == 'network': continue
    for i, item in enumerate(info[itemtype]):
        for subkey, value in item.items():
            server.set_attr(key=itemtype, subkey=subkey, value=value, number=i)

for ifnum in range(0, 2):
    ifname = 'eth%i' % ifnum
    server.set_port_attr('nic-eth', ifnum + 1, 'mac', info['network'][ifname]['hwaddr'])
    if 'inet addr' in info['network'][ifname]:
        server.bind_ip_to_osport(info['network'][ifname]['inet addr'], ifname)

clusto.commit()

print 'Discovered', server.name
