import unittest
from clusto.test import testbase

import clusto
from clusto.schema import *
from clusto.drivers.base import *
from clusto.drivers import BasicDatacenter, Pool, BasicServer, IPManager
from sqlalchemy.exceptions import InvalidRequestError

class TestClustoPlain(testbase.ClustoTestBase):

    def testInitClustoIdempotent(self):

        clusto.init_clusto()
        clusto.init_clusto()
        clusto.init_clusto()
        clusto.init_clusto()

        self.assertEqual(SESSION.query(ClustoVersioning).count(), 2)



class TestClusto(testbase.ClustoTestBase):
    def data(self):

        Entity('e1')
        Entity('e2')
        Entity('e3')

        clusto.flush()


    def testClustoMeta(self):

        cm = clusto.get_by_name('clustometa')

        self.assertEqual(cm.schemaversion, VERSION)

    def testGetByName(self):

        e1 = Entity.query().filter_by(name='e1').one()

        q = clusto.get_by_name('e1')

        self.assertEqual(q, e1)

        self.assertEqual(q.name, 'e1')

    def testGetByNames(self):

        names = ['e3','e1','e2']
        entities = [clusto.get_by_name(x) for x in names]

        self.assertEqual(entities, clusto.get_by_names(names))

        self.assertEqual([clusto.get_by_name('e3'),
                          None,
                          clusto.get_by_name('e1')],
                         clusto.get_by_names(['e3', 'shouldfail', 'e1']))


    def testSimpleRename(self):

        clusto.rename('e1', 'f1')

        q = Entity.query()

        self.assertEqual(q.filter_by(name='e1').count(), 0)

        self.assertEqual(q.filter_by(name='f1').count(), 1)


    def testChangeDriver(self):

        d = Driver('d1')
        d.add_attr('foo', 1)

        self.assertEqual(d.driver, Driver._driver_name)

        self.assertRaises(Exception, setattr, d.entity, driver, 'foo')

        clusto.change_driver(d.name, BasicServer)

        self.assertRaises(DriverException, clusto.change_driver, d.name, str)

        d = clusto.get_by_name('d1')

        self.assertEqual(d.driver, BasicServer._driver_name)
        self.assertTrue(isinstance(d, BasicServer))

        self.assertEqual(d.attr_value('foo'), 1)


    def testTransactionRollback(self):

        clusto.begin_transaction()

        d1 = Entity('d1')

        clusto.get_by_name('d1')

        d2 = Entity('d2')
        clusto.rollback_transaction()


        self.assertRaises(LookupError, clusto.get_by_name, 'd1')

    def testTransactionRollback2(self):

        try:
            clusto.begin_transaction()

            c1 = Entity('c1')

            raise Exception()
        except Exception:

            clusto.rollback_transaction()

        c2 = Entity('c2')

        self.assertRaises(LookupError, clusto.get_by_name, 'c1')
        clusto.get_by_name('c2')

    def testTransactionRollback3(self):

        d1 = Entity('d1')

        clusto.begin_transaction()
        d2 = Entity('d2')
        clusto.rollback_transaction()

        clusto.get_by_name('d1')
        self.assertRaises(LookupError, clusto.get_by_name, 'd2')

    def testTransactionRollback4(self):

        d1 = Driver('d1')

        try:
            clusto.begin_transaction()

            d2 = Driver('d2')

            try:
                clusto.begin_transaction()
                d2.add_attr('foo', 'bar')

                clusto.commit()

            except:
                clusto.rollback_transaction()

            d1.add_attr('foo2', 'bar2')

            raise Exception()
            clusto.commit()
        except:
            clusto.rollback_transaction()

        self.assertEqual(d1.attrs(), [])
        self.assertRaises(LookupError, clusto.get_by_name, 'd2')


    def testTransactionCommit(self):

        try:
            clusto.begin_transaction()

            c1 = Entity('c1')
            clusto.commit()
        except Exception:
            clusto.rollback_transaction()

        clusto.get_by_name('c1')


    def testGetEntities(self):

        d1 = Driver('d1')
        dv1 = Device('dv1')
        Location('l1')
        BasicDatacenter('dc1')


        namelist = ['e1', 'e2', 'dv1']

        self.assertEqual(sorted([n.name
                                 for n in clusto.get_entities(names=namelist)]),
                         sorted(namelist))

        dl = [Driver]
        self.assertEqual(sorted([n.name
                                 for n in clusto.get_entities(clusto_drivers=dl)]),
                         sorted(['d1','e1','e2','e3']))


        tl = [Location, BasicDatacenter]
        self.assertEqual(sorted([n.name
                                 for n in clusto.get_entities(clusto_types=tl)]),
                         sorted(['l1','dc1']))

        p1 = Pool('p1')
        p2 = Pool('p2')
        p3 = Pool('p3')
        p4 = Pool('p4')

        s1 = BasicServer('s1')
        s2 = BasicServer('s2')
        s3 = BasicServer('s3')

        p1.insert(s1)
        p1.insert(s2)

        p2.insert(s2)
        p2.insert(s3)
        p2.insert(d1)

        p3.insert(s3)
        p3.insert(d1)
        p3.insert(s1)

        p4.insert(p3)


        self.assertEqual(sorted([s2,s3]),
                         sorted(clusto.get_from_pools(pools=[p2],
                                                      clusto_types=[BasicServer])))

        self.assertEqual(sorted([s2]),
                         sorted(clusto.get_from_pools(pools=[p2, 'p1'],
                                                      clusto_types=[BasicServer])))
        self.assertEqual(sorted([s3]),
                         sorted(clusto.get_from_pools(pools=['p2', 'p3'],
                                                      clusto_types=[BasicServer])))

        self.assertEqual(sorted([s1]),
                         sorted(clusto.get_from_pools(pools=['p4', 'p1'],
                                                      clusto_types=[BasicServer])))

    def testGetEntitesWithAttrs(self):

        d1 = Driver('d1')
        d2 = Driver('d2')
        d3 = Driver('d3')
        d4 = Driver('d4')

        d1.add_attr('k1', 'test')
        d2.add_attr('k1', 'testA')

        d1.add_attr('k2', number=1, subkey='A', value=67)
        d3.add_attr('k3', number=True, value=d4)



        self.assertEqual(clusto.get_entities(attrs=[{'key':'k2'}]),
                         [d1])


        self.assertEqual(sorted(clusto.get_entities(attrs=[{'key':'k1'}])),
                         sorted([d1,d2]))


        self.assertEqual(sorted(clusto.get_entities(attrs=[{'value':d4}])),
                         [d3])


        self.assertEqual(clusto.get_entities(attrs=[{'value':67}]),
                         [d1])

        self.assertEqual(sorted(clusto.get_entities(attrs=[{'number':0}])),
                         sorted([d3]))

        self.assertEqual(clusto.get_entities(attrs=[{'subkey':'A'},
                                                   {'value':'test'}]),
                         [d1])

    def testGet(self):
        s1 = BasicServer('s1')
        s2 = BasicServer('s2')
        s3 = BasicServer('s3')
        ipm = IPManager('testnet', baseip='10.0.0.0', netmask='255.255.255.0')

        s1.set_attr(key='system', subkey='serial', value='P0000000000')
        s2.set_port_attr('nic-eth', 1, 'mac', '00:11:22:33:44:55')
        s3.bind_ip_to_osport('10.0.0.1', 'eth0')

        self.assertEqual(clusto.get('s1')[0], s1)
        self.assertEqual(clusto.get('00:11:22:33:44:55')[0], s2)
        self.assertEqual(clusto.get('10.0.0.1')[0], s3)
        self.assertEqual(clusto.get('P0000000000')[0], s1)
        self.assertEqual(clusto.get('foo'), None)
        self.assertRaises(ValueError, clusto.get, None)

    def testDeleteEntity(self):

        e1 = Entity.query().filter_by(name='e1').one()

        d = Driver(e1)

        d.add_attr('deltest1', 'test')
        d.add_attr('deltest1', 'testA')



        clusto.delete_entity(e1)


        self.assertEqual([], clusto.get_entities(names=['e1']))

        self.assertEqual([], Driver.do_attr_query(key='deltest*', glob=True))



    def testDriverSearches(self):

        d = Driver('d1')

        self.assertRaises(NameError, clusto.get_driver_name, 'FAKEDRIVER')

        self.assertEqual(clusto.get_driver_name(Driver),
                         'entity')

        self.assertRaises(LookupError, clusto.get_driver_name, 123)

        self.assertEqual(clusto.get_driver_name('entity'),
                         'entity')

        self.assertEqual(clusto.get_driver_name(d.entity),
                         'entity')

    def testTypeSearches(self):

        d = Driver('d1')

        self.assertEqual(clusto.get_type_name('generic'),
                         'generic')

        self.assertEqual(clusto.get_type_name(d.entity),
                         'generic')

        self.assertRaises(LookupError, clusto.get_type_name, 123)


    def testAttributeOldVersionsInGetEntities(self):

        sl = [BasicServer('s' + str(x)) for x in range(10)]
        for n, s in enumerate(sl):
            s.add_attr(key='old', value="val")
            s.del_attrs(key='old')
            s.add_attr(key='new', value='foo')

        l=clusto.get_entities(attrs=[{'key':'old', 'value':'val'}])

        self.assertEqual(l, [])


    def testSiblings(self):

        d1 = Driver('d1')
        d2 = Driver('d2')
        d3 = Driver('d3')
        d4 = Driver('d4')
        d5 = Driver('d5')
        d6 = Driver('d6')
        d7 = Driver('d7')
        d8 = Driver('d8')

        db = Pool('db')
        web = Pool('web')
        dev = Pool('dev')
        prod = Pool('prod')
        alpha = Pool('alpha')
        beta = Pool('beta')

        db.set_attr('pooltype', 'role')
        web.set_attr('pooltype', 'role')

        db.insert(d1)
        db.insert(d2)
        db.insert(d3)
        db.insert(d7)
        db.insert(d8)

        web.insert(d4)
        web.insert(d5)
        web.insert(d6)
        web.insert(d7)

        map(prod.insert, [d1,d2,d4,d5])

        map(dev.insert, [d3,d6,d7,d8])

        map(alpha.insert, [d7, d8])
        map(beta.insert, [d3,d6])


        self.assertEquals(sorted([d2]),
                          sorted(d1.siblings()))

        self.assertEquals(sorted(d3.siblings()),
                          sorted([]))

        self.assertEquals(sorted(d3.siblings(parent_filter=lambda x: not x.attr_values('pooltype', 'role'),
                                             additional_pools=[web])),
                          sorted([d6]))

        self.assertEquals(sorted(d7.siblings(parent_filter=lambda x: not x.attr_values('pooltype', 'role'),
                                             additional_pools=[db])),
                          sorted([d8]))


    def testUnderscore(self):

        d1 = Driver('with_underscore')
        d2 = Driver('withZunderscore')

        self.assertEqual(clusto.get_by_name('with_underscore'),
                         d1)

        d1.add_attr('keyZfoo', 'bar')
        d1.add_attr('key_foo', 'baz')

        self.assertEqual(len(d1.attrs('key_foo')), 1)

        self.assertEqual(len(d1.attr_query('key_foo')), 1)
