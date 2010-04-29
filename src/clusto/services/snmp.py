#!/usr/bin/env python
from socket import socket, AF_INET, SOCK_DGRAM
from traceback import format_exc
from time import strftime, time, localtime, sleep
from struct import unpack
import sys

import logging

from clusto.services.config import conf, get_logger
log = get_logger('clusto.snmp', 'INFO')

import logging
runtime = logging.getLogger('scapy.runtime')
runtime.setLevel(logging.ERROR)
loading = logging.getLogger('scapy.loading')
loading.setLevel(logging.ERROR)

from scapy.all import SNMP

from clusto.drivers import IPManager, PenguinServer
import clusto

sys.path.insert(0, '/var/lib/clusto')
import rackfactory

def update_clusto(trap):
    ts = strftime('[%Y-%m-%d %H:%M:%S]')
    if trap['operation'] != 1:
        return

    if not trap['mac'].startswith('00'):
        return

    switch = IPManager.get_devices(trap['switch'])
    if not switch:
        log.warning('Unknown trap source: %s' % trap['switch'])
        return
    else:
        switch = switch[0]

    if not switch.attrs(key='snmp', subkey='discovery', value=1, merge_container_attrs=True):
        log.debug('key=snmp, subkey=discovery for %s not set to 1, ignoring trap' % switch.name)
        return

    rack = switch.parents(clusto_types=['rack'])[0]

    try:
        factory = rackfactory.get_factory(rack.name)
        if not factory:
            log.warning('Unable to locate rack factory for %s' % rack.name)
            return
    except:
        log.error(format_exc())
        return

    server = switch.get_connected('nic-eth', trap['port'])
    if not server:
        servernames = clusto.get_by_name('servernames')
        clusto.SESSION.clusto_description = 'SNMP allocate new server'
        driver = factory.get_driver(trap['port'])
        server = servernames.allocate(driver)
        log.info('Created new %s on %s port %s: %s' % (driver.__name__, trap['switch'], trap['port'], server.name))

    try:
        clusto.begin_transaction()
        if not trap['mac'] in server.attr_values(key='bootstrap', subkey='mac', value=trap['mac']):
            log.debug('Adding bootstrap mac to', server.name)
            server.add_attr(key='bootstrap', subkey='mac', value=trap['mac'])

        factory.add_server(server, trap['port'])
        switch.set_port_attr('nic-eth', trap['port'], 'vlan', trap['vlan'])

        clusto.SESSION.clusto_description = 'SNMP update MAC and connections on %s' % server.name
        clusto.commit()
    except:
        log.error(format_exc())
        clusto.rollback_transaction()

    log.debug(repr(trap))

def trap_listen():
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('0.0.0.0', 162))
    while True:
        data, address = sock.recvfrom(4096)
        trap = SNMP(data)

        for var in trap.PDU.varbindlist:
            if var.oid.val == '1.3.6.1.4.1.9.9.215.1.1.8.1.2.1':
                var.value.val = var.value.val[:11]
                operation, vlan, mac, port = unpack('>cH6sH', var.value.val)
                result = {
                    'operation': ord(operation),
                    'vlan': vlan,
                    'mac': ':'.join([('%x' % ord(x)).rjust(2, '0') for x in mac]).lower(),
                    'port': port,
                    'switch': address[0],
                }
                yield result
