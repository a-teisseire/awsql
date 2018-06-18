import boto3
from .utils import create_list, create_paginated_list

def get_collections(session, iam):
    return {
        "roles": create_paginated_list(iam, 'list_roles', "Roles[]"),
        "users": create_paginated_list(iam, 'list_users', "Users[]"),
        "groups": create_paginated_list(iam, 'list_groups', "Groups[]"),
    }