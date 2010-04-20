import unittest
#from clusto.schema import *
import clusto
from clusto.drivers.Network import *
from clusto.test import testbase

class TestIP(testbase.ClustoTestBase):

    def testIP(self):

        ip1 = IP('ipone')

        ip1.ip = '192.168.243.22'

        
        self.assertEqual(ip1.ip, '192.168.243.22')
        

        clusto.flush()

        ip2 = clusto.get_by_name('ipone')

        self.assertEqual(ip2.ip, '192.168.243.22')
        

    def testEmptyIP(self):

        ip1 = IP('ipone')

        self.assertEqual(ip1.ip, None)
        

class TestNetBlock(testbase.ClustoTestBase):
    pass

