class ClustoException(Exception):
    """base clusto exception"""
    pass

class DriverException(ClustoException):
    """exception for driver errors"""
    pass

class ConnectionException(ClustoException):
    """exception for operations related to connecting two Things together"""
    pass


class NameException(ClustoException):
    """exception for invalid entity or attribute names"""
    pass


class ResourceException(ClustoException):
    """exception related to resources"""
    pass

class ResourceNotAvailableException(ResourceException):
    pass

class ResourceTypeException(ResourceException):
    pass


class PoolException(ClustoException):
    pass

class TransactionException(ClustoException):
    pass
