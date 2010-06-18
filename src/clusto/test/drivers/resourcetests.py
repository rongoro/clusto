import clusto
from clusto.test import testbase 
import itertools

from clusto.drivers import *

from clusto.drivers.resourcemanagers.simplenamemanager import SimpleNameManagerException


class ResourceManagerTests(testbase.ClustoTestBase):

    def testAllocate(self):

        rm = ResourceManager('test')
        d = Driver('d')

        rm.allocate(d, 'foo')

        self.assertEqual(rm.owners('foo'), [d])

    def testResourceCount(self):

        rm = ResourceManager('test')
        d = Driver('d')
        
        rm.allocate(d, 'foo')
        rm.allocate(d, 'bar')
        
        self.assertEqual(rm.count, 2)

    def testDeallocate(self):

        rm = ResourceManager('test')
        d = Driver('d')

        rm.allocate(d, 'foo')
        self.assertEqual(rm.count, 1)

        rm.deallocate(d, 'foo')
        self.assertEqual(rm.count, 0)
        self.assertEqual(rm.owners('foo'), [])

    def testGeneralDeallocate(self):

        rm = ResourceManager('test')
        d = Driver('d')

        rm.allocate(d, 'foo')
        rm.allocate(d, 'bar')
        
        self.assertEqual(rm.count, 2)
        self.assertEqual(sorted([x.value for x in rm.resources(d)]),
                         sorted(['foo', 'bar']))

        rm.deallocate(d)

        self.assertEqual(rm.count, 0)
        self.assertEqual(sorted(rm.resources(d)),
                         sorted([]))


    def testResourceAttrs(self):

        
        rm = ResourceManager('test')
        d = Driver('d')

        rm.allocate(d, 'foo')
        rm.allocate(d, 'bar')

        rm.add_resource_attr(d, 'foo', 'attr1', 10)

        self.assertEqual(rm.get_resource_attr_values(d, 'foo', 'attr1'), [10])

        rm.add_resource_attr(d, 'foo', 'attr1', 20)

        self.assertEqual(sorted(rm.get_resource_attr_values(d, 'foo', 'attr1')),
                         sorted([10, 20]))

        rm.del_resource_attr(d, 'foo', 'attr1')
        self.assertEqual(rm.get_resource_attr_values(d, 'foo', 'attr1'), [])

        rm.set_resource_attr(d,'bar', 'attr2', 1)        
        self.assertEqual(rm.get_resource_attr_values(d, 'bar', 'attr2'), [1])

        rm.set_resource_attr(d,'bar', 'attr2', 2)
        self.assertEqual(rm.get_resource_attr_values(d, 'bar', 'attr2'), [2])

    def testReserveResource(self):

        rm = ResourceManager('test')
        d = Driver('d')

        rm.allocate(d, 'foo')

        rm.allocate(rm, 'bar')
        

        self.assertRaises(ResourceException, rm.allocate, d, 'bar')
        
