import clusto
from clusto.scripthelpers import init_script
from discovery import SWITCHPORT_TO_RU
from loadipmac import SWITCHPORT_TO_PWRPORT
import subprocess

init_script()

def getinfo(server):
    mac = server.attr_values(key='port-nic-eth', subkey='mac')
    if not mac:
        print 'No MAC', server.name
        return
    else:
        mac = mac[0]
    p = subprocess.Popen(['motirtg-ipmac', '--mac=%s' % mac], stdout=subprocess.PIPE)
    stdout = p.communicate()[0]
    if stdout.count('\n') < 3:
        return

    return [x.strip(' ') for x in stdout.split('\n')[3].split('|') if x]

for s in clusto.get_entities(clusto_types=['server']):
    if s.name == 'motibox1': continue
    if s.parents(clusto_types=['rack']):
        continue
    result = getinfo(s)
    if not result:
        print 'Unable to find', s.name
        continue
    print s.name, result
    switch, switchip, port, mac, ipaddr = result
    port = int(port)
    switch = clusto.get_by_name(switch)
    rack = switch.parents(clusto_types=['rack'])[0]
    if mac.lower() in [x.lower() for x in s.attr_values(key='port-nic-eth', subkey='mac')]:
        print s.name, 'is on', switch.name, 'port', port

        clusto.begin_transaction()

        for r in s.parents(clusto_types=['rack']):
            r.remove(s)
        rack.insert(s, SWITCHPORT_TO_RU[port])
        print 'Inserted %s into %s:%s' % (s.name, rack.name, SWITCHPORT_TO_RU[port])

        s.disconnect_port('nic-eth', 1)
        s.disconnect_port('nic-eth', 2)
        s.disconnect_port('pwr-nema-5', 1)
        s.disconnect_port('console-serial', 1)
        print 'Disconnected ports'

        s.connect_ports('nic-eth', 1, switch, port)
        s.connect_ports('nic-eth', 2, switch, port + 20)
        s.connect_ports('pwr-nema-5', 1, clusto.get_by_name(rack.name + '-pwr1'), SWITCHPORT_TO_PWRPORT[port])
        s.connect_ports('console-serial', 1, clusto.get_by_name(rack.name + '-ts1'), port)
        print 'Connected ports'

        clusto.commit()
