
from clusto.test import testbase

from clusto.drivers import BasicServer, BasicRack, IPManager
from clusto.drivers import BasicNetworkSwitch, BasicPowerStrip, PowerTowerXM
from clusto.exceptions import ConnectionException
import clusto

class ServerInstallationTest(testbase.ClustoTestBase):
    """Test installing a server 

    Put the server into a rack 
    connect the server to a powerstrip and a networkswitch
    """

    def data(self):
        
        r1 = BasicRack('r1')
        
        sw1 = BasicNetworkSwitch('sw1')

        s1 = BasicServer('s1')
        
        p1 = PowerTowerXM('p1')

        r1.insert(p1, (10,11))
        r1.insert(sw1, 12)
        r1.insert(s1, 1)

    def testServerRackLocation(self):

        r = clusto.get_by_name('r1')
        s = clusto.get_by_name('s1')
        
        self.assertEqual(BasicRack.get_rack_and_u(s)['RU'], [1])

        self.assertEqual(r.get_device_in(12),
                         clusto.get_by_name('sw1'))

        self.assertEqual(r.get_device_in(10),
                         clusto.get_by_name('p1'))

        self.assertEqual(r.get_device_in(11),
                         clusto.get_by_name('p1'))
        
        

    def testPortConnections(self):

        s = clusto.get_by_name('s1')
        sw = clusto.get_by_name('sw1')
        p1 = clusto.get_by_name('p1')

        sw.connect_ports('nic-eth', 1, s, 1)
        
        
        self.assertRaises(ConnectionException,
                          s.connect_ports, 'nic-eth', 1, sw, 2)

        p1.connect_ports(porttype='pwr-nema-5',
                        srcportnum=1,
                        dstdev=s,
                        dstportnum=1)
                        
        self.assertEqual(s.get_connected('pwr-nema-5', 1),
                         p1)


    def testSettingUpServer(self):
        
        from clusto.drivers import SimpleEntityNameManager

        servernames = SimpleEntityNameManager('servernames',
                                              basename='server',
                                              digits=4
                                              )

        newserver = servernames.allocate(BasicServer)
        

        sw = clusto.get_by_name('sw1')
        p1 = clusto.get_by_name('p1')
        r = clusto.get_by_name('r1')

        self.assertEqual('server0001', newserver.name)


        self.assertRaises(TypeError, r.insert, newserver, 1)

        r.insert(newserver,2)
        p1.connect_ports('pwr-nema-5', 1, newserver, 1)
        sw.connect_ports('nic-eth', 1, newserver, 1)
        sw.connect_ports('nic-eth', 3, p1, 1)

        self.assertEqual(BasicRack.get_rack_and_u(newserver)['rack'], r)

        ipman = IPManager('subnet-10.0.0.1', netmask='255.255.255.0', baseip='10.0.0.1')

        newserver.bind_ip_to_osport('10.0.0.2', 'eth0', porttype='nic-eth', portnum=1)

        ipvals = newserver.attrs(value='10.0.0.2')
        self.assertEqual(len(ipvals), 1)

        self.assertEqual(ipvals[0].value, '10.0.0.2')

        self.assertEqual(clusto.get_by_attr('ip', '10.0.0.2'), [newserver])


        aserver = servernames.allocate(BasicServer)

        ipattr = ipman.allocate(aserver)
        
        aserver.bind_ip_to_osport(ipattr.value, 'eth0', porttype='nic-eth', portnum=1)

        ip = aserver.attr_values(ipattr.key, number=ipattr.number, subkey=ipattr.subkey)

        self.assertEqual(aserver.get_port_attr('nic-eth', 1, 'osportname'),
                         'eth0')

        self.assertEqual(len(aserver.attrs(subkey='osportname', value='eth0')),
                         2)

        self.assertEqual(aserver.attrs(IPManager._attr_name,
                                       subkey='ipstring',
                                       number=aserver.attrs(IPManager._attr_name,
                                                            subkey='osportname',
                                                            value='eth0')[0].number,
                                       )[0].value,
                         '10.0.0.1')

        ipattr2 = ipman.allocate(aserver)

        self.assertEqual(sorted(aserver.get_ips()),
                         sorted(['10.0.0.1', '10.0.0.3']))
        
        
        
        
        

        
