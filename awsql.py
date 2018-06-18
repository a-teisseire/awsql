import boto3
import parser
import awssource
import json
import argparse
import sys
import collections
from multiprocessing.pool import ThreadPool
from botocore.exceptions import ClientError

def get_all_regions():
    return [
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
        "ca-central-1",
        "eu-west-1",
        "eu-central-1",
        "eu-west-2",
        "eu-west-3",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-south-1",
        "sa-east-1",
    ]

def get_sessions_for_roles(roles):
    client = boto3.client('sts')

    for ro in roles:
        try:
            response = client.assume_role(
                RoleArn=ro,
                RoleSessionName="AWSQL"
            )
        except ClientError as e:
            sys.stderr.write("Cannot assume role: {0}\n".format(ro))
            sys.stderr.write("-> Reason: {0}\n".format(str(e)))
            continue
        except Exception as e:
            sys.stderr.write("Error: {0}\n".format(str(e)))

        credentials = response["Credentials"]
        yield (boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']), ro.split(':')[4])

    raise StopIteration()

class InterpreterRunParameters(object):
    def __init__(self, interpreter, session, regions, account_id, with_identity, with_alias):
        self.interpreter = interpreter
        self.session = session
        self.regions = regions
        self.account_id = account_id
        self.with_alias = with_alias
        self.with_identity = with_identity

def run_with_params(rp: InterpreterRunParameters):
    results = []
    acc = {}
    meta = {}

    # Get the AWS Account Alias
    if rp.with_alias:
        try:
            aliases = rp.session.client("iam").list_account_aliases()
            if len(aliases["AccountAliases"]) > 0:
                meta["alias"] = aliases["AccountAliases"][0]
        except Exception:
            pass

    # Get the identity
    if rp.account_id is None or rp.with_identity:
        try:
            identity = rp.session.client("sts").get_caller_identity()
            rp.account_id = identity["Account"]

            if rp.with_identity:
                meta["identity"] = identity["Arn"]
        except Exception:
            pass
            
    # Loop through all the regions and execute the query
    for rg in rp.regions:
        local_vars = awssource.get_all_collections(rp.session, rg)
        local_vars["account"] = {
            "id": rp.account_id,
            "region": rg
        }
        context = parser.Context(local_vars)

        try:
            result = {"result": rp.interpreter.run(context)}
        except Exception as e:
            result = {"error": str(e)}

        results.append({"region": rg, **result})

    acc = {"account": rp.account_id, "regions": results}

    if meta:
        acc["meta"] = meta

    return acc

class AWSQLInterpreter():
    def __init__(self, with_identity=False, with_alias=False):
        self.with_identity = with_identity
        self.with_alias = with_alias
        pass

    def load(self, content):
        p = parser.Parser(content)
        steps = p.parse()
        self.interpreter = parser.BaseInterpreter(steps)

    def new_run_params(self, session, regions, account_id=None):
        return InterpreterRunParameters(self.interpreter, session, regions, account_id, self.with_identity, self.with_alias)

    def create_worker_pool(self, tasks, workers):
        num_tasks = len(tasks)
        threads = []
        for x in range(workers):
            threads.append([])

        i = 0
        while num_tasks > 0:
            for x in range(min(workers, num_tasks)):
                threads[x].append(tasks[i])

            num_tasks -= workers
            i += 1

    def run(self, regions, roles=None, workers=False):
        if roles is None:
            sess = boto3.Session()
            tasks = [self.new_run_params(boto3.Session(), regions)]
        else:
            tasks = [self.new_run_params(x[0], regions, x[1]) for x in get_sessions_for_roles(roles)]

        if not workers:
            workers = 1

        pool = ThreadPool(workers)
        output = pool.map(run_with_params, tasks)

        return output

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", action="store")
    p.add_argument("--regions", dest="regions", action="store")
    p.add_argument("--roles", dest="roles", action="store")
    p.add_argument("--with-alias", dest="with_alias", action="store_true")
    p.add_argument("--with-identity", dest="with_identity", action="store_true")
    p.add_argument("-w", "--workers", dest="workers", type=int, action="store", default=False)

    args = p.parse_args()

    with open(args.input) as fp:
        cfg = fp.read()

    if args.regions is None:
        regions = [boto3.Session().region_name]
    elif args.regions == "all":
        regions = get_all_regions()
    else:
        regions = [x.strip() for x in args.regions.split(",")]

    roles = None
    if args.roles:
        with open(args.roles) as fp:
            roles = [x.strip() for x in fp.readlines()]

    interpreter = AWSQLInterpreter(with_alias=args.with_alias, with_identity=args.with_identity)
    interpreter.load(cfg)

    results = list(interpreter.run(regions, roles=roles, workers=args.workers))
    print(json.dumps(results, indent=2))   

if __name__ == "__main__":
    main()