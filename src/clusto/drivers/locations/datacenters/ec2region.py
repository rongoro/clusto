from clusto.drivers.locations.datacenters.basicdatacenter import BasicDatacenter

class EC2Region(BasicDatacenter):
    """
    EC2 region driver
    """

    _driver_name = "ec2region"

    def __init__(self, name_driver_entity, **kwargs):
        super(EC2Region, self).__init__(name_driver_entity, **kwargs)

        self.set_attr(key='aws', subkey='ec2_region', value=kwargs['region'])

        
