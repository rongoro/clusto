from basicserver import BasicVirtualServer
from random import shuffle
from IPy import IP
import libvirt

class XenVirtualServer(BasicVirtualServer):
    _driver_name = "xenvirtualserver"

    def __init__(self, name, **kwargs):
        BasicVirtualServer.__init__(self, name, **kwargs)

    @classmethod
    def _select_hypervisor(self, pool, options):
        hypervisors = pool.contents(clusto_types=['server'])
        shuffle(hypervisors)
        hypervisor = None
        for hv in hypervisors:
            ip = hv.get_ips()
            if not ip:
                continue
            ip = ip[0]

            conn = libvirt.open('xen+tcp://' + ip)
            if not conn:
                continue

            if conn.getFreeMemory() < options['memory']:
                continue
            if conn.storagePoolLookupByName('vol0').info()[3] < options['disk']:
                continue
            return (hv, conn)
        raise DriverException('Cannot find a hypervisor with enough free resources')

    @classmethod
    def create(self, namemanager, ipmanager, hypervisors, **kwargs):
        options = {
            'disk': 50,
            'memory': 1024,
        }
        options.update(kwargs)

        vm = namemanager.allocate(XenVirtualServer)
        print 'Created', vm.name
        vm.set_attr(key='system', subkey='memory', value=options['memory'])
        vm.set_attr(key='system', subkey='disk', value=options['disk'])
        ipmanager.allocate(vm)

        # Generate a MAC based on IP. Serious voodoo
        intip = IP(vm.get_ips()[0]).int()
        mac = (0x0152 << 32) + intip
        macstr = ['%02x' % ((mac >> (i * 8)) & 0xFF) for i in range(5, -1, -1)]
        mac = ':'.join(macstr)
        vm.set_port_attr('nic-eth', 1, 'mac', mac)
        print 'Allocated IP and MAC'

        hv, conn = XenVirtualServer._select_hypervisor(hypervisors, options)
        hv.insert(vm)
        print 'Using hypervisor:', hv.name

        options['disk'] = int(options['disk'] * 1073741824.0)
        options['memory'] = int(options['memory'] * 1048576.0)

        storage = conn.storagePoolLookupByName('vol0')
        for disktype, disksize in [('disk', options['disk']), ('swap', options['memory'])]:
            storage.createXML('''
<volume>
    <name>%(name)s-%(type)s</name>
    <capacity>%(size)i</capacity>
    <target>
        <path>/dev/vol0/%(name)s-%(type)s</path>
    </target>
</volume>''' % {
                'name': vm.name,
                'type': disktype,
                'size': disksize,
            }, 0)
        conn.defineXML('''
<domain type="xen">
    <name>%(name)s</name>
    <memory>%(memory)i</memory>
    <os>
        <type>hvm</type>
        <loader>/usr/lib/xen-default/boot/hvmloader</loader>
        <boot dev="hd" />
        <boot dev="network" />
    </os>
    <features>
        <pae />
    </features>
    <devices>
        <disk type="block">
            <source dev="/dev/vol0/%(name)s-disk" />
            <target dev="hda" />
        </disk>
        <disk type="block">
            <source dev="/dev/vol0/%(name)s-swap" />
            <target dev="hdb" />
        </disk>
        <interface type="bridge">
            <source bridge="eth0" />
            <mac address="%(mac)s" />
        </interface>
        <console type="pty">
            <target port="0" />
        </console>
    </devices>
</domain>''' % {
            'name': vm.name,
            'memory': options['memory'],
            'mac': mac,
        })
        print 'VM defined'
        return vm

    def get_domain(self):
        hv = self.parents(clusto_types=['server'])[0]
        conn = libvirt.open('xen+tcp://' + hv.get_ips()[0])
        return conn.lookupByName(self.name)

    def start(self):
        self.get_domain().create()

    def reboot(self):
        self.get_domain().reboot()

    def shutdown(self):
        self.get_domain().shutdown()

    def destroy(self):
        self.get_domain().destroy()
