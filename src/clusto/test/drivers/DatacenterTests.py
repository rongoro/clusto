
import clusto
from clusto.test import testbase

from clusto.drivers.Base import Thing
from clusto.drivers.Servers import Server
from clusto.drivers.Datacenter import Rack, RackU, Datacenter, Colo, Cage
from clusto.exceptions import *

class RackTests(testbase.ClustoTestBase):

    def testAddToRack(self):

        rackname = 'ashrack101'
        rack = Rack(rackname)

        t1 = Thing('foo1')

        rack.addToRack(t1, [23,24])

        clusto.flush()

        tp = clusto.get_by_name('foo1')

        theRack = tp.get_connectedByType(Rack)

        self.assert_(theRack[0].name == rackname)

    def testRackContents(self):

        rackname = 'ashrack101'

        rack = Rack(rackname)

        t1 = Thing('t1')
        t2 = Thing('t2')
        t3 = Thing('t3')

        rack.addToRack(t3, [1,2])
        rack.addToRack(t2, [32])
        rack.addToRack(t1, [23,24,25])

        clusto.flush()

        contents = rack.getRackContents()

        self.assert_(contents[1].name == contents[2].name =='t3')
        self.assert_(contents[32].name == 't2')
        self.assert_(contents[23].name == contents[24].name
                     == contents[25].name == 't1')

        t1.delete()

        clusto.flush()

        rack = clusto.get_by_name(rackname)
        contents = rack.getRackContents()
        clusto.flush()
        
        self.assertEqual(len(contents), 3)
        

    def testRackUMissingArg(self):

        # correct 
        RackU('foo2', 3)

        # missing RU number
        self.assertRaises(TypeError, RackU, 'foo') 



class Datacentertest(testbase.ClustoTestBase):
    """
    Test Datacenter Driver
    """

    def testLocationRequirement(self):

        d = Datacenter('d1', 'san francisco')
        clusto.flush()

        z = clusto.get_by_name('d1')

        self.assert_(z.getAttr('location') == 'san francisco')

    def testDatacenterThingStack(self):

        d = Datacenter('d1', 'footown')

        co = Colo('colo1')
        ca = Cage('cage1')

        ra = Rack('rack1')

        s = Server('s1')

        d.connect(co)
        co.connect(ca)
        ca.connect(ra)

        clusto.flush()

        # can't connect a server to a datacenter
        self.assertRaises(ConnectionException, d.connect, s)
        
