##################################
  Using clusto
##################################

:Release: |version|
:Date: |today|

In order to use clusto, you'll have to make it aware of your server environment. Every environment is built differently and may require different approaches to the discovery of servers and usage of clusto's features.

IPManagers for your subnets
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Clusto requires that every IP address you bind to a server must be associated with an IPManager instance for that subnet. This allows you to do dynamic allocation of addresses and associate related information (eg. netmask, broadcast) with every address. These features are especially useful when using clusto's DHCP server.

::

 from clusto.drivers import IPManager
 ipman = IPManager('subnet-dmz', baseip='192.168.20.0', netmask='255.255.252.0')

SimpleEntityNameManager
~~~~~~~~~~~~~~~~~~~~~~~
In order to automatically discover and create new server objects, Clusto needs to be able to generate new names for objects. SimpleEntityNameManagers provide an allocate(Driver) method that creates a new instance and generates a name for it.

::

 from clusto.drivers import SimpleEntityNameManager, PenguinServer

 names = SimpleEntityNameManager('servernames', basename='s', digits=4)
 server = names.allocate(PenguinServer)

This will create a new server instance with a name like "s0000"

Creating a datacenter
~~~~~~~~~~~~~~~~~~~~~
Clusto comes ready to use with Basic drivers for a variety of entities and devices most systems engineers are familiar with. These Basic drivers can be used directly if only basic functionality is desired, but are intended to be subclassed and overridden with different variables and method. It is considered a best practice to create subclasses in case you need to customize a driver later on.
This is an example of a custom datacenter driver representing a colocation facility. (src/clusto/drivers/locations/datacenters/equinixdatacenter.py)::

 from basicdatacenter import BasicDatacenter

 class EquinixDatacenter(BasicDatacenter):
 	'''
	Equinix datacenter driver
	'''

	_driver_name = 'equinixdatacenter'

Add the following to src/clusto/drivers/locations/datacenters/__init__.py::

 from equinixdatacenter import *

This subclass is an example of a simple wrapper that does not provide additional functionality beyond distinguishing this type of datacenter from another one.

At clusto's core, it's a tool for gluing together other services, protocols, and logic in a data-centric way. An example of such usage would be a method that opens a ticket with the colo provider for a remote hands action. Add the following to equinixdatacenter.py::

	from smtplib import SMTP
 	def remote_hands(self, message, priority='low', mail_server='mail.example.com', mail_from='clusto@example.com', mail_to='remotehands@datacenter.net'):
		msg = 'From: %s\r\nTo: %s\r\nSubject: Remote hands request: %s priority\r\n\r\n%s' % (mail_from, mail_to, priority, request)
		server = SMTP(mail_server)
		server.sendmail(mail_from, mail_to, request)
		server.quit()

Using clusto-shell we can instantiate our new datacenter and test the remote_hands method::

 from clusto.drivers import EquinixDatacenter

 datacenter = EquinixDatacenter('eqix-sv3')
 datacenter.remote_hands('Turn on power for new racks in my cage', priority='high')

Adding racks to the datacenter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Rack factories are fairly specific to each organization's environment... Common rack layouts are uncommon. For these types of highly-customized features, you'll need to modify the files in /var/lib/clusto to suit your needs. Clusto ships with some examples of the files used by Digg.

Take a look at /var/lib/clusto/rackfactory.py to get an idea of how to programatically define rack layouts.

Continuing our example from above, let's assume the remote hands at the datacenter plugged in your new rack and closed the ticket. Now you want to be able to manipulate the rack in clusto and start adding servers to it. Let's go back to clusto-shell::

 from clusto.drivers import APCRack

 rack = APCRack('sv3-001')
 rack.set_attr(key='racklayout', value='201001')
 datacenter = get_by_name('eqix-sv3')
 datacenter.insert(rack)

That's all you need to do to create a new rack instance and insert it into a datacenter. The set_attr for rack layout will be explained in the following section.

Rack factory
~~~~~~~~~~~~
If you have more than one rack using the same layout of devices and connections between them, clusto can ease a lot of the data entry involved with creating and populating new racks with custom RackFactory classes::

 from rackfactory import get_factory

 factory = get_factory('sv3-001')
 factory.connect_ports()

The get_factory call will get the 'sv3-001' rack instance from clusto and lookup an attribute of key='rackfactory' to determine which factory class should be used to fill in the rest of the information. The __init__ method of Digg201001RackFactory also creates network, console, and power switch instances with names based on the name of the rack.

The connect_ports method ensures that this rack is in the datacenter, that the network, console, and power instances are in this rack, and that their ports are all connected as intended. This gives us the basic structure of everything that will be identical across all racks with this layout.

Virtual machines
~~~~~~~~~~~~~~~~
Clusto supports managing virtual machines and their host environments through subclasses of VMManager. At the time of writing the only working implementation is XenVMManager.

Assuming you already have some server objects and you've installed Xen with libvirtd on those servers, with an LVM volume group named "vg0", the clusto side of things goes a bit like this::

 from clusto.drivers import XenVMManager, XenVirtualServer

 hosts = [
 	clusto.get_by_name('xenhost1')
 	clusto.get_by_name('xenhost2')
 	clusto.get_by_name('xenhost3')
 ]

 # Every hypervisor MUST have the following four attributes set
 for x in hosts:
  	x.set_attr(key='xen', subkey='volume-group', value='vg0')   # LVM VG name
 	x.set_attr(key='system', subkey='memory', value=16384)      # RAM in MB
 	x.set_attr(key='system', subkey='disk', value=2000)         # Disk in GB
 	x.set_attr(key='system', subkey='cpucount', value=8)        # Logical CPUs

 manager = XenVMManager('xenmanager')
 [manager.insert(x) for x in hosts]

Now that you have your host machines configured, allocate a new VM::

 vm = XenVirtualServer('xenvm1')
 vm.bind_ip_to_osport('192.168.1.51', 'eth0')
 vm.set_port_attr('nic-eth', 1, 'mac', '02:52:0a:00:00:01')
 vm.set_attr(key='system', subkey='memory', value=1024)
 vm.set_attr(key='system', subkey='disk', value=20)
 vm.set_attr(key='system', subkey='cpucount', value=1)
 manager.allocate(vm)

 vm.vm_create()		# Create the LVM logical volumes, define the domain
 vm.vm_start()		# Start the defined domain
 vm.vm_console()	# SSH to the host and open the VM's console
 vm.vm_stop()		# Shutdown the VM

If you already have IPManager and SimpleEntityNameManager instances setup, the command line tools should work as well::

 $ clusto vm create --disk 20 --memory 1024
 Created v1000
 $ clusto vm start v1000
