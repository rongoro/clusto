from xml.etree import ElementTree
from subprocess import Popen
from random import shuffle

from basicserver import BasicVirtualServer
from clusto.exceptions import DriverException

from IPy import IP
import libvirt

class XenVirtualServer(BasicVirtualServer):
    _driver_name = "xenvirtualserver"

    def __init__(self, name, **kwargs):
        BasicVirtualServer.__init__(self, name, **kwargs)

    def _libvirt_create_disk(self, conn, name, capacity, vgname):
        volume = ElementTree.XML('''
        <volume>
            <name></name>
            <capacity></capacity>
            <target>
                <path></path>
            </target>
        </volume>''')
        volume.find('name').text = '%s-%s' % (self.name, name)
        volume.find('capacity').text = str(capacity)
        volume.find('target/path').text = '/dev/%s/%s-%s' % (vgname, self.name, name)

        vg = conn.storagePoolLookupByName(vgname)
        return vg.createXML(ElementTree.tostring(volume), 0)

    def _libvirt_delete_disk(self, conn, name, vgname):
        vol = conn.storageVolLookupByPath('/dev/%s/%s-%s' % (vgname, self.name, name))
        if vol.delete(0) != 0:
            raise DriverException('Unable to delete disk %s-%s' % (self.name, name))

    def _libvirt_create_domain(self, conn, memory, cpucount, vgname):
        domain = ElementTree.XML('''
        <domain type="xen">
            <name></name>
            <memory></memory>
            <vcpu></vcpu>
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
                    <source />
                    <target />
                </disk>
                <disk type="block">
                    <source />
                    <target />
                </disk>
                <interface type="bridge">
                    <mac />
                    <source bridge="eth0" />
                </interface>
                <console type="pty">
                    <target port="0" />
                </console>
            </devices>
        </domain>''')

        domain.find('name').text = self.name
        domain.find('memory').text = str(memory)
        domain.find('vcpu').text = str(cpucount)

        disks = list(domain.findall('devices/disk'))
        disks[0].find('source').set('dev', '/dev/%s/%s-root' % (vgname, self.name))
        disks[0].find('target').set('dev', 'hda')
        disks[1].find('source').set('dev', '/dev/%s/%s-swap' % (vgname, self.name))
        disks[1].find('target').set('dev', 'hdb')

        domain.find('devices/interface/mac').set('address', self.get_port_attr('nic-eth', 1, 'mac'))

        xml = ElementTree.tostring(domain)
        return conn.defineXML(xml)

    def _libvirt_delete_domain(self, conn):
        domain = conn.lookupByName(self.name)
        if domain.undefine() != 0:
            raise DriverException('Unable to delete (undefine) domain %s' % name)

    def _libvirt_connect(self):
        host = self.get_hypervisor()

        ip = host.get_ips()
        if not ip:
            raise DriverException('Hypervisor does not have an IP!')
        ip = ip[0]

        conn = libvirt.open('xen+tcp://%s' % ip)
        if not conn:
            raise DriverException('Unable to connect to hypervisor! xen+tcp://%s' % ip)
        return conn

    def get_hypervisor(self):
        from clusto.drivers import VMManager
        host = VMManager.resources(self)
        if not host:
            raise DriverException('Cannot start a VM without first allocating a hypervisor with VMManager.allocate')
        return host[0].value

    def vm_create(self, conn=None):
        if not conn:
            conn = self._libvirt_connect()

        # Get and validate attributes
        disk_size = self.attr_values(key='system', subkey='disk')
        memory_size = self.attr_values(key='system', subkey='memory')
        swap_size = self.attr_values(key='system', subkey='swap')
        cpu_count = self.attr_values(key='system', subkey='cpucount')

        if not disk_size:
            raise DriverException('Cannot create a VM without a key=system,subkey=disk parameter (disk size in GB)')
        if not memory_size:
            raise DriverException('Cannot create a VM without a key=system,subkey=memory parameter (memory size in MB)')
        if not swap_size:
            swap_size = [512]
        if not cpu_count:
            cpu_count = [1]

        disk_size = disk_size[0]
        swap_size = swap_size[0]
        memory_size = memory_size[0]
        cpu_count = cpu_count[0]

        disk_size *= 1073741824
        swap_size *= 1048576
        memory_size *= 1024

        host = self.get_hypervisor()
        volume_group = host.attr_values(key='xen', subkey='volume-group', merge_container_attrs=True)
        if not volume_group:
            raise DriverException('No key=xen,subkey=volume-group defined for %s' % host.name)
        else:
            volume_group = volume_group[0]

        # Create disks and domain
        if not self._libvirt_create_disk(conn, 'root', disk_size, volume_group):
            raise DriverException('Unable to create logical volume %s-root' % self.name)
        if not self._libvirt_create_disk(conn, 'swap', swap_size, volume_group):
            raise DriverException('Unable to create logical volume %s-swap' % self.name)
        if not self._libvirt_create_domain(conn, memory_size, cpu_count, volume_group):
            raise DriverException('Unable to define domain %s' % self.name)

    def vm_start(self, conn=None):
        if not conn:
            conn = self._libvirt_connect()
        domain = conn.lookupByName(self.name)
        if domain.create() != 0:
            raise DriverException('Unable to start domain %s' % self.name)

    def vm_stop(self, force=False, conn=None):
        if not conn:
            conn = self._libvirt_connect()
        domain = conn.lookupByName(self.name)

        if force:
            ret = domain.destroy()
        else:
            ret = domain.shutdown()

        if ret != 0:
            raise DriverException('Unable to stop (destroy) domain %s' % self.name)

    def vm_reboot(self, conn=None):
        if not conn:
            conn = self._libvirt_connect()
        domain = conn.lookupByName(self.name)
        if domain.reboot(0) != 0:
            raise DriverException('Unable to reboot domain %s' % self.name)

    def vm_delete(self, conn=None):
        if not conn:
            conn = self._libvirt_connect()

        host = self.get_hypervisor()
        volume_group = host.attr_values(key='xen', subkey='volume-group', merge_container_attrs=True)
        if not volume_group:
            raise DriverException('No key=xen,subkey=volume-group defined for %s' % host.name)
        else:
            volume_group = volume_group[0]

        self._libvirt_delete_domain(conn)
        self._libvirt_delete_disk(conn, 'root', volume_group)
        self._libvirt_delete_disk(conn, 'swap', volume_group)

    def vm_console(self, ssh_user='root'):
        host = self.get_hypervisor()

        ip = host.get_ips()
        if not ip:
            raise DriverException('Hypervisor has no IP: %s' % host.name)
        ip = ip[0]

        proc = Popen('ssh -t -l %s %s "xm console %s"' % (ssh_user, ip, self.name), shell=True)
        proc.communicate()
