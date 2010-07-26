
import clusto
from clusto.schema import select, and_, ATTR_TABLE, Attribute, func, Counter
from clusto.drivers.base import Driver, ClustoMeta
from clusto.exceptions import ResourceTypeException, ResourceNotAvailableException, ResourceException



class ResourceManager(Driver):
    """The ResourceManager driver should be subclassed by a driver that will
    manage a resource such as IP allocation, MAC Address lists, etc.

    This base class just allocates unique integers.

    Resources are attributes on Entities that are managed by a ResourceManger.
    The implementation has the following properties:

    1. The Entity being assigned the resource gets an attribute who's key is
    defined by the resource manager, a number assigned by the resource manager
    (sometimes related to the resource being allocated), and a value which is
    a representation of the resource.

    2. The Entity gets an additional attribute who's key, and number match the
    allocated resource, but with subkey='manager', and value that is a
    reference to the resource manager assigning the resource.

    Any additional attributes with same attribute key and number are
    considered part of the resource and can be managed by the resource
    manager.
    """
    

    _clusto_type = "resourcemanager"
    _driver_name = "resourcemanager"

    _attr_name = "resource"
    _record_allocations = True
    


        
    def allocator(self, thing=None):
        """return an unused resource from this resource manager"""

        raise NotImplemented("No allocator implemented for %s you must explicitly specify a resource."
                             % self.name)


    def ensure_type(self, resource, number=True, thing=None):
        """checks the type of a given resourece

        if the resource is valid return it and optionally convert it to
        another format.  The format it returns has to be compatible with 
        attribute naming 
        """
        return (resource, number)


    def get_resource_number(self, thing, resource):
        """Get the number for a resource on a given entity."""
        
        resource, number = self.ensure_type(resource, thing=thing)
        
        attrs = thing.attrs(self._attr_name, value=resource)

        if attrs:
            return attrs[0].number
        else:
            raise ResourceException("%s isn't assigned resource %s"
                                    % (thing.name, str(resource)))


    def get_resource_attr_values(self, thing, resource, key, number=True):
        """Get the value for the attrs on the resource assigned to a given entity matching the given key."""
        
        return [x.value for x in self.get_resource_attrs(thing, resource,
                                                         key, number)]

    
    def get_resource_attrs(self, thing, resource, key=(), number=True):
        """Get the Attributes for the attrs on the resource assigned to a given enttiy matching the given key."""
        
        resource, number = self.ensure_type(resource, number, thing=thing)
        
        return thing.attrs(self._attr_name, number=number, subkey=key)

    
    def add_resource_attr(self, thing, resource, key, value, number=True):
        """Add an Attribute for the resource assigned to a given entity setting the given key and value"""
        
        resource, number = self.ensure_type(resource, number, thing=thing)

        attr = thing.add_attr(self._attr_name, number=number, subkey=key, value=value)
        return attr


    def set_resource_attr(self, thing, resource, key, value, number=True):
        """Set an Attribute for the resource assigned to a given entity with the given key and value"""
        
        resource, number = self.ensure_type(resource, number, thing=thing)
        attr = thing.set_attr(self._attr_name, number=number, subkey=key, value=value)

        return attr


    def del_resource_attr(self, thing, resource, key, value=(), number=True):
        """Delete an Attribute for the resource assigned to a given entity matching the given key and value"""
        
        resource, number = self.ensure_type(resource, number, thing=thing)
        thing.del_attrs(self._attr_name, number=number, subkey=key, value=value)


    def additional_attrs(self, thing, resource, number):
        pass

    
    def allocate(self, thing, resource=(), number=True, force=False):
        """allocates a resource element to the given thing.

        resource - is passed as an argument it will be checked 
                   before assignment.  

        refattr - the attribute name on the entity that will refer back
                  this resource manager.

        returns the resource that was either passed in and processed 
        or generated.
        """

        try:
            clusto.begin_transaction()
            if not isinstance(thing, Driver):
                raise TypeError("thing is not of type Driver")

            if resource is ():
                # allocate a new resource
                resource, number = self.allocator(thing)

            else:
                resource, number = self.ensure_type(resource, number, thing)
                if not force and not self.available(resource, number, thing):
                    raise ResourceException("Requested resource is not available.")

            if self._record_allocations:
                if number == True:
                    c = Counter.get(ClustoMeta().entity, self._attr_name)
                    attr = thing.add_attr(self._attr_name,
                                          resource,
                                          number=c.value
                                          )
                    c.next()
                else:
                    attr = thing.add_attr(self._attr_name, resource, number=number)
                    
                clusto.flush()

                a=thing.add_attr(self._attr_name,
                            self.entity,
                            number=attr.number,
                            subkey='manager',
                            )

                clusto.flush()
                self.additional_attrs(thing, resource, attr.number)
                
            else:
                attr = None
            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x

        return attr #resource


    def deallocate(self, thing, resource=(), number=True):
        """deallocates a resource from the given thing."""


        clusto.begin_transaction()
        try:
            if resource is ():                      
                for res in self.resources(thing):
                    thing.del_attrs(self._attr_name, number=res.number)

            elif resource and not self.available(resource, number):
                resource, number = self.ensure_type(resource, number)

                res = thing.attrs(self._attr_name, self, subkey='manager', number=number)
                for a in res: 
                    thing.del_attrs(self._attr_name, number=a.number)
                    
            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x


    def available(self, resource, number=True, thing=None):
        """return True if resource is available, False otherwise.
        """

        resource, number = self.ensure_type(resource, number)

        if self.owners(resource, number):
            return False

        return True
            

    def owners(self, resource, number=True):
        """return a list of driver objects for the owners of a given resource.
        """

        resource, number = self.ensure_type(resource, number)

        return Driver.get_by_attr(self._attr_name, resource, number=number)


    @classmethod
    def get_resource_manager(cls, resource_attr):
        """Return the resource manager for a given resource_attr"""

        thing = Driver(resource_attr.entity)
        
        return thing.attr_value(key=resource_attr.key,
                                subkey='manager',
                                number=resource_attr.number)
        

    @classmethod
    def resources(cls, thing):
        """return a list of resources from the resource manager that is
        associated with the given thing.

        A resource is a resource attribute in a resource manager.
        """
        
        attrs = [x for x in thing.attrs(cls._attr_name, subkey='manager') 
                 if isinstance(Driver(x.value), cls)]

        res = []

        for attr in attrs:
            t=thing.attrs(cls._attr_name, number=attr.number, subkey=None)
            res.extend(t)


        return res


    @property
    def count(self):
        """Return the number of resources used."""

        return len(self.references(self._attr_name, self, subkey='manager'))

