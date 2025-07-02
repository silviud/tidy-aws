import boto3
from collections import Counter
import os

# Create an EC2 client
ec2 = boto3.client("ec2", region_name=os.environ.get("AWS_REGION", "us-east-1"))

# Describe running instances
response = ec2.describe_instances(
    Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
)

# Extract instance types
instance_types = []
for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:
        instance_types.append(instance["InstanceType"])

# Count instances by type
instance_count = Counter(instance_types)

# Print results
for instance_type, count in instance_count.items():
    print(f"{instance_type}: {count}")
