from socket import socket, AF_INET, SOCK_DGRAM
from traceback import format_exc
from struct import unpack

from scapy import BOOTP

from clusto.scripthelpers import init_script
from clusto.drivers import IPManager, PenguinServer
import clusto

def dhcp_parse(packet):
    options = packet[BOOTP].payload.options
    hwaddr = ':'.join(['%02x' % ord(x) for x in packet.chaddr.rstrip('\x00')])

    mac = None
    vendor = None
    options = [(k, v) for k, v in [x for x in options if type(x) == tuple]]
    options = dict(options)
    if 'client_id' in options:
        mac = unpack('>6s', options['client_id'][1:])[0]
        options['client_id'] = ':'.join([('%x' % ord(x)).ljust(2, '0') for x in mac]).lower()
    return (hwaddr, options)

def dhcp_listen():
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('0.0.0.0', 67))

    while True:
        data, address = sock.recvfrom(4096)
        packet = BOOTP(data)
        yield dhcp_parse(packet)
    return

def update_clusto(address, request):
    if 'client_id' in request and (request['client_id'].lower() != address.lower()):
        pass
        #print 'Warning: DHCP client ID does not match source MAC', request['client_id'], '!=', address
    address = request.get('client_id', address).lower()

    server = clusto.get_entities(attrs=[{
            'key': 'bootstrap',
            'subkey': 'mac',
            'value': address
        }, {
            'key': 'port-nic-eth',
            'subkey': 'mac',
            'number': 1,
            'value': address
        }])
    if not server:
        #print 'DHCP from unknown MAC:', address
        return

    try:
        server = server[0]
        if request.get('vendor_class_id', None) == 'udhcp 0.9.9-pre':
            # This is an IPMI request
            #print 'Associating IPMI address', address, 'with nic-eth:1 on', server.name
            server.set_port_attr('nic-eth', 1, 'ipmi-mac', address)
        else:
            print 'Associating physical address with nic-eth:1 on', server.name
            server.set_port_attr('nic-eth', 1, 'mac', address)
    except:
        print 'Something went wrong'
        print format_exc()

def main():
    init_script()
    for address, request in dhcp_listen():
        try:
            update_clusto(address, request)
        except:
            print 'Exception in watch_dhcp'
            print format_exc()

if __name__ == '__main__':
    main()
