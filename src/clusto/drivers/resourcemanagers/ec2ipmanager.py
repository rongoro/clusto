
from clusto.drivers.resourcemanagers import IPManager
from clusto.drivers.devices import EC2VirtualServer
from clusto.exceptions import ResourceException, ResourceTypeException


import operator
import IPy
import boto

class EC2IPManager(IPManager):

    _driver_name = "ec2ipmanager"

    _properties = {'aws_access_key_id':None,
                   'aws_secret_access_key':None,
                   }


    _ec2_ip_ranges = {'us-east-1': ["216.182.224.0/20",
                                   "72.44.32.0/19",
                                   "67.202.0.0/18",
                                   "75.101.128.0/17",
                                   "174.129.0.0/16",
                                   "204.236.192.0/18",
                                   "184.73.0.0/16",
                                   "184.72.128.0/17",],
                     'us-west-1': ["204.236.128.0/18",
                                   "184.72.0.0/18",],
                     'eu-west-1': ["79.125.0.0/17",
                                   "46.51.128.0/18",],
                     'ap-southeast-1': ["175.41.128.0/18",],
                     'internal': ["10.0.0.0/8"]}

    _ip_range_list = []
    map(_ip_range_list.extend, [map(IPy.IP, x)
                                for x in _ec2_ip_ranges.values()])


    def _ec2_connection(self, region=None):
        c = boto.connect_ec2(aws_access_key_id=str(self.aws_access_key_id),
                             aws_secret_access_key=str(self.aws_secret_access_key))

        if not region or region == 'us-east-1':
            return c
        else:
            return boto.ec2.connect_to_region(region,
                                              aws_access_key_id=str(self.aws_access_key_id),
                                              aws_secret_access_key=str(self.aws_secret_access_key))
            

    def ensure_type(self, resource, number=True, thing=None):
        """check that the given ip can be managed by this manager"""

        try:
            if isinstance(resource, int):
                ip = IPy.IP(resource+self.__int_ip_const)
            else:
                ip = IPy.IP(resource)
        except ValueError:
            raise ResourceTypeException("%s is not a valid ip."
                                        % resource)

        if not any(map(lambda x: operator.contains(x, ip), _ip_range_list)):
            raise ResourceTypeException("%s is not a valid ip." % resource)

        return (int(ip.int()-self.__int_ip_const), number)
        

    def reserve_ip(self, region='us-west-1', ip=None):
        """Reserve an ip from ec2, or add a previously reserved ip"""

        conn = self._ec2_connection(region)
        if not ip:
            address = conn.allocate_address()
            ip = IPy.IP(address.public_ip)
        else:
            ip = IPy.IP(ip)

            a = self.add_attr(key='reserved_ip', subkey=region,
                              value=self._ipy_to_int(ip))


    def reserved_ips(self):

        ips = {}
        for attr in self.attrs(key='reserved_ip'):        
            ips.setdefault(attr.subkey, []).append(self._int_to_ipy(attr.value))

        return ips


    def update_reserved_ips(self):

        conn = self._ec2_connection()

        ips = set()
        for region in conn.get_all_regions():
            conn = self._ec2_connection(region.name)
            for address in conn.get_all_addresses():
                ips.add((region.name,
                         self._ipy_to_int(IPy.IP(address.public_ip))))

        reserved_ips = set((a.subkey, a.value)
                           for a in self.attrs(key='reserved_ip'))
        
        for region, ip in reserved_ips.difference(ips):
            self.del_attrs(key='reserved_ip', subkey=region, value=ip)

        for region, ip in ips.difference(reserved_ips):
                self.reserve_ip(region, ip)

                
    def get_instance_ips(self, vm):
        """Get the IPs for this EC2 server."""
        
        return [vm._instance.private_ip_address, vm._instance.ip_address]


    def allocator(self, ec2vm=None):
        """allocate IPs from this manager"""

        if not ec2vm:
            
        if ec2vm and ec2vm._driver_name != EC2VirtualServer._driver_name:
            raise ResourceException("%s is not a EC2 Virtual Server" % ec2vm.name)
        ec2vm_state = ec2vm.get_state() 
        if ec2vm and ec2vm_state != 'running':
            raise ResourceNotAvailableException("%s is not a running vm" % ec2vm.name)
        elif ec2vm and ec2vm_state == 'running':
            
            
            
        raise ResourceNotAvailableException("out of available ips.")

