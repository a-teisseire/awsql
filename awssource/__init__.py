from . import ec2, s3, r53, rds, iam

COLLECTIONS = {
    "ec2": ec2,
    "s3": s3,
    "route53": r53,
    "rds": rds,
    "iam": iam,
}

def get_all_collections(session, region):
    output = {}
    for c in COLLECTIONS:
        output[c] = COLLECTIONS[c].get_collections(session, session.client(c, region_name=region))

    return output
