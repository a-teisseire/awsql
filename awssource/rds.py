import boto3
from .utils import create_list, create_paginated_list

def get_collections(session, rds):
    return {
        "instances": create_paginated_list(rds, 'describe_db_instances', "DBInstances[]"),
        "subnet_groups": create_paginated_list(rds, 'describe_db_subnet_groups', "DBSubnetGroups[]")
    }