#!/usr/bin/env python

import os

import boto3

AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')


def list_running_instances():
    # Create an EC2 resource
    ec2 = boto3.resource('ec2', region_name=AWS_REGION)

    # Filter to get only running instances
    filters = [{'Name': 'instance-state-name', 'Values': ['running']}]

    # Retrieve instances
    instances = ec2.instances.filter(Filters=filters)

    # Print instance details
    for instance in instances:
        print(f'Instance ID: {instance.id}, State: {instance.state["Name"]}, Type: {instance.instance_type}, Launch Time: {instance.launch_time}')

if __name__ == "__main__":
    list_running_instances()
