
import clusto
from clusto.test import testbase 
import itertools

from clusto.drivers import *
from clusto.exceptions import PoolException

class PoolTests(testbase.ClustoTestBase):

    def data(self):

        d1 = Driver('d1')
        d2 = Driver('d2')

        p1 = Pool('p1')

        clusto.flush()


    def testPoolCreate(self):

        p3 = Pool('p3')
        d3 = Driver('d3')
        
        clusto.flush()

        q = clusto.get_by_name('p3')

        self.assertTrue(isinstance(q, Pool))

        self.assertFalse(isinstance(clusto.get_by_name('d3'), Pool))

    def testPoolMembers(self):

        d1, d2, p1 = map(clusto.get_by_name, ('d1', 'd2', 'p1'))
        
        p1.insert(d1)
        p1.insert(d2)
        
        clusto.flush()


        q = clusto.get_by_name('p1')

        membernames = sorted([x.name for x in p1.contents()])

        self.assertEqual(membernames, sorted(['d1','d2']))

    def testGetPools(self):

        d1, d2, p1 = [clusto.get_by_name(i) for i in ['d1', 'd2', 'p1']]

        p2 = Pool('p2')
        
        p1.insert(d1)
        p2.insert(d1)
        p1.insert(d2)


        self.assertEqual(sorted(Pool.get_pools(d1)),
                         sorted([p1,p2]))

    def testGetPoolsMultiLevel(self):

        d1, d2, p1 = [clusto.get_by_name(i) for i in ['d1', 'd2', 'p1']]

        p2 = Pool('p2')
        p3 = Pool('p3')
        p4 = Pool('p4')
        d3 = Driver('d3')
        
        p1.insert(d1)
        p2.insert(d1)
        p1.insert(d2)

        p1.insert(p3)
        p3.insert(p4)
        p4.insert(d3)

        self.assertEqual(sorted(Pool.get_pools(d1, allPools=True)),
                         sorted([p1,p2]))

                
        self.assertEqual(sorted(set(Pool.get_pools(d3, allPools=True))),
                         sorted([p1, p3, p4]))

    def testPoolsIterator(self):

        
        A = Pool('A')

        d1, d2 = [clusto.get_by_name(i) for i in ['d1', 'd2']]

        B = Pool('B')
        C = Pool('C')
        A1 = Pool('A1')
        B2 = Pool('B2')
        B1 = Pool('B1')
        C1 = Pool('C1')

        C1.insert(C)
        B1.insert(B)
        A1.insert(B)

        A1.insert(A)
        B2.insert(A)

        A.insert(d1)
        B.insert(d1)
        C.insert(d1)

        clusto.flush()

        self.assertEqual([x.name for x in Pool.get_pools(d1)],
                         [u'A', u'B', u'C', u'A1', u'B2', u'B1', u'A1', u'C1'])

        self.assertEqual([x.name for x in Pool.get_pools(d1, allPools=False)],
                         [u'A', u'B', u'C'])


    def testPoolAttrs(self):

        d1, d2, p1 = map(clusto.get_by_name, ('d1', 'd2', 'p1'))

        p1.add_attr('t1', 1)
        p1.add_attr('t2', 2)

        d1.add_attr('t3', 3)

        p1.insert(d1)
        p1.insert(d2)
        

        clusto.flush()

        d2 = clusto.get_by_name('d2')

        self.assertEqual(sorted(d2.attrs(merge_container_attrs=True)), sorted(p1.attrs()))


        self.assertEqual(sorted(['t1', 't2', 't3']),
                         sorted([x.key for x in d1.attrs(merge_container_attrs=True)]))


    def testPoolAttrsOverride(self):

        d1, d2, p1 = map(clusto.get_by_name, ('d1', 'd2', 'p1'))

        p1.add_attr('t1', 1)
        p1.add_attr('t2', 2)

        p1.insert(d1)
        d1.add_attr('t1', 'foo')
        clusto.flush()

        
    def testFilterPoolContents(self):
        
        d1, d2, p1 = map(clusto.get_by_name, ('d1', 'd2', 'p1'))

        p1.insert(d1)
        p1.insert(d2)
        p1.insert(BasicServer('s1'))
        p1.insert(BasicServer('s2'))
        p1.insert(BasicNetworkSwitch('sw1'))

        self.assertEqual(p1.contents(clusto_types=[BasicNetworkSwitch]),
                         [clusto.get_by_name('sw1')])

    def testAddToPoolMultipleTimes(self):
        
        d1, d2, p1 = map(clusto.get_by_name, ('d1', 'd2', 'p1'))

        p1.insert(d1)

        self.assertRaises(PoolException, p1.insert, d1)
        

    def testDelAttrs(self):

        d1, d2, p1 = map(clusto.get_by_name, ('d1', 'd2', 'p1'))

        p1.insert(d1)
        p1.insert(d2)

        p1.add_attr('testkey', 'foo')
        
        self.assertEqual(sorted(p1.contents()),
                         sorted([d1,d2]))

        self.assertEqual([(a.key, a.value) for a in p1.attrs()],
                         [('testkey','foo')])
        
        p1.del_attrs()

        self.assertEqual(sorted(p1.contents()),
                         sorted([d1,d2]))

        self.assertEqual(p1.attrs(), [])

        
