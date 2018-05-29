import boto3
import parser
import awssource
import json
import argparse

p = argparse.ArgumentParser()
p.add_argument("input", action="store")

args = p.parse_args()

with open(args.input) as fp:
    i = parser.Interpreter(fp.read())

client_cfg = {
    "region_name": "eu-west-1"
}
i.add_local("ec2", awssource.ec2.get_collections(client_cfg))
r = i.run()
print(json.dumps(r, indent=2))