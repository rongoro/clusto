
from clusto.test import testbase
import unittest

from schema import *
from drivers import *

class TestThingSchema(unittest.TestCase):

    def setUp(self):
        
        metadata.connect('sqlite:///:memory:')
        metadata.create_all()



    def tearDown(self):

        ctx.current.clear()
        metadata.dispose()


    def testThingConnections(self):
        
        t=Thing('foo1')
        t2=Thing('subfoo')
        t3=Thing('foo2')
        s=Server('serv1')

        t.connect(s)
        ctx.current.flush()

        ta1=ThingAssociation(t,t2)
        ta2=ThingAssociation(t3,t)

        ctx.current.flush()
        ctx.current.clear()
        
        f=Thing.selectone(Thing.c.name=='foo1')

        for i in f.connections:
            pass #sys.stderr.write('\n' + i.name +": " + str(i.meta_attrs) + '\n')
        self.assertEqual(len(f.connections), 3)

    def testDrivers(self):

        
        s1=Server('s1')
        s2=Server('s2')

        t1=Thing('t1')
        t2=Thing('t2')

        self.assertEqual(s1.getAttr('clustotype'), 'server')
                                 
        ctx.current.flush()

        l=Server.select()
        
        self.assertEqual(len(l), 2)

        o=Thing.select()
        self.assertEqual(len(o), 4)
        ctx.current.flush()
        
    def testAttributes(self):

        s1=Server('s4')
        
        ctx.current.flush()
        
        s=Server.selectone(Server.c.name=='s4')

        #s.attrs.append(Attribute('g',1))
        s.add_attr('g', 1)
        s.add_attr('a', 2)
        s.add_attr('b', 3)
        
        ctx.current.flush()        

        a = Attribute.select()
        self.assertEqual(len(a), 4)

        n1 = Netscaler('one1')

        self.assertEqual(n1.getAttr('vendor'), 'citrix')
        
        ctx.current.flush()

    def testOutput(self):

        s1 = Server('s5')
        s1.add_attr('version', 1)
        s1.add_attr('model', 'amd')
        
                
        s2 = Server('s6')
        s2.add_attrs([('version', 2), ('vender', 'penguin computing')])
        
        s1.connect(s2)
        
        ctx.current.flush()

        s=Server.select()

if __name__ == '__main__':
    suite = unittest.makeSuite(TestThingSchema)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
