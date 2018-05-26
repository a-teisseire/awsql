import awsql

instances = [
    {
        "InstanceId": 1234,
        "Tags": [
            {
                "Key": "Name",
                "Value": "VM Palo Alto A"
            }
        ],
        "SubnetId": 1,
        "VpcId": 123
    },
    {
        "InstanceId": 1235,
        "Tags": [
            {
                "Key": "Name",
                "Value": "VM Palo Alto B"
            }
        ],
        "SubnetId": 2,
        "VpcId": 123
    },
    {
        "InstanceId": 1236,
        "Tags": [
            {
                "Key": "Name",
                "Value": "VM CSR Router A"
            }
        ],
        "SubnetId": 1,
        "VpcId": 123
    },
    {
        "InstanceId": 1237,
        "Tags": [
            {
                "Key": "Name",
                "Value": "VM CSR Router B"
            }
        ],
        "SubnetId": 2,
        "VpcId": 123
    },
    {
        "InstanceId": 1238,
        "Tags": [
            {
                "Key": "Name",
                "Value": "Test VM"
            }
        ],
        "SubnetId": 3,
        "VpcId": 124
    }
]

subnets = [
    {
        "SubnetId": 1,
        "Tags": [
            {
                "Key": "Name",
                "Value": "subnet-transit-public-a"
            }
        ]
    },
    {
        "SubnetId": 2,
        "Tags": [
            {
                "Key": "Name",
                "Value": "subnet-transit-public-b"
            }
        ]
    },
    {
        "SubnetId": 3,
        "Tags": [
            {
                "Key": "Name",
                "Value": "subnet-test-a"
            }
        ]
    }
]


test_query = """
from i in instances
where i.VpcId != 123
join sub in subnets on i.SubnetId equals sub.SubnetId
path "[*].{id: i.InstanceId, name: i.Tags[?Key=='Name'].Value | [0], subnet_id: sub.SubnetId, subnet_name: sub.Tags[?Key=='Name'].Value | [0]}"
"""

i = awsql.Interpreter(test_query)
i.add_local("instances", instances)
i.add_local("subnets", subnets)
print(i.run())
