import boto3
from .utils import create_list

def get_collections(session, s3):
    return {
        "buckets": create_list(s3.list_buckets, "Buckets[]")
    }