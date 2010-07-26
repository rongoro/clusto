"""
Test the basic Entity object
"""

import unittest
from clusto.test import testbase
import datetime

import clusto
from clusto.schema import *

class TestEntitySchema(testbase.ClustoTestBase):

    def testCreateEntityObject(self):

        curver = clusto.get_latest_version_number()

        e1 = Entity('e1')
        e2 = Entity('e2')

        res = Entity.query().filter_by(name='e1')

        self.assertEqual(res.count(),1)

        e = res.all()[0]

        self.assertEqual(e.name, 'e1')


    def testOutputEntityObject(self):

        expectedout = "e1"
        
        e1 = Entity('e1')

        self.assertEqual(str(e1), expectedout)

        clusto.flush()

        self.assertEqual(str(Entity.query().filter_by(name='e1')[0]), expectedout)
        

    def testDeleteEntity(self):

        e1 = Entity('e1')

        clusto.flush()

        self.assertEqual(Entity.query().filter_by(type='entity').count(), 1)

        e1.delete()

        clusto.flush()

        self.assertEqual(Entity.query().filter_by(type='entity').count(), 0)
    
class TestEntityAttributes(testbase.ClustoTestBase):

    def data(self):

        Entity('e1')
        Entity('e2')
        Entity('e3')

        clusto.flush()

    def testAddingAttribute(self):

        e = Entity.query().filter_by(name='e2').one()

        e1 = Entity.query().filter_by(name='e1').one()

                
        self.assertEqual(e.name, 'e2')

        e.add_attr(key='one', value=1)
        e.add_attr(key='two', value=2)

        clusto.flush()

        q = Attribute.query().filter_by(entity_id=e.entity_id,
                                               key='two').one() 
        self.assertEqual(q.value, 2)

        q = Attribute.query().filter_by(entity_id=e.entity_id,
                                               key='one').one()

        self.assertEqual(q.value, 1)
        

    def testAddingDateAttribute(self):

        e1 = Entity.query().filter_by(name='e1').one()

        d = datetime.datetime(2007,12,16,7,46)
        
        e1.add_attr('somedate', d)

        clusto.flush()

        q = Attribute.query().filter_by(entity_id=e1.entity_id,
                                               key='somedate').one()

        self.assertEqual(q.value, d)
        
    def testData(self):

        q = Entity.query().\
               filter(not_(Entity.type=='clustometa')).count()

        self.assertEqual(q, 3)
        
    def testEmptyAttributes(self):
        """
        If I set no attributes there shouldn't be any in the DB except the
        clusto meta attributes
        """
        
        q = Attribute.query().join('entity').\
               filter(not_(Entity.type=='clustometa')).count()

        self.assertEqual(q, 0)
        
    def testRelationAttribute(self):

        e1 = Entity.query().filter_by(name='e1').one()
        
        e4 = Entity('e4')
        e4.add_attr(key='e1', value=e1)
        
        clusto.flush()


        e4 = Entity.query().filter_by(name='e4').one()

        attr = e4.attrs[0]

        self.assertEqual(attr.relation_value, e1)

    def testStringAttribute(self):

        e2 = Entity.query().filter_by(name='e2').one()

        e2.add_attr(key='somestring', value='thestring')

        clusto.flush()

        q = Attribute.query().filter_by(entity=e2,
                                               key='somestring').one()

        self.assertEqual(q.value, 'thestring')

    def testJSONAttribute(self):

        e2 = Entity.query().filter_by(name='e2').one()

        e2.add_attr(key="somejson", value=['foo', 'bar'])

        clusto.flush()

        q = Attribute.query().filter_by(entity=e2,
                                        key='somejson').one()

        self.assertEqual(q.value, ['foo', 'bar'])

        e2.add_attr(key="otherjson", value={'foo':200, 'bar':'test'})

        q = Attribute.query().filter_by(entity=e2,
                                        key="otherjson").one()

        self.assertEqual(q.value, {'foo':200, 'bar':'test'})

    def testIntAttribute(self):

        e4 = Entity('e4')
        e4.add_attr(key='someint', value=10)

        clusto.flush()

        q = Attribute.query().filter_by(entity=e4,
                                               key='someint').one()

        self.assertEqual(q.value, 10)

    def testMultipleAttributes(self):

        e2 = Entity.query().filter_by(name='e2').one()

        e2.add_attr(key='somestring', number=1, subkey='foo',
                                   value='thestring')

        e2.add_attr(key='somestring', number=1, subkey='foo',
                                   value='thestring')


        clusto.flush()

        q = Attribute.query().filter_by(entity=e2,
                                               key='somestring').all()

        self.assertEqual([a.value for a in q], 
                         ['thestring', 'thestring'])

    def testEntityDeleteRelations(self):

        e1 = Entity.query().filter_by(name='e1').one()
        e2 = Entity.query().filter_by(name='e2').one()

        e1.add_attr('pointer1', e2)

        clusto.flush()

        self.assertEqual(Entity.query().\
                            filter_by(type='entity').count(),
                         3)

        self.assertEqual(Attribute.query().\
                            filter(and_(Entity.entity_id==Attribute.entity_id,
                                        Entity.type=='entity',
                                        
                                        )).count()
                         , 1)

        e2new = Entity.query().filter_by(name='e2').one()

        e2new.delete()

        self.assertEqual(Entity.query().\
                            filter_by(type='entity').count(),
                         2)
        
        self.assertEqual(Attribute.query().\
                            filter(and_(Entity.entity_id==Attribute.entity_id,
                                        Entity.type=='entity')).count(),
                         0)

        clusto.flush()

        self.assertEqual(Entity.query().\
                            filter_by(type='entity').count(),
                         2)
        self.assertEqual(Attribute.query().\
                            filter(and_(Entity.entity_id==Attribute.entity_id,
                                        Entity.type=='entity')).count(),
                         0)


    def testAccessRelationAttributesMultipleTimes(self):
        e1 = Entity.query().filter_by(name='e1').one()
        e2 = Entity.query().filter_by(name='e2').one()

        e1.add_attr('foo', 2)
        e1.add_attr('foo', e2)

        clusto.flush()
        e1 = Entity.query().filter_by(name='e1').one()
        self.assertEqual(len(list(e1.attrs)), 2)
        self.assertEqual(len(list(e1.attrs)), 2)
        self.assertEqual(len(list(e1.attrs)), 2)

        
    
class TestEntityReferences(testbase.ClustoTestBase):

    def data(self):
        
        e1 = Entity('e1')
        e2 = Entity('e2')
        e3 = Entity('e3')

        e3.add_attr(key='e1', value=e1)
        e3.add_attr(key='e2', value=e2)

        clusto.flush()
    
    def testReference(self):

        e1 = Entity.query().filter_by(name='e1').one()
        e2 = Entity.query().filter_by(name='e2').one()
        e3 = Entity.query().filter_by(name='e3').one()

        self.assertEqual(e1.references[0].entity,
                         e2.references[0].entity)

        self.assertEqual(e3,
                         e2.references[0].entity)

    def testReferenceDelete(self):

        e1 = Entity.query().filter_by(name='e1').one()


        e3 = Entity.query().filter_by(name='e3').one()

        
        e3.delete()

        self.assertEqual(len(list(e1.references)), 0)

        clusto.flush()

        e1a = Entity.query().filter_by(name='e1').one()

        self.assertEqual(len(list(e1a.references)), 0)
        self.assertEqual(id(e1a), id(e1))

        e2 = Entity.query().filter_by(name='e2').one()

        self.assertEqual(len(list(e2.references)), 0)

