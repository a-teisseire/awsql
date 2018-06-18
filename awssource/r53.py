import boto3
from .utils import create_list, create_paginated_list

def get_collections(session, r53):
    return {
        "hosted_zones": create_paginated_list(r53, 'list_hosted_zones', "HostedZones[]")
    }