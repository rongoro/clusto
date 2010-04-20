import clusto
from clusto.test import testbase 
import itertools

from clusto.drivers import *

from clusto.drivers.resourcemanagers.simplenamemanager import SimpleNameManagerException



class SimpleEntityNameManagerTests(testbase.ClustoTestBase):

    def data(self):

        n1 = SimpleEntityNameManager('foonamegen',
                                     basename='foo',
                                     digits=4,
                                     next=1,
                                     )


        n2 = SimpleEntityNameManager('barnamegen',
                                     basename='bar',
                                     digits=2,
                                     next=95,
                                     )
        
        clusto.flush()

    def testNamedDriverCreation(self):
        ngen = clusto.get_by_name('foonamegen')
        
        s1 = ngen.allocate(Driver)

        clusto.flush()

        d1 = clusto.get_by_name('foo0001')

        self.assertEquals(s1.name, d1.name)
        
    def testAllocateName(self):

        ngen = clusto.get_by_name('foonamegen')
        
        s1 = ngen.allocate(Driver)
        s2 = ngen.allocate(Driver)
        s3 = ngen.allocate(Driver)
        s4 = ngen.allocate(Driver)

        clusto.flush()

        self.assertEqual(s1.name, 'foo0001')
        self.assertEqual(s2.name, 'foo0002')
        self.assertEqual(s3.name, 'foo0003')
        self.assertEqual(s4.name, 'foo0004')

    def testNoLeadingZeros(self):

        ngen = clusto.get_by_name('barnamegen')

        s1 = ngen.allocate(Driver)
        s2 = ngen.allocate(Driver)
        s3 = ngen.allocate(Driver)
        s4 = ngen.allocate(Driver)

        clusto.flush()

        self.assertEqual(s1.name, 'bar95')
        self.assertEqual(s2.name, 'bar96')
        self.assertEqual(s3.name, 'bar97')
        self.assertEqual(s4.name, 'bar98')

    def testTooManyDigits(self):
        
        ngen = clusto.get_by_name('barnamegen')

        s1 = ngen.allocate(Driver)
        s2 = ngen.allocate(Driver)
        s3 = ngen.allocate(Driver)
        s4 = ngen.allocate(Driver)

        s5 = ngen.allocate(Driver)
        self.assertRaises(SimpleNameManagerException,
                          ngen.allocate, Driver)


    def testAllocateManyNames(self):
        
        ngen = clusto.get_by_name('foonamegen')

        for i in xrange(50):
            ngen.allocate(Driver)

        self.assertRaises(LookupError, clusto.get_by_name, 'foo0051')
        self.assertEqual(clusto.get_by_name('foo0050').name, 'foo0050')


    def testAllocateGivenName(self):

        ngen = clusto.get_by_name('foonamegen')

        d = ngen.allocate(Driver, 'testname')

        self.assertEqual(d.name, 'testname')

class SimpleNameManagerTests(testbase.ClustoTestBase):

    def data(self):
        n1 = SimpleNameManager('foonamegen',
                               basename='foo',
                               digits=4,
                               startingnum=1,
                               )

        clusto.flush()

    def testAllocateManyNames(self):
        
        ngen = clusto.get_by_name('foonamegen')

        d = Driver('foo')

        for i in xrange(50):
            ngen.allocate(d)
            
        
        self.assertEqual(len(SimpleNameManager.resources(d)), 50)
