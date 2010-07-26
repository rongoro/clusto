
from clusto.drivers.devices.servers import BasicVirtualServer
from clusto.drivers.resourcemanagers.ec2vmmanager import EC2VMManager

class EC2VirtualServer(BasicVirtualServer):
    _driver_name = "ec2virtualserver"

    _port_meta = {}


    @property
    def _instance(self):
        res = EC2VMManager.resources(self)[0]
        manager = EC2VMManager.get_resource_manager(res)

        instance = manager._get_instance_from_resource(res.value)
        return instance
    
    def get_ips(self):
        """Get the IPs for this EC2 server."""
        
        return [self._instance.private_ip_address, self._instance.ip_address]

    def get_state(self):
        """Get the instance state."""
        
        return self._instance.state

    def console(self, *args, **kwargs):

        console = self._instance.get_console_output()

        return console.output
