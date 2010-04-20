import clusto
from clusto.drivers.base import ResourceManager

from clusto.exceptions import ResourceException
from clusto.schema import ATTR_TABLE

class SimpleNameManagerException(ResourceException):
    pass

class SimpleNameManager(ResourceManager):
    """
    SimpleNameManager - manage the generation of a names with a common
    prefix and an incrementing integer component.

    e.g foo001, foo002, foo003, etc.
    
    """

    _driver_name = "simplenamemanager"
    _properties = {'basename':'',
                   'digits':2,
                   'next':1,
                   'leadingZeros':int(True)}

    _record_allocations = True
    _attr_name = 'simplename'
    
    def allocator(self):
        clusto.flush()

        counter = clusto.Counter.get(self.entity, 'next', default=self.next)

        num = str(counter.value)

        if self.leadingZeros:
            num = num.rjust(self.digits, '0')

        if len(num) > self.digits:
            raise SimpleNameManagerException("Out of digits for the integer. "
                                             "Max of %d digits and we're at "
                                             "number %s." % (self.digits, num))
        
        nextname = self.basename + num

        counter.next()

        return (nextname, True)
        

class SimpleEntityNameManager(SimpleNameManager):    

    _driver_name = "simpleentitynamemanager"

    _record_allocations = False


    def allocate(self, clustotype, resource=None, number=True):
        """allocates a resource element to the given thing.

        resource - is passed as an argument it will be checked 
                   before assignment.  

        refattr - the attribute name on the entity that will refer back
                  this resource manager.

        returns the resource that was either passed in and processed 
        or generated.
        """

        if not isinstance(clustotype, type):
            raise TypeError("thing is not a Driver class")

        try:
            clusto.begin_transaction()

            if not resource:
                name, num = self.allocator()

                newobj = clustotype(name)

            else:
                name = resource
                newobj = clustotype(resource)


            super(SimpleEntityNameManager, self).allocate(newobj, name)

            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x
        
        return newobj


    def deallocate(self, thing, resource=None, number=True):
        raise Exception("can't deallocate an entity name, delete the entity instead.")

