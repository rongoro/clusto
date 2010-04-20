
TYPELIST = {}
DRIVERLIST = {}
RESERVEDATTRS = {}

class ClustoDriver(type):
    """
    Metaclass for all clusto drivers
    """
    def __init__(cls, name, bases, dct):

        if not hasattr(cls, '_driver_name'):
            raise DriverException("Driver %s missing _driver_name attribute"
                                  % cls.__name__)

        if cls._driver_name in DRIVERLIST:
            raise KeyError("class '%s' is trying to add the driver_name '%s' "
                           "to the driver list but that name is already "
                           "claimed by the '%s' class."
                           % (cls.__name__,
                              cls._driver_name,
                              DRIVERLIST[cls._driver_name].__name__))
        

        DRIVERLIST[cls._driver_name] = cls
        TYPELIST[cls._clusto_type] = cls

        # setup properties
        if not isinstance(cls._properties, dict):
            raise TypeError('_properties of %s is not a dict type.',
                            cls.__name__)
        

        super(ClustoDriver, cls).__init__(name, bases, dct)

