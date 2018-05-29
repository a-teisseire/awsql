import boto3
from .utils import create_list

def get_collections(client_cfg):
    ec2 = boto3.client("ec2", **client_cfg)
    return {
        "instances": create_list(ec2.describe_instances, "Reservations[].Instances[]"),
        "vpcs": create_list(ec2.describe_vpcs, "Vpcs[]"),
        "vpns": create_list(ec2.describe_vpn_connections, "VpnConnections[]"),
        "vpn_gateways": create_list(ec2.describe_vpn_gateways, "VpnGateways[]"),
        "customer_gateways": create_list(ec2.describe_customer_gateways, "CustomerGateways[]"),
        "images": create_list(ec2.describe_images, "Images[]"),
        "volumes": create_list(ec2.describe_volumes, "Volumes[]"),
        "subnets": create_list(ec2.describe_subnets, "Subnets[]"),
        "vpc_endpoints": create_list(ec2.describe_vpc_endpoints, "VpcEndpoints[]")
    }