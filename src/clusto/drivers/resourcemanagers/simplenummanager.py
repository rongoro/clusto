import clusto
from clusto.drivers.base import ResourceManager

from clusto.exceptions import ResourceException
from clusto.schema import ATTR_TABLE

class SimpleNumManagerException(ResourceException):
    pass

class SimpleNumManager(ResourceManager):
    """Manage the generation of numbers that can be associated with Entities
    
    """

    _driver_name = "simplenummanager"
    _properties = {'maxnum':None,
                   'next':0,
                   }

    _record_allocations = True
    _attr_name = "simplenum"
    
    def allocator(self, thing=None):

        clusto.flush()

        counter = clusto.Counter.get(self.entity, 'next', default=self.next)

        num = counter.value
        
        if self.maxnum and num > self.maxnum:
            raise SimpleNumManagerException("Out of numbers. "
                                            "Max of %d reached." 
                                            % (self.maxnum))
        
        counter.next()
        return (num, True)

