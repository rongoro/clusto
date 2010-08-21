import clusto

def make_all_ec2_objects(aws_access_key_id=None, aws_secret_access_key=None):
    ec2man = clusto.get_entities(clusto_types=[clusto.drivers.EC2VMManager])

    if not ec2man:
        if not aws_access_key_id and not aws_secret_access_key:
            raise Exception("you must specify both an aws_access_key_id and an "
                            "aws_secret_access_key if you don't already have "
                            "an EC2VMManager")
        
        ec2man = clusto.drivers.EC2VMManger('ec2vmman',
                                            aws_access_key_id=aws_access_key_id,
                                            aws_secret_access_key=aws_secret_access_key)

    else:
        ec2man = ec2man.pop()

    conn = ec2man._ec2_connection()

    for region in conn.get_all_regions():
        curconn = ec2man._ec2_connection(region.name)
        region_entity = clusto.get_or_create(region.name,
                                             clusto.drivers.EC2Region,
                                             region=region.name)
        for zone in curconn.get_all_zones():
            zone_entity = clusto.get_or_create(zone.name,
                                               clusto.drivers.EC2Zone,
                                               placement=zone.name)

            if zone_entity not in region_entity:
                region_entity.insert(zone_entity)
                
