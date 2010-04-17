"""
SNMPMixin for objects that can be accessed with SNMP
"""

import clusto
from clusto.drivers.resourcemanagers import IPManager

# Get rid of pesky errors about missing routes and tcpdump
import logging
runtime = logging.getLogger('scapy.runtime')
runtime.setLevel(logging.ERROR)
loading = logging.getLogger('scapy.loading')
loading.setLevel(logging.ERROR)

from scapy.all import SNMP, SNMPget, SNMPset, SNMPnext, SNMPvarbind
from socket import socket, AF_INET, SOCK_DGRAM

class SNMPMixin:
    """Provide SNMP capabilities to devices
    """

    def _snmp_connect(self, port=161):
        ip = IPManager.get_ips(self)
        if not ip:
            raise ValueError('Device %s does not have an IP' % self.name)
        ip = ip[0]

        community = self.attr_values(key='snmp', subkey='community', merge_container_attrs=True)
        if not community:
            raise ValueError('Device %s does not have an SNMP community attribute' % self.name)
        
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.connect((ip, port))
        return (str(community[0]), sock)

    def _snmp_get(self, oid):
        community, sock = self._snmp_connect()

        pdu = SNMPget(varbindlist=[SNMPvarbind(oid=str(oid))])
        p = SNMP(community=community, PDU=pdu)
        sock.sendall(p.build())

        r = SNMP(sock.recv(4096))
        return r.PDU.varbindlist[0].value.val

    def _snmp_set(self, oid, value):
        community, sock = self._snmp_connect()

        pdu = SNMPset(varbindlist=[SNMPvarbind(oid=str(oid), value=value)])
        p = SNMP(community=community, PDU=pdu)
        sock.sendall(p.build())

        r = SNMP(sock.recv(4096))
        return r

    def _snmp_walk(self, oid_prefix):
        community, sock = self._snmp_connect()

        nextoid = oid_prefix
        while True:
            p = SNMP(community=community, PDU=SNMPnext(varbindlist=[SNMPvarbind(oid=nextoid)]))
            sock.sendall(p.build())

            r = SNMP(sock.recv(4096))
            oid = r.PDU.varbindlist[0].oid.val
            if oid.startswith(oid_prefix):
                yield (oid, r.PDU.varbindlist[0].value.val)
            else:
                break
            nextoid = oid

        sock.close()
