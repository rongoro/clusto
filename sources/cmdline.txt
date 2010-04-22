######################
  Command line usage
######################

:Release: |version|
:Date: |today|

There are a number of interactive clusto commands you can use for inspecting and manipulating the database. A lot of them are broken because we haven't used them in a while. Feel free to fix them when you're done reading this doc.

clusto info
~~~~~~~~~~~
Gives a quick overview of the important attributes of an object identified by name, IP, or MAC address::

 $ clusto info s0233
 Name:                s0233
 Type:                server
 IP:                  10.2.129.191
 Parents:             sjc1-017, production, rofl-gamma, wtf-gamma, zomg-gamma-nokill

 Serial:              P1238090236
 Memory:              16 GB
 Disk:                1500 GB (3)
 CPU Cores:           8

 nic-eth(1)           mac = 00:a0:d1:e8:57:70
 nic-eth(2)           mac = 00:a0:d1:e8:57:71

clusto attr
~~~~~~~~~~~
Manipulates the attributes of an object::

 $ clusto attr add -k puppet -s class -v site::ldap-client s0245
 $ clusto attr show -m -k puppet -s class s0245
 KEY      SUBKEY     NUM    VALUE
 puppet   class      None   site::ldap-client

clusto pool
~~~~~~~~~~~
Manipulates the contents of pool objects::

 $ clusto pool create testing
 $ clusto pool insert s0245
 $ clusto pool show testing
 s0245
 $ clusto pool remove testing s0245
 $ clusto pool delete testing

clusto shell
~~~~~~~~~~~~
Probably the most powerful command for working with clusto, this command spawns an ipython shell with the clusto database connection initialized and a few clusto "builtins" imported into the local scope. This is a great way to test out new ideas, run complicated one-shot queries against clusto, or just to get more comfortable with the clusto interface. If you want to create objects, you'll have to do::

 from clusto.drivers import *

clusto tree
~~~~~~~~~~~

Outputs a tree-like listing of objects contained within other objects::

 $ clusto tree sjc1-003
 name: sjc1-003 
    name: sjc1-003-pwr1 
    name: sjc1-003-sw1  
    name: sjc1-003-ts1  
    name: s0001 
    name: s0002 
 ...
 $ clusto tree sjc1-003 name system
 name: sjc1-003 system: None    
    name: sjc1-003-pwr1 system: None    
    name: sjc1-003-sw1  system: None    
    name: sjc1-003-ts1  system: None    
    name: s0001 system: [u'P1238110062\n', 8]   
    name: s0002 system: [u'P1238110064\n', 8]   
    name: s0004 system: [u'P1238110066\n', 8]  
