import boto3
import click
import csv
import json
import os
import logging
import sys
from boto3.session import Session
from collections import Counter
from datetime import datetime
from typing import List


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Create an EC2 client
def get_aws_client(service: str, region: str = "us-east-1") -> Session:
    return boto3.client(service, region_name=os.environ.get("AWS_REGION", region))


def list_instances():
    ec2 = get_aws_client("ec2")
    # Describe running instances
    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    return response


def count_instances(response) -> Counter:
    # Extract instance types
    instance_types = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_types.append(instance["InstanceType"])

    # Count instances by type
    instance_count = Counter(instance_types)

    return instance_count


def get_results(instance_count: Counter):
    data = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for instance_type, count in instance_count.items():
        # print(f"{instance_type}: {count}")
        data.append(
            {
                "instance_type": f"{instance_type}",
                "count": count,
                "timestamp": timestamp,
            }
        )

    return data


def write_csv(data: List) -> str:
    if not data:
        return

    writer = csv.DictWriter(
        sys.stdout, fieldnames=["timestamp", "instance_type", "count"]
    )
    writer.writeheader()
    writer.writerows(data)


def write_sql(data: List, table_name: str = "usage") -> str:
    """
    The table structure must have the columns

    - instance_type as String/Text/Varchar
    - count as Integer

    If other columns exists they must have defaults or filled.
    """
    if not data:
        return

    tmpl = "INSERT INTO {0}(timestamp, instance_type, count) VALUES('{1}', '{2}', {3});"

    for entry in data:
        instance_type = entry.get("instance_type")
        count = entry.get("count")
        timestamp = entry.get("timestamp")
        print(tmpl.format(table_name, timestamp, instance_type, count))


@click.command()
@click.option("--output", default="json", type=click.Choice(["json", "csv", "sql"]))
def main(output):
    response = list_instances()
    counter = count_instances(response)
    data = get_results(counter)

    if output == "json":
        click.echo(json.dumps(data, indent=2))
    elif output == "csv":
        click.echo(write_csv(data))
    elif output == "sql":
        click.echo(write_sql(data))
    else:
        click.echo("Format not supported")


if __name__ == "__main__":
    main()
