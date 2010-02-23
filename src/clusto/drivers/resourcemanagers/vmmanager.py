"""
The VMManager is a special case of resource manager.

It overrides many of the standard ResourceManager functions but still makes
use of the ResourceManager plumbing where appropriate.

"""

import clusto
from clusto.drivers import ResourceManager
from clusto.exceptions import ResourceException

class VMManager(ResourceManager):
    """Manage resources for Virtual Machines.

    The resource being managed are the host machines.  A VM gets assigned to a
    host machine.  The VMManager keeps track of how much cpu/ram/disk is
    available on each host and allocates them accordingly.
    """
    
    _driver_name = "vmmanager"

    _attr_name = "vmmanager"

    def ensure_type(self, resource, number=True, thing=None):

        if isinstance(resource, basestring):
            resource = clusto.get_by_name(resource)

        if resource not in self:
            raise ResourceTypeException("%s is not managed by this VM manager"
                                        % resource.name)

        return (resource, number)
    
        
    def insert(self, thing, memory=None, disk=None):
        # insert into self and also add attributes that will help with  allocation
        if thing.type != 'server':
            raise ResourceTypeException("Only servers can be inserted into "
                                        "this manager.")

        
        memory = memory or thing.attr_value('system', subkey='memory')
        disk = disk or thing.attr_value('system', subkey='disk')

        if not memory and not disk:
            raise ResourceTypeException("Server must have attributes for "
                                        "key='system' and subkey='disk' "
                                        "and 'memory' set to be inserted into "
                                        "this manager.")

        try:
            clusto.begin_transaction()

            attr = super(VMManager, self).insert(thing)

            self.add_attr(thing.name,
                          subkey='available_memory',
                          value=memory)

            self.add_attr(thing.name,
                          subkey='available_disk',
                          value=disk)
            clusto.commit()
            
        except Exception, x:
            clusto.rollback_transaction()
            raise x
        
        
        return attr
    
    def remove(self, thing):
        # check if thing is in use by a VM
        # error if yes
        # remove if no and clear attributes related to helping allocation
        pass
        
    def additional_attrs(self, thing, resource, number):
        pass

    def allocate(self, thing, resource=(), number=True, **kwargs):
        """Allocate resources for VMs

        pass off normal allocation to the parent but also keep track of
        available host-resources
        """

        
        attr = super(VMManager, self).allocate(thing, resource, number)

        return attr
    

    def deallocate(self, vm):
        # free up resources used by vm
        pass
        

class EC2VMManager(VMManager):

    _driver_name = "ec2vmmanager"

    _properties = {'budget':None,
                   'current_cost':None,
                   'accountstuff':None} # i'd have to lookup again what ec2 actually needs

    def allocator(self):
        """allocate VMs on ec2 while keeping track of current costs and staying within the budget"""
        pass

class XenVMManager(VMManager):
    """Manage Xen Instances


    insert() servers that can act as hypervisors into this VM manager
    """
    
    _driver_name = "xenvmmanager"

    #_properties = { # som configuration properties that help control how many VMs per CPU or something like that}
    
    def allocator(self):
        """allocate VMs """
        pass
        # get list of potential servers: self.contents(clusto_type=[BasicServer])

        # find server with available resources

        # maybe do some bookeeping

        
        
