"""
PortMixin is a basic mixin to be used with devices that have ports
"""

import re

import clusto


from clusto.exceptions import ConnectionException

class PortMixin:
    """Provide port capabilities to devices
    
    The ports are defined in the Driver's _portmeta dictionary:

    _portmeta = { '<porttype>' : {'numports': <num> }}

    Several ports types can be defined in this dictionary.  Currently
    'numports' is the only porttype attribute used.  This data does not get
    stored as Entity attributes in the clusto db.  They live only in the class
    definition.

    Port data gets stored in the DB as the connect to other ports.  The
    keynames are of the form '_port-<porttype>'.  Each port has a specific
    number associated with it (usually the same number as on the physical
    device itself) and can have several port attributes.  There are no
    restrictions on attributes but some common ones might be: osname,
    cabletype, status, etc.
    
    """
    
    # _portmeta = { 'porttype' : {'numports': 10 }}

    _portmeta = { 'pwr-nema-5' : { 'numports':1, },
                  'nic-eth' : { 'numports':2, },
                  }


    def _port_key(self, porttype):
        
        return 'port-' + porttype
    
    def _ensure_portnum(self, porttype, num):


        if not self._portmeta.has_key(porttype) \
                or not isinstance(num, int) \
                or num < 1 \
                or num > self._portmeta[porttype]['numports']:

            msg = "No port %s:%s exists on %s." % (porttype, str(num), self.name)
                    
            raise ConnectionException(msg)
                

        return num

    def connect_ports(self, porttype, srcportnum, dstdev, dstportnum):
        """connect a local port to a port on another device
        """


        for dev, num in [(self, srcportnum), (dstdev, dstportnum)]:

            if not hasattr(dev, 'port_exists'):
                msg = "%s has no ports."
                raise ConnectionException(msg % (dev.name))

            num = dev._ensure_portnum(porttype, num)

            if not dev.port_exists(porttype, num):
                msg = "port %s:%d doesn't exist on %s"
                raise ConnectionException(msg % (porttype, num, dev.name))

        
            if not dev.port_free(porttype, num):
                msg = "port %s%d on %s is already in use"
                raise ConnectionException(msg % (porttype, num, dev.name))

        try:
            clusto.begin_transaction()
            self.set_port_attr(porttype, srcportnum, 'connection', dstdev)
            self.set_port_attr(porttype, srcportnum, 'otherportnum', dstportnum)
            
            dstdev.set_port_attr(porttype, dstportnum, 'connection', self)
            dstdev.set_port_attr(porttype, dstportnum, 'otherportnum', srcportnum)
            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x

    def disconnect_port(self, porttype, portnum):
        """disconnect both sides of a port"""

        portnum = self._ensure_portnum(porttype, portnum)

        if not self.port_free(porttype, portnum):

            dev = self.get_connected(porttype, portnum)
            
            otherportnum = self.get_port_attr(porttype, portnum, 'otherportnum')
            
            clusto.begin_transaction()
            try:
                dev.del_port_attr(porttype, otherportnum, 'connection')
                dev.del_port_attr(porttype, otherportnum, 'otherportnum')
                
                self.del_port_attr(porttype, portnum, 'connection')
                self.del_port_attr(porttype, portnum, 'otherportnum')
                clusto.commit()
            except Exception, x:
                clusto.rollback_transaction()
                raise x
            

    def get_connected(self, porttype, portnum):
        """return the device that the given porttype/portnum is connected to"""

        portnum = self._ensure_portnum(porttype, portnum)

        if not self.port_exists(porttype, portnum):
            msg = "port %s:%d doesn't exist on %s"
            raise ConnectionException(msg % (porttype, portnum, self.name))
            

        return self.get_port_attr(porttype, portnum, 'connection')
            

    def ports_connectable(self, porttype, srcportnum, dstdev, dstportnum):
        """test if the ports you're trying to connect are compatible.
        """

        return (self.port_exists(porttype, srcportnum) 
                and dstdev.port_exists(porttype, dstportnum))
 
    def port_exists(self, porttype, portnum):
        """return true if the given port exists on this device"""
        
        if ((porttype in self._portmeta)):
            try:
                portnum = self._ensure_portnum(porttype, portnum)
                return True
            except ConnectionException:
                return False
        else:
            return False

    def port_free(self, porttype, portnum):
        """return true if the given porttype and portnum are not in use"""
        
        portnum = self._ensure_portnum(porttype, portnum)

        if (not self.port_exists(porttype, portnum) or
            self.has_attr(key=self._port_key(porttype), number=portnum, 
                         subkey='connection')):
            return False
        else:
            return True
        

    def add_port_attr(self, porttype, portnum, key, value):
        """add an attribute on the given port"""

        portnum = self._ensure_portnum(porttype, portnum)

        self.add_attr(key=self._port_key(porttype),
                     number=portnum,
                     subkey=key,
                     value=value)

    def set_port_attr(self, porttype, portnum, key, value):
        """set an attribute on the given port"""

        portnum = self._ensure_portnum(porttype, portnum)

        self.set_attr(key=self._port_key(porttype),
                     number=portnum,
                     subkey=key,
                     value=value)


    def del_port_attr(self, porttype, portnum, key, value=()):
        """delete an attribute on the given port"""

        portnum = self._ensure_portnum(porttype, portnum)

        if value is ():
            self.del_attrs(key=self._port_key(porttype),
                          number=portnum,
                          subkey=key)
        else:

            self.del_attrs(key=self._port_key(porttype),
                          number=portnum,
                          subkey=key,
                          value=value)
            
                     
    def get_port_attr(self, porttype, portnum, key):
        """get an attribute on the given port"""

        portnum = self._ensure_portnum(porttype, portnum)

        attr = self.attrs(key=self._port_key(porttype),
                          number=portnum,
                          subkey=key)

        if len(attr) > 1:
            raise ConnectionException("Somehow more than one attribute named "
                                      "%s is associated with port %s:%d on %s"
                                      % (key, porttype, portnum, self.name))

        elif len(attr) == 1:
            return attr[0].value

        else:
            return None
            
    @property
    def port_info(self):
        """return a list of tuples containing port information for this device
        
        format:
            port_info[<porttype>][<portnum>][<portattr>]
        """

        portinfo = {}
        for ptype in self.port_types:
            portinfo[ptype]={}
            for n in range(1, self._portmeta[ptype]['numports'] + 1):
                portinfo[ptype][n] = {'connection': self.get_port_attr(ptype, n, 'connection'),
                                      'otherportnum': self.get_port_attr(ptype, n, 'otherportnum')}

        return portinfo

    @property
    def port_info_tuples(self):
        """return port information as a list of tuples that are suitble for use
        as *args to connect_ports

        format:
          [ ('porttype', portnum, <connected device>, <port connected to>), ... ]
        """
        
        t = []
        d = self.port_info
        for porttype, numdict in d.iteritems():
            for num, stats in numdict.iteritems():
                t.append((porttype, num, 
                          stats['connection'], stats['otherportnum']))
        
        return t

                         

    
    @property
    def free_ports(self):
        
        return [(pinfo[0], pinfo[1]) for pinfo in self.port_info_tuples if pinfo[3] == None]

    @property
    def connected_ports(self):
        """Return a list of connected ports"""

        pdict = {}
        for ptype in self.port_types:

            portlist = [a.number for a in self.attrs(self._port_key(ptype), 
                                                     subkey='connection')]
            portlist.sort()
            pdict[ptype] = portlist

        return pdict

    @property
    def port_types(self):
        return self._portmeta.keys()


