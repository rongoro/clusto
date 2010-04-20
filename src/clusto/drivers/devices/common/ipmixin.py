"""
IPMixin is a basic mixin to be used by devices that can be assigned IPs
"""

import re

import clusto

from clusto.drivers.resourcemanagers import IPManager

from clusto.exceptions import ConnectionException,  ResourceException


class IPMixin:

    def add_ip(self, ip=None, ipman=None):

        if not ip and not ipman:
            raise ResourceException('If no ip is specified then an ipmanager must be specified')

        elif ip:
            
            if not ipman:
                ipman = IPManager.get_ip_manager(ip)

            return ipman.allocate(self, ip)
        else:
            return ipman.allocate(self)
            
            
        
    def has_ip(self, ip):

        ipman = IPManager.get_ip_manager(ip)

        return self in ipman.owners(ip)

    def get_ips(self):
        """Get a list of IPs for this Entity in ipstring format"""

        return self.attr_values(IPManager._attr_name, subkey='ipstring')
        

    def bind_ip_to_osport(self, ip, osportname, ipman=None, porttype=None, portnum=None):
        """bind an IP to an os port and optionally also asign the os port name
        to a physical port

        If the given ip is already allocated to this device then use it.  If
        it isn't, try to allocate it from a matching IPManager.

        
        """

        if (porttype != None) ^ (portnum != None):
                raise Exception("both portype and portnum need to be specified or set to None")
            
        try:
            clusto.begin_transaction()

            if not self.has_ip(ip):
                if not ipman:
                    ipman = IPManager.get_ip_manager(ip)

                ipman.allocate(self, ip)

                clusto.flush()
            else:
                ipman = IPManager.get_ip_manager(ip)

            ipattrs = ipman.get_resource_attrs(self, ip)

            if porttype is not None and portnum is not None:
                self.set_port_attr(porttype, portnum, 'osportname', osportname)

            self.set_attr(ipattrs[0].key,
                         number=ipattrs[0].number,
                         subkey='osportname',
                         value=osportname)

            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x
        


        



            
        
