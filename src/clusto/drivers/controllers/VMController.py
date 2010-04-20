from random import shuffle

from clusto.drivers import Controller
import libvirt

class VMController(Controller):
    @classmethod
    def allocate(cls, pool, namemanager, ipmanager, memory, disk, swap, storage_pool='vol0'):
        '''
        Allocate a new VM running on a server in the given pool with enough
        free memory.  The new VM will be assigned a name from the given
        namemanager.

        Memory is specified in megabytes (MB)
        Swap is specified in megabytes (MB)
        Disk is specified in gigabytes (GB)
        '''

        # Find a suitable server in the pool
        host = VMController._find_hypervisor(pool, memory, disk, swap, storage_pool)

        # Call libvirt to create the server
        vmxml = VMController._xen_create_vm(host, memory, disk, swap, storage_pool)

        vm = namemanager.allocate(XenVirtualServer)
        vm.from_xml(vmxml)

        # Assign an IP to the server object
        ipmanager.allocate(vm)

        # Return VM object
        return vm
    
    @classmethod
    def destroy(cls, obj):
        # Call libvirt to destroy the server
        # clusto.deleteEntity(obj.entity)

    @classmethod
    def _find_hypervisor(cls, pool, memory, disk, swap, storage_pool):
        candidates = pool.contents()
        shuffle(candidates)

        while True:
            if not candidates:
                raise Exception('No hypervisor candidates have enough available resources')
            server = candidates.pop()
            ip = server.get_ips()
            if not ip:
                continue
            conn = libvirt.openReadOnly('xen+tcp://%s' % ip[0])
            if not conn:
                continue

            freedisk = conn.storagePoolLookupByName(storage_pool).info()[3]
            if (disk * 1073741824) > freedisk:
                continue

            freemem = conn.getFreeMemory() / 1048576
            if mem > freemem:
                continue
            return server

    @classmethod
    def _xen_create_vm(cls, 
