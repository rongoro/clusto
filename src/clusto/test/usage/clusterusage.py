from clusto.test import testbase

from clusto.drivers import BasicServer, APCRack, IPManager, Pool
from clusto.drivers import Cisco4948, PowerTowerXM, BasicDatacenter
from clusto.exceptions import ConnectionException
import clusto

class ClusterUsageTest(testbase.ClustoTestBase):
    """Test managing a cluster

    create pools, find services, query machine properties, etc.
    """

    def data(self):

        def createRack(datacenter, rackprefix):

            try:
                clusto.begin_transaction()
                r = APCRack(rackprefix)
                pwr = PowerTowerXM(rackprefix+'-pwr1', withslave=True)

                sw = Cisco4948(rackprefix+'-sw1')
                sw.connect_ports('nic-eth', 48, pwr, 1)
                pwr.connect_ports('pwr-nema-5', 'aa8', sw, 1)

                r.insert(pwr, [1,2,3,4])
                r.insert(sw, [5])

                for i in range(20):
                    s=BasicServer(rackprefix+'-s'+'%02d'%i)
                    r.insert(s, [6+i])
                    s.connect_ports('nic-eth', 1, sw, i+1)
                    s.connect_ports('pwr-nema-5', 1,
                                    pwr, 'ab'[i/10%2] + 'ab'[i/5%2] + str(i%5 + 1))
                clusto.commit()
            except Exception, x:
                clusto.rollback_transaction()
                raise x
                
            return r

        ds = map(BasicDatacenter, ['dc1', 'dc2', 'dc3'])

        for num, d in enumerate(ds):
            for i in range(1):
                rackname = 'rack-'+ str(num) + '%03d' % i
                r = createRack(d, rackname)

                d.insert(r)

        ipmans = [IPManager('block-' + x, netmask='255.255.0.0', baseip=x)
                  for x in ('10.1.0.0', '10.2.0.0', '10.3.0.0')]

        state_pools = map(Pool, ('production', 'development'))
        type_pools = map(Pool, ('webserver', 'database'))
        db_group_pools = map(Pool, ('users', 'objects', 'logs'))
        web_group_pools = map(Pool, ('frontend', 'api', 'admin'))
        
        for num, d in enumerate(ds):
            ipman = ipmans[num]
            for s in d.contents(clusto_types=[BasicServer],
                                search_children=True):
                ipman.allocate(s)
                ipman.allocate(s)
                
        
    def testGetServers(self):
        pass
