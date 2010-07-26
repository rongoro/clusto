"""
Clusto schema

"""

VERSION = 3
from sqlalchemy import *
from sqlalchemy.exc import OperationalError
from sqlalchemy.exceptions import InvalidRequestError

#from sqlalchemy.ext.sessioncontext import SessionContext
#from sqlalchemy.ext.assignmapper import assign_mapper

from sqlalchemy.orm import * #Mapper, MapperExtension
from sqlalchemy.orm.mapper import Mapper

from sqlalchemy.orm import mapperlib
import sqlalchemy.sql

import re
import sys
import datetime
import clusto
from functools import wraps

try:
    import simplejson as json
except:
    import json


__all__ = ['ATTR_TABLE', 'Attribute', 'and_', 'ENTITY_TABLE', 'Entity', 'func',
           'METADATA', 'not_', 'or_', 'SESSION', 'select', 'VERSION',
           'latest_version', 'CLUSTO_VERSIONING', 'Counter', 'ClustoVersioning',
           'working_version', 'OperationalError', 'ClustoEmptyCommit']


METADATA = MetaData()


CLUSTO_VERSIONING = Table('clustoversioning', METADATA,
                          Column('version', Integer, primary_key=True),
                          Column('timestamp', TIMESTAMP, default=func.current_timestamp(), index=True),
                          Column('user', String(64), default=None),
                          Column('description', Text, default=None),
                          mysql_engine='InnoDB'

                          )

class ClustoEmptyCommit(Exception):
    pass

class ClustoSession(sqlalchemy.orm.interfaces.SessionExtension):

    def after_begin(self, session, transaction, connection):

        sql = CLUSTO_VERSIONING.insert().values(user=SESSION.clusto_user,
                                                description=SESSION.clusto_description)

        session.execute(sql)

        SESSION.clusto_description = None
        SESSION.flushed = set()

    def before_commit(self, session):

        if not any([session.is_modified(x) for x in session]) \
               and hasattr(SESSION, 'flushed') \
               and not SESSION.flushed:
            raise ClustoEmptyCommit()

    def after_commit(self, session):
        SESSION.flushed = set()

    def after_flush(self, session, flush_context):
        SESSION.flushed.update(x for x in session)


SESSION = scoped_session(sessionmaker(autoflush=True, autocommit=True,
                                      extension=ClustoSession()))


def latest_version():
    return select([func.coalesce(func.max(CLUSTO_VERSIONING.c.version), 0)])

def working_version():
    return select([func.coalesce(func.max(CLUSTO_VERSIONING.c.version),1)])

SESSION.clusto_version = working_version()
SESSION.clusto_user = None
SESSION.clusto_description = None

ENTITY_TABLE = Table('entities', METADATA,
                     Column('entity_id', Integer, primary_key=True),
                     Column('name', String(128, convert_unicode=True,
                                           assert_unicode=None),
                            nullable=False, ),
                     Column('type', String(32), nullable=False),
                     Column('driver', String(32), nullable=False),
                     Column('version', Integer, nullable=False),
                     Column('deleted_at_version', Integer, default=None),
                     mysql_engine='InnoDB'
                     )

Index('idx_entity_name_version',
      ENTITY_TABLE.c.name,
      ENTITY_TABLE.c.version,
      ENTITY_TABLE.c.deleted_at_version)

ATTR_TABLE = Table('entity_attrs', METADATA,
                   Column('attr_id', Integer, primary_key=True),
                   Column('entity_id', Integer,
                          ForeignKey('entities.entity_id'), nullable=False),
                   Column('key', String(256, convert_unicode=True,
                           assert_unicode=None),),
                   Column('subkey', String(256, convert_unicode=True,
                           assert_unicode=None), nullable=True,
                          default=None, ),
                   Column('number', Integer, nullable=True, default=None),
                   Column('datatype', String(32), default='string', nullable=False),

                   Column('int_value', Integer, default=None),
                   Column('string_value', Text(convert_unicode=True,
                           assert_unicode=None), default=None,),
                   Column('datetime_value', DateTime, default=None),
                   Column('relation_id', Integer,
                          ForeignKey('entities.entity_id'), default=None),

                   Column('version', Integer, nullable=False),
                   Column('deleted_at_version', Integer, default=None),
                   mysql_engine='InnoDB'

                   )
Index('idx_attrs_entity_version',
      ATTR_TABLE.c.entity_id,
      ATTR_TABLE.c.version,
      ATTR_TABLE.c.deleted_at_version)

Index('idx_attrs_key', ATTR_TABLE.c.key)
Index('idx_attrs_subkey', ATTR_TABLE.c.subkey)

DDL('CREATE INDEX idx_attrs_str_value on %(table)s (string_value(20))', on='mysql').execute_at("after-create", ATTR_TABLE)

DDL('CREATE INDEX idx_attrs_str_value on %(table)s ((substring(string_value,0,20)))', on='postgresql').execute_at("after-create", ATTR_TABLE)

DDL('CREATE INDEX idx_attrs_str_value on %(table)s (string_value)', on='sqlite').execute_at("after-create", ATTR_TABLE)

COUNTER_TABLE = Table('counters', METADATA,
                      Column('counter_id', Integer, primary_key=True),
                      Column('entity_id', Integer, ForeignKey('entities.entity_id'), nullable=False),
                      Column('attr_key', String(256, convert_unicode=True, assert_unicode=None)),
                      Column('value', Integer, default=0),
                      mysql_engine='InnoDB'
                      )

Index('idx_counter_entity_attr',
      COUNTER_TABLE.c.entity_id,
      COUNTER_TABLE.c.attr_key)

class ClustoVersioning(object):
    pass

class Counter(object):

    def __init__(self, entity, keyname, start=0):
        self.entity = entity
        self.attr_key = keyname

        self.value = start

        SESSION.add(self)
        SESSION.flush()

    def next(self):

        self.value = Counter.value + 1
        SESSION.flush()
        return self.value

    @classmethod
    def get(cls, entity, keyname, default=0):

        try:
            ctr = SESSION.query(cls).filter(and_(cls.entity==entity,
                                                 cls.attr_key==keyname)).one()

        except sqlalchemy.orm.exc.NoResultFound:
            ctr = cls(entity, keyname, default)

        return ctr

class ProtectedObj(object):

    ## this is a hack to make these objects immutable-ish
    writable = False

    @staticmethod
    def writer(func):
        @wraps(func)
        def newfunc(self, *args, **kwargs):
            self.writable = True
            res = func(self, *args, **kwargs)
            self.writable = False
            return res
        return newfunc

    def __setattr__(self, name, val):
        if (name.startswith('_sa_')
            or self.writable
            or name == 'writable'):
            super(ProtectedObj, self).__setattr__(name, val)
        else:
            raise Exception("Not Writable")




class Attribute(ProtectedObj):
    """Attribute class holds key/value pair

    An Attribute is a DB backed object that holds a key, number, subkey,
    and a value.

    Each Attribute is associated with an Entity.

    There can be multiple attributes with the same key, number, subkey, and/or
    value.

    Optionally you can explicitely set int_value, string_value,
    datetime_value, relation_id, and datatype.  These settings would override
    the values set by passing in 'value'.
    """

    @ProtectedObj.writer
    def __init__(self, entity, key, value=None,
                 subkey=None, number=None):

        self.entity = entity
        self.key = key

        self.value = value

        self.subkey = subkey
        self.version = working_version()
        if isinstance(number, bool) and number == True:
            counter = Counter.get(entity, key, default=-1)
            self.number = counter.next()
        elif isinstance(number, Counter):
            self.number = number.next()
        else:
            self.number = number


        SESSION.add(self)
        SESSION.flush()



    def __cmp__(self, other):

        if not isinstance(other, Attribute):
            raise TypeError("Can only compare equality with an Attribute. "
                            "Got a %s instead." % (type(other).__name__))

        return cmp(self.key, other.key)

    def __eq__(self, other):

        if not isinstance(other, Attribute):
            return False

        return ((self.key == other.key) and (self.value == other.value))

    def __repr__(self):

        params = ('key','value','subkey','number','datatype','version', 'deleted_at_version')
                  #'int_value','string_value','datetime_value','relation_id')


        vals = ((x,getattr(self,x)) for x in params)
        strs = ("%s=%s" % (key, ("'%s'" % val if isinstance(val,basestring) else '%s'%str(val))) for key, val in vals)

        s = "%s(%s)" % (self.__class__.__name__, ','.join(strs))

        return s

    def __str__(self):

        params = ('key','number','subkey','datatype',)

        val = "%s.%s %s" % (self.entity.name, '|'.join([str(getattr(self, param)) for param in params]), str(self.value))
        return val

    @property
    def is_relation(self):
        return self.datatype == 'relation'

    def get_value_type(self, value=None):
        if value == None:
            if self.datatype == None:
                valtype = "string"
            else:
                valtype = self.datatype
        else:
            valtype = self.get_type(value)

        if valtype == 'json':
            valtype = "string"
        return valtype + "_value"

    @property
    def keytuple(self):
        return (self.key, self.number, self.subkey)

    @property
    def to_tuple(self):
        return (self.key, self.number, self.subkey, self.value)

    @classmethod
    def get_type(self, value):

        if isinstance(value, (int,long)):
            if value > sys.maxint:
                raise ValueError("Can only store number between %s and %s"
                                 % (-sys.maxint-1, sys.maxint))
            datatype = 'int'
        elif isinstance(value, basestring):
            datatype = 'string'
        elif isinstance(value, datetime.datetime):
            datatype = 'datetime'
        elif isinstance(value, Entity):
            datatype = 'relation'
        elif hasattr(value, 'entity') and isinstance(value.entity, Entity):
            datatype = 'relation'
        elif isinstance(value, (list, dict)):
            datatype = 'json'
        else:
            datatype = 'string'

        return datatype


    def _get_value(self):

        if self.get_value_type() == 'relation_value':
            return clusto.drivers.base.Driver(getattr(self, self.get_value_type()))
        else:
            val = getattr(self, self.get_value_type())
            if self.datatype == 'int':
                return int(val)
            elif self.datatype == 'json':
                return json.loads(val)
            else:
                return val

    def _set_value(self, value):

        if not isinstance(value, sqlalchemy.sql.ColumnElement):
            self.datatype = self.get_type(value)
            if self.datatype == 'int':
                value = int(value)
            elif self.datatype == 'json':
                value = json.dumps(value)
                
        setattr(self, self.get_value_type(value), value)



    value = property(_get_value, _set_value)

    @ProtectedObj.writer
    def delete(self):
        ### TODO this seems like a hack

        self.deleted_at_version = working_version()

    @classmethod
    def queryarg(cls, key=None, value=(), subkey=(), number=()):

        args = [or_(cls.deleted_at_version==None,
                    cls.deleted_at_version>SESSION.clusto_version),
                cls.version<=SESSION.clusto_version]

        if key:
            args.append(Attribute.key==key)

        if number is not ():
            args.append(Attribute.number==number)

        if subkey is not ():
            args.append(Attribute.subkey==subkey)

        if value is not ():
            valtype = Attribute.get_type(value) + '_value'
            if valtype == 'relation_value':

                # get entity_id from Drivers too
                if hasattr(value, 'entity'):
                    e = value.entity
                else:
                    e = value

                args.append(getattr(Attribute, 'relation_id') == e.entity_id)

            else:
                args.append(getattr(Attribute, valtype) == value)

        return and_(*args)

    @classmethod
    def query(cls):
        return SESSION.query(cls).filter(or_(cls.deleted_at_version==None,
                                             cls.deleted_at_version>SESSION.clusto_version)).filter(cls.version<=SESSION.clusto_version)

class Entity(ProtectedObj):
    """
    The base object that can be stored and managed in clusto.

    An entity can have a name, type, and attributes.

    An Entity's functionality is augmented by Drivers which act as proxies for
    interacting with an Entity and its Attributes.
    """

    @ProtectedObj.writer
    def __init__(self, name, driver='entity', clustotype='entity'):
        """Initialize an Entity.

        @param name: the name of the new Entity
        @type name: C{str}
        @param attrslist: the list of key/value pairs to be set as attributes
        @type attrslist: C{list} of C{tuple}s of length 2
        """

        self.name = name

        self.driver = driver
        self.type = clustotype

        self.version = working_version()
        SESSION.add(self)
        SESSION.flush()

    def __eq__(self, otherentity):
        """Am I the same as the Other Entity.

        @param otherentity: the entity you're comparing with
        @type otherentity: L{Entity}
        """

        ## each Thing must have a unique name so I'll just compare those
        if not isinstance(otherentity, Entity):
            retval = False
        else:
            retval = self.name == otherentity.name

        return retval

    def __cmp__(self, other):

        if not hasattr(other, 'name'):
            raise TypeError("Can only compare equality with an Entity-like "
                            "object.  Got a %s instead."
                            % (type(other).__name__))

        return cmp(self.name, other.name)


    def __repr__(self):
        s = "%s(name=%s, driver=%s, clustotype=%s, version=%s, deleted_at_version=%s)"

        return s % (self.__class__.__name__,
                    self.name, self.driver, self.type, str(self.version), str(self.deleted_at_version))

    def __str__(self):
        "Return string representing this entity"

        return str(self.name)

    @property
    def attrs(self):
        return Attribute.query().filter(and_(Attribute.entity==self,
                                             and_(or_(ATTR_TABLE.c.deleted_at_version>SESSION.clusto_version,
                                                      ATTR_TABLE.c.deleted_at_version==None),
                                                  ATTR_TABLE.c.version<=SESSION.clusto_version))).all()

    @property
    def references(self):
        return Attribute.query().filter(and_(Attribute.relation_id==self.entity_id,
                                             and_(or_(ATTR_TABLE.c.deleted_at_version>SESSION.clusto_version,
                                                      ATTR_TABLE.c.deleted_at_version==None),
                                                  ATTR_TABLE.c.version<=SESSION.clusto_version))).all()


    def add_attr(self, *args, **kwargs):

        return Attribute(self, *args, **kwargs)

    @ProtectedObj.writer
    def delete(self):
        "Delete self and all references to self."

        clusto.begin_transaction()
        try:
            self.deleted_at_version = working_version()

            for i in self.references:
                i.delete()

            for i in self.attrs:
                i.delete()

            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x

    @classmethod
    def query(cls):
        return SESSION.query(cls).filter(or_(cls.deleted_at_version==None,
                                             cls.deleted_at_version>SESSION.clusto_version)).filter(cls.version<=SESSION.clusto_version)


    @ProtectedObj.writer
    def _set_driver_and_type(self, driver, clusto_type):
        """sets the driver and type for the entity

        this shouldn't be too dangerous, but be careful

        params:
          driver: the driver name
          clusto_type: the type name
        """

        try:
            clusto.begin_transaction()

            self.type = clusto_type
            self.driver = driver

            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x


mapper(ClustoVersioning, CLUSTO_VERSIONING)

mapper(Counter, COUNTER_TABLE,
       properties = {'entity': relation(Entity, lazy=True, uselist=False)},

       )

mapper(Attribute, ATTR_TABLE,
       properties = {'relation_value': relation(Entity, lazy=True,
                                                primaryjoin=ATTR_TABLE.c.relation_id==ENTITY_TABLE.c.entity_id,
                                                uselist=False,
                                                passive_updates=False),
                     'entity': relation(Entity, lazy=True, uselist=False,
                                        primaryjoin=ATTR_TABLE.c.entity_id==ENTITY_TABLE.c.entity_id)})


## might be better to make the relationships here dynamic_loaders in the long
## term.
mapper(Entity, ENTITY_TABLE,

       )
