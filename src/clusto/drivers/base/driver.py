"""Driver class

A Driver provides an interface to an Entity and its Attributes.
"""

import re
import itertools

import clusto
from clusto.schema import *
from clusto.exceptions import *

from clusto.drivers.base.clustodriver import *


class Driver(object):
    """Base Driver.

    The Driver class provides a proxy interface for managing and Entity and
    its Attributes. It provides many helper functions includeing attribute
    setters and accessors, attribute querying, and a handful of conventions.

    Every driver defines a _clusto_type and a _driver_name member variable.
    Upon creation these become the type and driver for the Entity and provides
    a mechanism for choosing the correct driver for a given Entity.

    A Driver can be created by passing either the name (a string) for a new
    Entity you'd like to create, an already instantiated Entity object, or a
    Driver object (which has already been instantiated and is managing an
    Entity).

    If a _properties member dictionary is defined they will be treated as
    default values for the given Entity attributes as well as exposed via a
    simpler mydriver.key access pattern.  So for:

    >>> class MyDriver(Driver):
    >>>    ...
    >>>    _properties = {'propA': 10, 'propB': "default1"}
    >>>    ...

    >>> d = MyDriver('foo')
    >>> d.propA == 10
    True
    
    >>> d.propB == "default1"
    True

    Only properties with non-None default values are set in the clusto db at
    initial instantiation time (when creating a brand new entity).

    >>> d.propA = 54
    >>> d.propA == 54
    True

    Several conventions are also exposed via the Driver interface.  
    
    """
    
    __metaclass__ = ClustoDriver

    _clusto_type = "generic"
    _driver_name = "entity"

    _properties = dict()


    @property
    def type(self):
        return self.entity.type

    @property
    def driver(self):
        return self.entity.driver

    def __new__(cls, name_driver_entity, **kwargs):

        if isinstance(name_driver_entity, Driver):
            return name_driver_entity
        else:
            return object.__new__(cls, name_driver_entity, **kwargs)

    def __init__(self, name_driver_entity, **kwargs):

        if not isinstance(name_driver_entity, (str, unicode, Entity, Driver)):
            raise TypeError("First argument must be a string, "
                            "Driver, or Entity.")

        if isinstance(name_driver_entity, Driver):
            return 

        if isinstance(name_driver_entity, Entity):
            
            self.entity = name_driver_entity
            self._choose_best_driver()
            return
        elif isinstance(name_driver_entity, (str, unicode)):

            try:
                existing = clusto.get_by_name(name_driver_entity)
            except LookupError, x:
                existing = None
            
            if existing:
                raise NameException("Driver with the name %s already exists."
                                    % (name_driver_entity))


            self.entity = Entity(name_driver_entity,
                                 driver=self._driver_name,
                                 clustotype=self._clusto_type)


        else:
            raise TypeError("Could not create driver from given arguments.")

        for key, val in self._properties.iteritems():
            if key in kwargs:
                val = kwargs[key]
            if val is None:
                continue
            setattr(self, key, val)


    def __eq__(self, other):

        if isinstance(other, Entity):
            return self.entity.name == other.name
        elif isinstance(other, Driver):
            return self.entity.name == other.entity.name
        else:
            return False

    def __repr__(self):

        s = "%s(name=%s, type=%s, driver=%s)"

        return s % (self.__class__.__name__, self.entity.name, 
                    self.entity.type, self.entity.driver)

    def __cmp__(self, other):

        if hasattr(other, 'name'):
            return cmp(self.name, other.name)
        elif other is None:
            return 1
        else:
            raise TypeError("Cannot compare %s with %s", type(self), type(other))

    def __hash__(self):
        return hash(self.entity.name)

    def __contains__(self, other):
        return self.has_attr(key="_contains", value=other)
    
    def _choose_best_driver(self):
        """
        Examine the attributes of our entity and set the best driver class and
        mixins.
        """

        self.__class__ = DRIVERLIST[self.entity.driver]
    
        

    name = property(lambda x: x.entity.name)


    def _check_attr_name(self, key):
        """
        check to make sure the key does not contain invalid characters
        raise NameException if fail.
        """

        if not isinstance(key, basestring):
            raise TypeError("An attribute name must be a string.")

        if not re.match('^[A-Za-z_]+[0-9A-Za-z_-]*$', key):

            raise NameException("Attribute name %s is invalid. "
                                "Attribute names may not contain periods or "
                                "comas." % key)
    

    def __getattr__(self, name):
        if name in self._properties:                
            attr = self.attr_query(name, subkey='property')
            if not attr:
                return self._properties[name]
            else:
                return attr[0].value
        else:
            raise AttributeError("Attribute %s does not exist." % name)


    def __setattr__(self, name, value):

        if name in self._properties:
            self.set_attr(name, value, subkey='property')
        else:
            object.__setattr__(self, name, value)
        
    @classmethod
    def ensure_driver(self, obj, msg=None):
        """Ensure that the given argument is a Driver.

        If the object is an Entity it will be turned into a Driver and then
        returned.  If it's a Driver it will be returned unaffected.  Otherwise
        a TypeError is raised with either a generic or given message.
        """
        
        if isinstance(obj, Entity):
            d = Driver(obj)
        elif isinstance(obj, Driver):
            d = obj
        else:
            if not msg:
                msg = "Not a Driver."
            raise TypeError(msg)

        return d
        
    @classmethod
    def do_attr_query(cls, key=(), value=(), number=(),
                    subkey=(), ignore_hidden=True, sort_by_keys=False, 
                    glob=False, count=False, querybase=None, return_query=False,
                    entity=None):
        """Does queries against all Attributes using the DB."""

        clusto.flush()
        if querybase:
            query = querybase 
        else:
            query = Attribute.query()

        ### This is bunk, gotta fix it
        if isinstance(cls, Driver):
            query = query.filter(and_(Attribute.entity_id==Entity.entity_id,
                                      Entity.driver == cls._driver_name,
                                      Entity.type == cls._clusto_type))

        if entity:
            query = query.filter_by(entity_id=entity.entity_id)

        if key is not ():
            if glob:
                query = query.filter(Attribute.key.like(key.replace('*', '%')))
            else:
                query = query.filter_by(key=key)

        if subkey is not ():
            if glob and subkey:
                query = query.filter(Attribute.subkey.like(subkey.replace('*', '%')))
            else:
                query = query.filter_by(subkey=subkey)

        if value is not ():
            typename = Attribute.get_type(value)

            if typename == 'relation':
                if isinstance(value, Driver):
                    value = value.entity.entity_id
                query = query.filter_by(relation_id=value)

            else:
                query = query.filter_by(**{typename+'_value':value})

        if number is not ():
            if isinstance(number, bool):
                if number == True:
                    query = query.filter(Attribute.number != None)
                else:
                    query = query.filter(Attribute.number == None)
            elif isinstance(number, (int, long)):
                query = query.filter_by(number=number)
                
            else:
                raise TypeError("number must be either a boolean or an integer.")

        if ignore_hidden:
            query.filter(not_(Attribute.key.like('_%')))

        if sort_by_keys:
            query = query.order_by(Attribute.key)

        if count:
            return query.count()

        if return_query:
            return query

        return query.all()

    def attr_query(self, *args, **kwargs):
        """Queries all attributes of *this* entity using the DB."""
        
        kwargs['entity'] = self.entity

        return self.do_attr_query(*args, **kwargs)

    @classmethod
    def attr_filter(cls, attrlist, key=(), value=(), number=(), 
                   subkey=(), ignore_hidden=True, 
                   sort_by_keys=True, 
                   regex=False, 
                   clusto_types=None,
                   clusto_drivers=None,
                   ):
        """Filter attribute lists. (Uses generator comprehension)

        Given a list of Attributes filter them based on exact matches of key,
        number, subkey, value.

        There are some special cases:

        if number is True then the number variable must be non-null. if
        number is False then the number variable must be null.

        if ignore_hidden is True (the default) then filter out keys that begin
        with an underscore, if false don't filter out such keys.  If you
        specify a key that begins with an underscore as one of the arguments
        then ignore_hidden is assumed to be False.

        if sort_by_keys is True then attributes are returned sorted by keys,
        otherwise their order is undefined.

        if regex is True then treat the key, subkey, and value query
        parameters as regular expressions.

        clusto_types is a list of types that the entities referenced by
        relation attributes must match.

        clusto_drivers is a list of drivers that the entities referenced by
        relation attributes must match.
        """


        result = attrlist

        def subfilter(attrs, val, name):
            
            if regex:
                testregex = re.compile(val)
                result = (attr for attr in attrs 
                          if testregex.match(getattr(attr, name)))

            else:
                result = (attr for attr in attrs
                          if getattr(attr, name) == val)


            return result

        parts = ((key, 'key'), (subkey, 'subkey'), (value, 'value'))
        argattr = ((val,name) for val,name in parts if val is not ())

        for v, n in argattr:
            result = subfilter(result, v, n)


        if number is not ():
            if isinstance(number, bool) or number is None:
                if number:
                    result = (attr for attr in result if attr.number is not None)
                else:
                    result = (attr for attr in result if attr.number is None)

            elif isinstance(number, (int, long)):
                result = (attr for attr in result if attr.number == number)
            
            else:
                raise TypeError("number must be either a boolean or an integer.")

                    
        if value:
            result = (attr for attr in result if attr.value == value)


        if key and key.startswith('_'):
            ignore_hidden = False

        if ignore_hidden:
            result = (attr for attr in result if not attr.key.startswith('_'))

        if clusto_drivers:
            cdl = [clusto.get_driver_name(n) for n in clusto_drivers]
            result = (attr for attr in result if attr.is_relation and attr.value.entity.driver in cdl)

        if clusto_types:
            ctl = [clusto.get_type_name(n) for n in clusto_types]
            result = (attr for attr in result if attr.is_relation and attr.value.entity.type in ctl)
            
        if sort_by_keys:
            result = sorted(result)

        
        return list(result)

    def _itemize_attrs(self, attrlist):
        return [(x.keytuple, x.value) for x in attrlist]
        
    def attrs(self, *args, **kwargs):
        """Return attributes for this entity.

        (filters whole attribute list as opposed to querying the db directly)
        """

        if 'merge_container_attrs' in kwargs:
            merge_container_attrs = kwargs.pop('merge_container_attrs')
        else:
            merge_container_attrs = False

        attrs = self.attr_filter(self.entity.attrs, *args, **kwargs) 

        if merge_container_attrs:
            kwargs['merge_container_attrs'] = merge_container_attrs
            for parent in self.parents():
                attrs.extend(parent.attrs(*args,  **kwargs))

        return attrs

    def attr_values(self, *args, **kwargs):
        """Return the values of the attributes that match the given arguments"""

        return [k.value for k in self.attrs(*args, **kwargs)]

    def attr_value(self, *args, **kwargs):
        """Return a single value for the given arguments or the default if none exist

        extra parameters:
          default - the default value to return if none exist
        """
        
        if 'default' in kwargs:
            default = kwargs.pop('default')
        else:
            default = None
            
        vals = self.attr_values(*args, **kwargs)

        if vals:
            if len(vals) != 1:
                raise DriverException("args match more than one value")         
            return vals[0]
        else:            
            return default
        
    def references(self, *args, **kwargs):
        """Return the references to this Thing. The references are attributes. 

        Accepts the same arguments as attrs().

        The semantics of clusto_types and clusto_drivers changes to match the
        clusto_type or clusto_driver of the Entity that owns the attribute as
        opposed to the Entity the attribute refers to.
        """

        
        clusto_drivers = kwargs.pop('clusto_drivers', None)
            
        clusto_types = kwargs.pop('clusto_types', None)
        
        result = self.attr_filter(self.entity.references, *args, **kwargs)

        if clusto_drivers:
            cdl = [clusto.get_driver_name(n) for n in clusto_drivers]
            result = (attr for attr in result if attr.entity.driver in cdl)

        if clusto_types:
            ctl = [clusto.get_type_name(n) for n in clusto_types]
            result = (attr for attr in result if attr.entity.type in ctl)


        return list(result)

    def referencers(self, *args, **kwargs):
        """Return the Things that reference _this_ Thing.
        
        Accepts the same arguments as references() but adds an instanceOf filter
        argument.
        """
        
        refs = [Driver(a.entity) for a in sorted(self.references(*args, **kwargs),
                                                 lambda x,y: cmp(x.attr_id,
                                                                 y.attr_id))]

        return refs

                   
    def attr_keys(self, *args, **kwargs):

        return [x.key for x in self.attrs(*args, **kwargs)]

    def attr_key_tuples(self, *args, **kwargs):

        return [x.keytuple for x in self.attrs(*args, **kwargs)]

    def attr_items(self, *args, **kwargs):
        return self._itemize_attrs(self.attrs(*args, **kwargs))

    def add_attr(self, key, value=(), number=(), subkey=()):
        """add a key/value to the list of attributes

        if number is True, create an attribute with the next available
        otherwise number just gets passed to the Attribute constructor so it
        can be an integer or an sqlalchemy expression
        
        An optional subkey can also be specified. Subkeys don't affect
        numbering by default.
        """

        if isinstance(key, Attribute):
            raise Exception("Unsupported Operation.  You can no longer add an attribute directly")
        
        self._check_attr_name(key)
        if subkey:
            self._check_attr_name(subkey)

        if isinstance(value, Driver):
            value = value.entity

        if (number is ()) or (number is False):
            number = None
        if subkey is ():
            subkey = None


        return self.entity.add_attr(key, value, subkey=subkey, number=number)


    def del_attrs(self, *args, **kwargs):
        "delete attribute with the given key and value optionally value also"

        clusto.flush()
        try:
            clusto.begin_transaction()
            for i in self.attr_query(*args, **kwargs):
                i.delete()
            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x


    def set_attr(self, key, value, number=False, subkey=None):
        """replaces all attributes with the given key"""        
        self._check_attr_name(key)

        attrs = self.attrs(key=key, number=number, subkey=subkey)

        if len(attrs) > 1:
            raise DriverException("cannot set an attribute when args match more than one value")

        else:
            if len(attrs) == 1:
                if attrs[0].value == value:
                    return attrs[0]
                self.del_attrs(key=key, number=number, subkey=subkey)

            attr = self.add_attr(key, value, number=number, subkey=subkey)

        return attr        

    
    def has_attr(self, *args, **kwargs):
        """return True if this list has an attribute with the given key"""

        if self.attr_query(*args, **kwargs):
            return True

        return False
    
    def insert(self, thing):
        """Insert the given Enity or Driver into this Entity.  Such that:

        >>> A.insert(B)
        >>> (B in A) 
        True


        """
        
        d = self.ensure_driver(thing, 
                              "Can only insert an Entity or a Driver. "
                              "Tried to insert %s." % str(type(thing)))


        parent = thing.parents()

        if parent:
            raise TypeError("%s is already in %s and cannot be inserted into %s."
                            % (d.name, parent[0].entity.name, self.name))

        self.add_attr("_contains", d, number=True)
        
    def remove(self, thing):
        """Remove the given Entity or Driver from this Entity. Such that:
        
        >>> A.insert(B)
        >>> B in A
        True
        >>> A.remove(B)
        >>> B in A
        False

        """
        if isinstance(thing, Entity):
            d = Driver(Entity)
        elif isinstance(thing, Driver):
            d = thing
        else:
            raise TypeError("Can only remove an Entity or a Driver. "
                            "Tried to remove %s." % str(type(thing)))


        self.del_attrs("_contains", d, ignore_hidden=False)

    def content_attrs(self, *args, **kwargs):
        """Return the attributes referring to this Thing's contents

        """

        attrs = self.attrs("_contains", *args, **kwargs) 

        return attrs

    def contents(self, *args, **kwargs):
        """Return the contents of this Entity.  Such that:

        >>> A.insert(B)
        >>> A.insert(C)
        >>> A.contents()
        [B, C]
        
        """

        if 'search_children' in kwargs:
            search_children = kwargs.pop('search_children')
        else:
            search_children = False

        contents = [attr.value for attr in self.content_attrs(*args, **kwargs)]
        if search_children:
            for child in (attr.value for attr in self.content_attrs()):
                kwargs['search_children'] = search_children
                contents.extend(child.contents(*args, **kwargs))

        return contents

    def parents(self, **kwargs):        
        """Return a list of Things that contain _this_ Thing. """

        search_parents = kwargs.pop('search_parents', False)

        if search_parents:
            parents=self.parents(**kwargs)
            allparents = self.parents()
            for thing in allparents:
                allparents.extend(thing.parents())

            for thing in allparents:
                parents.extend(thing.parents(**kwargs))
        else:
            parents = self.referencers('_contains', **kwargs)

        return parents

    def siblings(self, parent_filter=None, parent_kwargs=None,
                 additional_pools=None, **kwargs):
        """Return a list of Things that have the same parents as me.

        parameters:
           parent_filter - a function used to filter out unwanted parents
           parent_kwargs - arguments to be passed to self.parents()
           additional_pools - a list of additional pools to use as sibling parents
           **kwargs - arguments to clusto.get_from_pools()
        """

        if parent_kwargs is None:
            parent_kwargs = dict(clusto_types=[clusto.drivers.Pool])
            
        parents = self.parents(**parent_kwargs)

        if parent_filter:
            parents = filter(parent_filter, parents)
            
        if additional_pools:
            parents.extend(additional_pools)

        return [s for s in clusto.get_from_pools(parents, **kwargs) if s != self]

    @classmethod
    def get_by_attr(cls, *args, **kwargs):
        """Get list of Drivers that have by attributes search """
        
        attrlist = cls.do_attr_query(*args, **kwargs)

        objs = [Driver(x.entity) for x in attrlist]

        return objs
            

    
    @property
    def name(self):
        return self.entity.name
