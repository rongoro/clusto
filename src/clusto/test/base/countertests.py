import unittest
from clusto.test import testbase

import clusto
from clusto.schema import *
from clusto.drivers.base import *
from clusto.drivers import BasicDatacenter
from sqlalchemy.exceptions import InvalidRequestError

class TestClustoCounter(testbase.ClustoTestBase):

    def testCounterDefault(self):


        e = Entity('e1')
        c = Counter(e, 'key1')

        self.assertEqual(c.value, 0)

        d = Counter(e, 'key2', start=10)

        self.assertEqual(d.value, 10)

    def testCounterIncrement(self):
    
        e = Entity('e1')
        c = Counter(e, 'key1')

                         
        c.next()
        c.next()
        self.assertEqual(c.value,2)

    def testGetCounter(self):

        e = Entity('e1')

        c = Counter.get(e, 'key1')

        c.next()
        self.assertEqual(c.value, 1)


        d = Counter.get(e, 'key1', default=100)
        d.next()
        self.assertEqual(d.value, 2)

        f = Counter.get(e, 'key2', default=20)
        self.assertEqual(f.value, 20)

