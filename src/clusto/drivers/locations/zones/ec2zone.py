from clusto.drivers.locations.zones import BasicZone

class EC2Zone(BasicZone):
    """
    EC2 zone driver.
    """

    _driver_name = "ec2zone"

    def __init__(self, name_driver_entity, **kwargs):
        super(EC2Zone, self).__init__(name_driver_entity, **kwargs)

        self.set_attr(key='aws', subkey='ec2_placement', value=kwargs['placement'])
    
