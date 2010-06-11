
import clusto
from clusto.test import testbase

from clusto.drivers import (VMManager, BasicServer, BasicVirtualServer,
                            ResourceTypeException, ResourceException)


class VMManagerTest(testbase.ClustoTestBase):

    def data(self):

        vmm = VMManager('vmm')

        s1 = BasicServer('s1')
        s1.set_attr('system', subkey='memory', value=1000)
        s1.set_attr('system', subkey='disk', value=5000)
        s1.set_attr('system', subkey='cpucount', value=2)
        
        s2 = BasicServer('s2')
        s2.set_attr('system', subkey='memory', value=16000)
        s2.set_attr('system', subkey='disk', value=2500)
        s2.set_attr('system', subkey='cpucount', value=2)
        

        vmm.insert(s1)
        vmm.insert(s2)
        

    def testVMManagerAllocate(self):

        s1 = clusto.get_by_name('s1')
        s2 = clusto.get_by_name('s2')
        
        vs1 = BasicVirtualServer('vs1')
        vs1.set_attr('system', subkey='memory', value=1000)
        vs1.set_attr('system', subkey='disk', value=50)
        vs1.set_attr('system', subkey='cpucount', value=1)

        vs2 = BasicVirtualServer('vs2')
        vs2.set_attr('system', subkey='memory', value=8000)
        vs2.set_attr('system', subkey='disk', value=1000)
        vs2.set_attr('system', subkey='cpucount', value=1)

        vs3 = BasicVirtualServer('vs3')
        vs3.set_attr('system', subkey='memory', value=800)
        vs3.set_attr('system', subkey='disk', value=100)
        vs3.set_attr('system', subkey='cpucount', value=3)

        vmm = clusto.get_by_name('vmm')

        vmm.allocate(vs1)

        self.assertEqual(len(vmm.resources(vs1)), 1)

        self.assert_(vmm.resources(vs1)[0].value in [s1, s2])

        vmm.allocate(vs2)

        self.assertEqual([r.value for r in vmm.resources(vs2)], [s2])

        self.assertRaises(ResourceException, vmm.allocate, vs3)

    def testVMDestroy(self):

        vmm = clusto.get_by_name('vmm')


        vs1 = BasicVirtualServer('vs1')
        vs1.set_attr('system', subkey='memory', value=1000)
        vs1.set_attr('system', subkey='disk', value=50)
        vs1.set_attr('system', subkey='cpucount', value=2)

        vs2 = BasicVirtualServer('vs2')
        vs2.set_attr('system', subkey='memory', value=5000)
        vs2.set_attr('system', subkey='disk', value=50)
        vs2.set_attr('system', subkey='cpucount', value=2)

        vs3 = BasicVirtualServer('vs3')
        vs3.set_attr('system', subkey='memory', value=1000)
        vs3.set_attr('system', subkey='disk', value=50)
        vs3.set_attr('system', subkey='cpucount', value=1)

        s1 = clusto.get_by_name('s1')
        s2 = clusto.get_by_name('s2')
        
        vmm.allocate(vs1)
        vmm.allocate(vs2)

        self.assertRaises(ResourceException, vmm.allocate, vs3)

        vmm.deallocate(vs2)

        vmm.allocate(vs3)

        self.assertEqual([r.value for r in vmm.resources(vs3)],
                         [clusto.get_by_name('s2')])
                          
    def testVMAllocateToSpecificHost(self):

        vs1 = BasicVirtualServer('vs1')
        vs1.set_attr('system', subkey='memory', value=1000)
        vs1.set_attr('system', subkey='disk', value=50)
        vs1.set_attr('system', subkey='cpucount', value=2)

        vs2 = BasicVirtualServer('vs2')
        vs2.set_attr('system', subkey='memory', value=5000)
        vs2.set_attr('system', subkey='disk', value=50)
        vs2.set_attr('system', subkey='cpucount', value=2)

        vs3 = BasicVirtualServer('vs3')
        vs3.set_attr('system', subkey='memory', value=1000)
        vs3.set_attr('system', subkey='disk', value=50)
        vs3.set_attr('system', subkey='cpucount', value=1)

        s1 = clusto.get_by_name('s1')
        s2 = clusto.get_by_name('s2')
        s3 = BasicServer('s3')
        
        vmm = clusto.get_by_name('vmm')
        vmm.allocate(vs1, s1)

        self.assertRaises(ResourceException, vmm.allocate, vs2, s3)

        self.assertRaises(ResourceException, vmm.allocate, vs1, s1)
        self.assertRaises(ResourceException, vmm.allocate, vs1, s2)

        self.assertEqual([r.value for r in vmm.resources(vs1)],
                         [clusto.get_by_name('s1')])

        self.assertRaises(ResourceException, vmm.allocate, vs2, s1)

        self.assertEqual([r.value for r in vmm.resources(vs2)],
                         [])

        vmm.allocate(vs2, s1, force=True)

        self.assertEqual([r.value for r in vmm.resources(vs2)],
                         [clusto.get_by_name('s1')])


    def testAddingAndRemovingHosts(self):

        s1 = clusto.get_by_name('s1')
        s2 = clusto.get_by_name('s2')
        s3 = BasicServer('s3')
        s3.set_attr('system', subkey='memory', value=16000)
        s3.set_attr('system', subkey='disk', value=2500)
        s3.set_attr('system', subkey='cpucount', value=2)
        
        vmm = clusto.get_by_name('vmm')

        vs1 = BasicVirtualServer('vs1')
        vs1.set_attr('system', subkey='memory', value=1000)
        vs1.set_attr('system', subkey='disk', value=50)
        vs1.set_attr('system', subkey='cpucount', value=2)

        self.assertRaises(ResourceException, vmm.allocate, vs1, s3)

        vmm.allocate(vs1, s1)

        self.assertRaises(ResourceException, vmm.remove, s1)
        vmm.deallocate(vs1)
        vmm.remove(s1)

        vmm.insert(s3)

        vmm.allocate(vs1, s3)

    def testReservingResource(self):

        s1 = clusto.get_by_name('s1')
        s2 = clusto.get_by_name('s2')

        vmm = clusto.get_by_name('vmm')

        vs1 = BasicVirtualServer('vs1')
        vs1.set_attr('system', subkey='memory', value=1000)
        vs1.set_attr('system', subkey='disk', value=50)
        vs1.set_attr('system', subkey='cpucount', value=2)

        vmm.allocate(vmm, s1)

        self.assertRaises(ResourceException, vmm.allocate, vs1, s1)
        

class EC2VMManagerTest(testbase.ClustoTestBase):

    def data(self):

        vmm = clusto.drivers.EC2VMManager('ec2man')

        
