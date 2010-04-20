

import clusto
from clusto.drivers.base import Driver
from clusto.schema import VERSION

# incrementing the first number means a major schema change
# incrementing the second number means a change in a driver's storage details


class ClustoMeta(Driver):
    """
    Holds meta information about the clusto database
    """

    _properties = {'schemaversion':None}

    _clusto_type = "clustometa"
    _driver_name = "clustometa"


    def __new__(cls):

        try:
            cls.__singleton = clusto.get_by_name(cls._driver_name)
        except LookupError:
            cls.__singleton = Driver.__new__(cls, cls._driver_name)


        return cls.__singleton


    def __init__(self): #, name=None, entity=None, *args, **kwargs):

        if not hasattr(self, 'entity'):
            super(ClustoMeta, self).__init__(self._driver_name)
            self.schemaversion = VERSION




        
