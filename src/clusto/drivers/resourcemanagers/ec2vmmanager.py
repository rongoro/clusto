from clusto.drivers.base import ResourceManager
from clusto.exceptions import ResourceException


import boto
from mako.template import Template

class EC2VMManagerException(ResourceException):
    pass

class EC2VMManager(ResourceManager):

    _driver_name = "ec2vmmanager"
    _attr_name = "ec2vmmanager"

    _properties = {'budget':None, # hourly budget
                   'aws_access_key_id':None,
                   'aws_secret_access_key':None}


    _type_costs = {'eu-west-1':{'unix':{'m1.small':0.095,
                                        'm1.large':0.38,
                                        'm1.xlarge':0.76,
                                        'm2.xlarge':0.57,
                                        'm2.2xlarge':1.34,
                                        'm2.4xlarge':2.68,
                                        'c1.medium':0.19,
                                        'c1.xlarge':0.76}
                                },
                                        
                   'us-east-1':{'unix':{'m1.small':0.085,
                                        'm1.large':0.34,
                                        'm1.xlarge':0.68,
                                        'm2.xlarge':0.50,
                                        'm2.2xlarge':1.20,
                                        'm2.4xlarge':2.40,
                                        'c1.medium':0.17,
                                        'c1.xlarge':0.68,
                                        'cc1.4xlarge':1.60}
                                },
                   'us-west-1':{'unix':{'m1.small':0.095,
                                        'm1.large':0.38,
                                        'm1.xlarge':0.76,
                                        'm2.xlarge':0.57,
                                        'm2.2xlarge':1.34,
                                        'm2.4xlarge':2.68,
                                        'c1.medium':0.19,
                                        'c1.xlarge':0.76}
                                },
                   'ap-southeast-1':{'unix':{'m1.small':0.095,
                                        'm1.large':0.38,
                                        'm1.xlarge':0.76,
                                        'm2.xlarge':0.57,
                                        'm2.2xlarge':1.34,
                                        'm2.4xlarge':2.68,
                                        'c1.medium':0.19,
                                        'c1.xlarge':0.76}
                                },
                   }

    def _ec2_connection(self, region=None):
        c = boto.connect_ec2(aws_access_key_id=str(self.aws_access_key_id),
                             aws_secret_access_key=str(self.aws_secret_access_key))

        if not region or region == 'us-east-1':
            return c
        else:
            return boto.ec2.connect_to_region(region,
                                              aws_access_key_id=str(self.aws_access_key_id),
                                              aws_secret_access_key=str(self.aws_secret_access_key))
            

    def _instance_to_dict(self, instance):

        placement = instance.placement
            
        d= {'placement':placement,
            'instance_id':instance.id}

        return d

    def _get_instance_from_resource(self, resource):

        conn = self._ec2_connection(resource['placement'][:-1])

        il = conn.get_all_instances(instance_ids=[resource['instance_id']])
        
        return il[0].instances[0]

    def _stop_instance(self, resource):

        conn = self._ec2_connection(resource['placement'][:-1])

        reservations = conn.get_all_instances([resource['instance_id']])

        for reservation in reservations:
            for instance in reservation.instances:
                if instance.id == resource['instance_id']:
                    instance.stop()
                    return
                

    def get_all_ec2_instance_resources(self):
        """Query AWS and return all active ec2 instances and their state"""
        
        instance_resources = []

        regions = [r.name for r in self._ec2_connection().get_all_regions()]
        
        for region in regions:

            conn = self._ec2_connection(region)

            for reservation in conn.get_all_instances():
                for instance in reservation.instances:
                    instance_resources.append({'resource':self._instance_to_dict(instance),
                                               'state': instance.state
                                               })

        return instance_resources
                    
        
    def additional_attrs(self, thing, resource, number):

        for name,val in resource.items():
            self.set_resource_attr(thing,
                                   resource,
                                   number=number,
                                   key=str(name),
                                   value=str(val))

    def _build_user_data(self, thing):

        udata = thing.attr_value(key='aws', subkey='ec2_user_data',
                                 merge_container_attrs=True)

        if udata:
            template = Template(udata)
            return template.render(clusto={'name':thing.name})
        else:
            return None

    def allocator(self, thing):
        """Allocate VMs on ec2 while keeping track of current costs and staying within the budget

        """

        for res in self.resources(thing):
            raise ResourceException("%s is already assigned to %s"
                                    % (thing.name, res.value))


        region = thing.attr_value(key='aws', subkey='ec2_region',
                                  merge_container_attrs=True) or 'us-east-1'

        instance_type = thing.attr_value(key='aws', subkey='ec2_instance_type',
                                         merge_container_attrs=True)

        if not instance_type:
            raise ResourceException("No instance type specified for %s"
                                    % thing.name)
        
        image_id = thing.attr_value(key='aws', subkey='ec2_ami',
                                    merge_container_attrs=True)

        if not image_id:
            raise ResourceException("No AMI specified for %s" % thing.name)
        
        placement = thing.attr_value(key='aws', subkey='ec2_placement',
                                     merge_container_attrs=True)

        user_data = self._build_user_data(thing)
        
        key_name = thing.attr_value(key='aws', subkey='ec2_key_name',
                                    merge_container_attrs=True)


        security_groups = thing.attr_values(key='aws', subkey='ec2_security_group',
                                            merge_container_attrs=True)
        
        res = self.resources(thing)
        if len(res) > 1:
            raise ResourceException("%s is somehow already assigned more than one instance")
        elif len(res) == 1:
            raise ResourceException("%s is already running as %s"
                                    % res[0].value)
        else:
            
            c = self._ec2_connection(region)
            image = c.get_image(image_id)

            reservation = image.run(instance_type=instance_type,
                                    placement=placement,
                                    key_name=key_name,
                                    user_data=user_data,
                                    security_groups=security_groups)

            i = reservation.instances[0]
        
        return (self._instance_to_dict(i), True)


    def deallocate(self, thing, resource=(), number=True):
        """deallocates a resource from the given thing."""

        if thing.attr_value(key='aws', subkey='ec2_allow_termination',
                            merge_container_attrs=True) == False:
            raise EC2VMManagerException("Not Allowed to terminate %s." % thing.name)
        
        if not resource:
            for resource in self.resources(thing):
                self._stop_instance(resource.value)
                thing.clear_metadata()
                super(EC2VMManager, self).deallocate(thing, resource.value,
                                                     number)
        else:
            super(EC2VMManager, self).deallocate(thing, resource.value, number)
