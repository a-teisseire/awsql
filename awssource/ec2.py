import boto3
from .utils import create_list, create_paginated_list

def get_collections(session, ec2):
    return {
        "instances": create_paginated_list(ec2, 'describe_instances', "Reservations[].Instances[]"),
        "vpcs": create_list(ec2.describe_vpcs, "Vpcs[]"),
        "vpns": create_list(ec2.describe_vpn_connections, "VpnConnections[]"),
        "vpn_gateways": create_list(ec2.describe_vpn_gateways, "VpnGateways[]"),
        "customer_gateways": create_list(ec2.describe_customer_gateways, "CustomerGateways[]"),
        "internet_gateways": create_list(ec2.describe_internet_gateways, "InternetGateways[]"),
        "images": create_list(ec2.describe_images, "Images[]"),
        "volumes": create_paginated_list(ec2, 'describe_volumes', "Volumes[]"),
        "subnets": create_list(ec2.describe_subnets, "Subnets[]"),
        "vpc_endpoints": create_list(ec2.describe_vpc_endpoints, "VpcEndpoints[]")
    }