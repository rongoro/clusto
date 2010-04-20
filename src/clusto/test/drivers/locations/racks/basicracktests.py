
import clusto
from clusto.drivers import BasicRack, BasicServer
from clusto.test import testbase

class BasicRackTest(testbase.ClustoTestBase):

    def data(self):

        r1 = BasicRack('r1')
        r2 = BasicRack('r2')

        clusto.flush()

    def testAddingToRack(self):

        r1 = clusto.get_by_name('r1')

        s1 = BasicServer('s1')

        r1.insert(s1, 1)


        rt = clusto.get_by_name('r1')
        st = clusto.get_by_name('s1')

        self.assertEqual(len(r1.contents(subkey='ru')), 1)

        self.assertEqual(r1.contents(subkey='ru')[0].name, 's1')
        
        self.assertEqual(s1.parents(clusto_drivers=[BasicRack])[0].name, 'r1')

    def testMaxRackPosition(self):

        r1 = clusto.get_by_name('r1')

        self.assertRaises(TypeError, r1.insert, BasicServer('s1'), 400)

        self.assertRaises(TypeError, r1.insert, BasicServer('s2'), -13)

        clusto.flush()

    def testGettingThingInRack(self):

        r1 = clusto.get_by_name('r1')

        r1.insert(BasicServer('s1'), 40)

        clusto.flush()

        s1 = r1.get_device_in(40)

        self.assertEqual(s1.name, 's1')
        

    def testGettingRackAndU(self):

        r1, r2 = [clusto.get_by_name(r) for r in ['r1','r2']]

        s=BasicServer('s1')
        clusto.flush()
        r1.insert(s, 13)

        clusto.flush()

        s = clusto.get_by_name('s1')

        res = BasicRack.get_rack_and_u(s)

        
        self.assertEqual(res['rack'].name, 'r1')
        self.assertEqual(res['RU'], [13])

        res2 = BasicRack.get_rack_and_u(BasicServer('s2'))
        self.assertEqual(res2, None)

    def testCanOnlyAddToOneRack(self):
        """
        A device should only be able to get added to a single rack
        """

        
        r1, r2 = [clusto.get_by_name(r) for r in ['r1','r2']]

        s1 = BasicServer('s1')
        s2 = BasicServer('s2')
        
        r1.insert(s1, 13)
        self.assertRaises(Exception, r2.insert,s1, 1)
        
    def testCanAddADeviceToMultipleAdjacentUs(self):
        """
        you should be able to add a device to multiple adjacent RUs
        """

        r1, r2 = [clusto.get_by_name(r) for r in ['r1','r2']]

        s1 = BasicServer('s1')
        s2 = BasicServer('s2')
        
        r1.insert(s1, [1,2,3])

        clusto.flush()

        s = clusto.get_by_name('s1')

        self.assertEqual(sorted(BasicRack.get_rack_and_u(s)['RU']),
                         [1,2,3])

        self.assertRaises(TypeError, r1.insert, s2, [1,2,4])

    def testAddingToDoubleDigitLocationThenSingleDigitLocation(self):

        r1, r2 = [clusto.get_by_name(r) for r in ['r1','r2']]

        s1 = BasicServer('s1')
        s2 = BasicServer('s2')
        
        r1.insert(s1, 11)

        r1.insert(s2, 1)

        clusto.flush()

        s = clusto.get_by_name('s1')

        self.assertEqual(sorted(BasicRack.get_rack_and_u(s)['RU']),
                         [11])

        self.assertEqual(sorted(BasicRack.get_rack_and_u(s2)['RU']),
                         [1])

