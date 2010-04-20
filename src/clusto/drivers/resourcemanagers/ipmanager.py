import clusto
from clusto.schema import Attribute

from clusto.drivers import ResourceManager, ResourceTypeException, Driver
from clusto.exceptions import ResourceNotAvailableException, ResourceException

import IPy

class IPManager(ResourceManager):
    """Resource Manager for IP spaces
    
    roughly follows the functionality available in IPy
    """


    _driver_name="ipmanager"

    _properties = {'gateway': None,
                   'netmask': '255.255.255.255',
                   'baseip': None }

    _attr_name = "ip"

    __int_ip_const = 2147483648
    
    @property
    def ipy(self):
        if not hasattr(self, '__ipy'):

            self.__ipy = IPy.IP(''.join([str(self.baseip), '/', self.netmask]),
                                make_net=True)


        return self.__ipy

    def ensure_type(self, resource, number=True, thing=None):
        """check that the given ip falls within the range managed by this manager"""

        try:
            if isinstance(resource, int):
                ip = IPy.IP(resource+self.__int_ip_const)
            else:
                ip = IPy.IP(resource)
        except ValueError:
            raise ResourceTypeException("%s is not a valid ip."
                                        % resource)

        if self.baseip and (ip not in self.ipy):
            raise ResourceTypeException("The ip %s is out of range for this IP manager.  Should be in %s/%s"
                                        % (str(ip), self.baseip, self.netmask))


        return (int(ip.int()-self.__int_ip_const), number)


    def additional_attrs(self, thing, resource, number):

        resource, number = self.ensure_type(resource, number)

        thing.add_attr(self._attr_name, number=number, subkey='ipstring', value=str(IPy.IP(resource+self.__int_ip_const)))
        
                     
    def allocator(self):
        """allocate IPs from this manager"""

        if self.baseip is None:
            raise ResourceTypeException("Cannot generate an IP for an ipManager with no baseip")

        lastip = self.attr_query('_lastip')
                
        if not lastip:
            # I subtract self.__int_ip_const to keep in int range
            startip=int(self.ipy.net().int() + 1) - self.__int_ip_const 
        else:
            startip = lastip[0].value


        
        ## generate new ips the slow naive way
        nextip = int(startip)
        if self.gateway:
            gateway = IPy.IP(self.gateway).int() - self.__int_ip_const
        else:
            gateway = None
        endip = self.ipy.broadcast().int() - self.__int_ip_const

        for i in range(2):
            while nextip < endip:

                if nextip == gateway:
                    nextip += 1
                    continue

                if self.available(nextip):
                    self.set_attr('_lastip', nextip)
                    return self.ensure_type(nextip, True)
                else:
                    nextip += 1
            
            # check from the beginning again in case an earlier ip
            # got freed
                    
            nextip = int(self.ipy.net().int() + 1)
            
        raise ResourceNotAvailableException("out of available ips.")

    @classmethod
    def get_ip_manager(cls, ip):
        """return a valid ip manager for the given ip.

        @param ip: the ip
        @type ip: integer, string, or IPy object

        @return: the appropriate IP manager from the clusto database
        """

        ipman = None
        if isinstance(ip, Attribute):
            ipman = ip.entity
            return Driver(ipman)

        for ipmantest in clusto.get_entities(clusto_drivers=[cls]):
            try:
                ipmantest.ensure_type(ip)
            except ResourceTypeException:
                continue

            ipman = Driver(ipmantest)
            break
        

        if not ipman:
            raise ResourceException("No resource manager for %s exists."
                                    % str(ip))
        
        return ipman
        
    @classmethod
    def get_ips(cls, device):

        ret = [str(IPy.IP(x.value+cls.__int_ip_const))
               for x in cls.resources(device)]

        return ret

    @classmethod
    def get_devices(self, ip):
        subnet = IPManager.get_ip_manager(ip)
        return subnet.owners(ip)
