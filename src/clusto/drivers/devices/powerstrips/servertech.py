"""
Server Technology Power Strips

"""


from basicpowerstrip import BasicPowerStrip
from clusto.drivers.devices.common import IPMixin, SNMPMixin
from clusto.drivers import IPManager
from clusto.exceptions import DriverException

import re


class PowerTowerXM(BasicPowerStrip, IPMixin, SNMPMixin):
    """
    Provides support for Power Tower XL/XM

    Power Port designations start with 1 at the upper left (.aa1) down to 32
    at the bottom right (.bb8).
    """

    _driver_name = "powertowerxm"

    _properties = {'withslave':0}


    _portmeta = { 'pwr-nema-L5': { 'numports':2 },
                  'pwr-nema-5' : { 'numports':16, },
                  'nic-eth' : { 'numports':1, },
                  'console-serial' : { 'numports':1, },
                  }



    _portmap = {'aa1':1,'aa2':2,'aa3':3,'aa4':4,'aa5':5,'aa6':6,'aa7':7,'aa8':8,
                'ab1':9,'ab2':10,'ab3':11,'ab4':12,'ab5':13,'ab6':14,'ab7':15,
                'ab8':16,'ba1':17,'ba2':18,'ba3':19,'ba4':20,'ba5':21,'ba6':22,
                'ba7':23,'ba8':24,'bb1':25,'bb2':26,'bb3':27,'bb4':28,'bb5':29,
                'bb6':30,'bb7':31,'bb8':32}

    _outlet_states = ['idleOff', 'idleOn', 'wakeOff', 'wakeOn', 'off', 'on', 'lockedOff', 'reboot', 'shutdown', 'pendOn', 'pendOff', 'minimumOff', 'minimumOn', 'eventOff', 'eventOn', 'eventReboot', 'eventShutdown']

    def _ensure_portnum(self, porttype, portnum):
        """map powertower port names to clusto port numbers"""

        if not self._portmeta.has_key(porttype):
            msg = "No port %s:%s exists on %s." % (porttype, str(num), self.name)
                    
            raise ConnectionException(msg)

        if isinstance(portnum, int):
            num = portnum
        else:
            if portnum.startswith('.'):
                portnum = portnum[1:] 
            
            if self._portmap.has_key(portnum):
                num = self._portmap[portnum]
            else:
                msg = "No port %s:%s exists on %s." % (porttype, str(num), 
                                                       self.name)
                    
                raise ConnectionException(msg)
 
        numports = self._portmeta[porttype]
        if self.withslave:
            if porttype in ['mains', 'pwr']:
                numports *= 2

        if num < 0 or num >= numports:
            msg = "No port %s:%s exists on %s." % (porttype, str(num), 
                                                   self.name)
                    
            raise ConnectionException(msg)



        return num

    def _get_port_oid(self, outlet):
        for oid, value in self._snmp_walk('1.3.6.1.4.1.1718.3.2.3.1.2'):
            if value.lower() == outlet:
                return oid

    def get_outlet_state(self, outlet):
        oid = self._get_port_oid(outlet)
        oid = oid.replace('1.3.6.1.4.1.1718.3.2.3.1.2', '1.3.6.1.4.1.1718.3.2.3.1.10')
        state = self._snmp_get(oid)
        return self._outlet_states[int(state)]

    def set_outlet_state(self, outlet, state, session=None):
        oid = self._get_port_oid(outlet)
        oid = oid.replace('1.3.6.1.4.1.1718.3.2.3.1.2', '1.3.6.1.4.1.1718.3.2.3.1.11')
        r = self._snmp_set(oid, state)
        if r.PDU.varbindlist[0].value.val != state:
            raise DriverException('Unable to set SNMP state')

    def set_power_off(self, porttype, portnum):
        if porttype != 'pwr-nema-5':
            raise DriverException('Cannot turn off ports of type: %s' % str(porttype))
        portnum = portnum.lstrip('.').lower()
        state = self.set_outlet_state(portnum, 2)

    def set_power_on(self, porttype, portnum):
        if porttype != 'pwr-nema-5':
            raise DriverException('Cannot turn off ports of type: %s' % str(porttype))
        portnum = portnum.lstrip('.').lower()
        state = self.set_outlet_state(portnum, 1)

    def reboot(self, porttype, portnum):
        if porttype != 'pwr-nema-5':
            raise DriverException('Cannot reboot ports of type: %s' % str(porttype))

        portnum = portnum.lstrip('.').lower()

        state = self.get_outlet_state(portnum)

        nextstate = None
        if state == 'off':
            nextstate = 1
        if state in ('idleOn', 'on', 'wakeOn'):
            nextstate = 3

        if not nextstate:
            raise DriverException('Outlet in unexpected state: %s' % state)

        self.set_outlet_state(portnum, nextstate)
