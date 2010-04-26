##################################
  Services
##################################

:Release: |version|
:Date: |today|

DHCP server
~~~~~~~~~~~
As clusto acts as a single source of truth about your network, it only makes sense that you would use it for assigning network configuration to servers. Clusto's DHCP server isn't really dynamic though, it only hands out IPs that are already bound to server objects in the database and ignores DHCP requests from hosts that don't exist in the database or don't have IPs bound, though in both cases it will log a warning with details.

The design of clusto-dhcpd is a bit different from the other daemons in that it communicates with the clusto database entirely over HTTP via the clusto-httpd daemon. This method was used to avoid the transfer of large result sets from the database to the DHCP server when certain queries took place (eg. IPManager.get_ip_manager), only to have the results filtered later on. Admittedly, this is due to inefficient querying by the clusto library and will probably be fixed in a later release.

Configuration options
---------------------
*api_url*
The base URL of the clusto-httpd server. Must NOT include a trailing slash

*update_ipmi*
Boolean that sets whether or not requests will be checked for a client_id that resembles an IPMI card and distinguish it from a normal server MAC. If you don't have IPMI cards that use the same physical interfaces as your eth0, you probably don't need this.

*extra_options*
Specify custom options that can be set via clusto attributes, in addition to those already supported by scapy. This is a dict where the key is an integer option ID and the value is a name to map to that option, to be used later as a subkey.

Usage
-----
Upon receiving a DHCP request packet, clusto-dhcpd will look for any server object in the database with a Attribute(key='port-nic-eth', subkey='mac', value='00:11:22:33:44:55', number=1). If no object is found, the request is ignored. Otherwise, the daemon queries Attribute(key='dhcp', subkey='enabled', value=1, merge_container_attrs=True). This attribute is merged so that you can enable DHCP at a pool or datacenter level, depending on your needs. If the enabled attribute is found, the daemon builds a response based upon any remaining key='dhcp' attributes, including those merged from the parents. More specific attributes take precedence.

Example
-------
::

 p = Pool('pxeboot-servers')
 p.set_attr(key='dhcp', subkey='enabled', value=1)
 p.set_attr(key='dhcp', subkey='tftp_server', value='192.168.1.1')
 p.set_attr(key='dhcp', subkey='tftp_filename', value='/pxelinux.0')
 p.set_attr(key='dhcp', subkey='domain', value='example.org')

 s = BasicServer('ex0000')
 s.set_port_attr('nic-eth', 1, 'mac', '00:11:22:33:44:55')
 s.bind_ip_to_osport('192.168.1.50', 'eth0')

SNMP trap listener
~~~~~~~~~~~~~~~~~~
One of the services that ships with clusto called clusto-snmptrapd, will listen for SNMP traps from Cisco switches implementing the CISCO-MAC-NOTIFICATION-MIB which can be enabled with the following configuration on supported IOS releases::

 snmp-server enable traps mac-notification change
 snmp-server host <ip> version 2c <community>  mac-notification
 mac address-table notification change
 !
 interface <int>
   snmp trap mac-notification change added

When clusto-snmptrapd receives one of these traps, it gathers the IP of the switch, the port number, the VLAN that learned the MAC, and the MAC itself. It then queries the clusto database for the switch IP and checks for an attribute of key='snmp', subkey='discovery', value=1... If this attribute is set on the switch or any of it's parents, the daemon checks to see if there's an object connected to the switch port in clusto. If not, then we assume this is a new server and create a new PenguinServer object with a name generated from a SimpleEntityNameManager called 'servernames'. The daemon then gets the switch's parent rack, gets the rack factory for that rack, then calls add_server(server, switchport) on the rack factory instance.

It's a bit of a complicated process, but the end result is that new servers get added to clusto automatically as soon as they appear on the network without any human intervention aside from creating the rack instance.
