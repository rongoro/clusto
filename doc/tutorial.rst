######################
  Tutorial
######################

:Release: |version|
:Date: |today|

Setting up a development environment
------------------------------------
::

$ git clone git://github.com/digg/clusto.git
$ cd clusto
$ mkdir env
$ virtualenv env
$ source env/bin/activate
$ python setup.py install

At this point, you have a virtualenv populated with the latest clusto code. Every time you want to use the new clusto code, you'll need to do this::

$ cd clusto
$ source env/bin/activate
$ export CLUSTODSN="sqlite:////path/to/sqlite.db"

I usually edit the activate script and add the export command somewhere near the top.

Writing clusto scripts
----------------------

Initialization
~~~~~~~~~~~~~~
::

 from clusto.scripthelpers import init_script
 from clusto.drivers import *
 import clusto

 init_script()

Transactions
~~~~~~~~~~~~

Clusto stores versioning information for all objects. By default, all modifications to the clusto database are atomic. If you find yourself making a large number of related modifications at the same time, you may enclose them in a transaction so that the changeset is treated as a single version::

 try:
     clusto.begin_transaction()
     # make a bunch of changes to objects
     clusto.commit()
 except:
     clusto.rollback_transaction()

Server creation workflow
~~~~~~~~~~~~~~~~~~~~~~~~
::

 names = clusto.get_by_name('servernames')
 server = names.allocate(PenguinServer)

 # Put this server in a specific RU
 rack = clusto.get_by_name('sjc1-000')
 rack.insert(server, 1)

 # Connect eth0 to a switch port and bind a MAC address and IP
 switch = clusto.get_by_name('sjc1-000-sw1')
 server.connect_ports('nic-eth', 0, switch, 1)
 server.set_port_attr('nic-eth', 0, 'mac', '00:11:22:33:44:55')
 server.bind_ip_to_port('1.2.3.4', 'nic-eth', 0)

 # Connect power to an outlet
 power = clusto.get_by_name('sjc1-000-pwr1')
 server.connect_ports('pwr-nema-5', 0, power, 'aa1')

Add a server to a pool
~~~~~~~~~~~~~~~~~~~~~~
::

 pool = clusto.get_by_name('development')
 pool.insert(server)

Remove a server from a pool
~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

 pool.remove(server)

Set an attribute on an object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

 pool = clusto.get_by_name('n00b_read')
 pool.set_attr(key='mysql', subkey='port', value=3309)

Querying clusto
---------------

Get a list of servers in a pool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

 servers = clusto.get_by_name('production').contents(clusto_types=['server'])
 repr(servers)
 [BasicServer(name=s0014, type=server, driver=basicserver),
 BasicServer(name=s0015, type=server, driver=basicserver),
 BasicServer(name=s0016, type=server, driver=basicserver),
 BasicServer(name=s0017, type=server, driver=basicserver),
 BasicServer(name=s0018, type=server, driver=basicserver),
 BasicServer(name=s0019, type=server, driver=basicserver),
 ...

Find servers with the given IP address
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

 servers = IPManager.get_device('10.2.128.103')
 repr(servers)
 [BasicServer(name=mgmt, type=server, driver=basicserver)]

Find all IPs bound to a given server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

 iplist = clusto.get_by_name('s0000').get_ips()
 repr(iplist)
 ['10.2.128.107']
