
from clusto.drivers.devices.common import IPMixin
from clusto.drivers.devices.servers import BasicVirtualServer
from clusto.drivers.resourcemanagers.ec2vmmanager import EC2VMManager

import time

class EC2VirtualServer(BasicVirtualServer, IPMixin):
    _driver_name = "ec2virtualserver"

    _port_meta = {}


    @property
    def _instance(self):
        res = EC2VMManager.resources(self)[0]
        manager = EC2VMManager.get_resource_manager(res)

        instance = manager._get_instance_from_resource(res.value)
        return instance
    
    def get_state(self):
        """Get the instance state."""
        
        return self._instance.state

    def console(self, *args, **kwargs):

        console = self._instance.get_console_output()

        return console.output

    
    def update_metadata(self, *args, **kwargs):

        wait = kwargs.get('wait', False)
        while wait:

            state = self.get_state()


            if state == 'running':
                self.clear_metadata()
                self.bind_ip_to_osport(self._instance.private_ip_address,
                                       'nic-eth0')

                self.bind_ip_to_osport(self._instance.ip_address, 'ext-eth0')
                break
            
            time.sleep(2)

    def clear_metadata(self, *args, **kwargs):

        self.del_attrs('ip')
        
