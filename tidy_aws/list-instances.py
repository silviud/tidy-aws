#!/usr/bin/env python

import argparse
import os

import boto3

AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')


def list_running_instances():
    # Create an EC2 resource
    ec2 = boto3.resource('ec2', region_name=AWS_REGION)

    filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
    instances = ec2.instances.filter(Filters=filters)

    return instances


def print_instances(instances: list, f_type: str = 'table'):

    if f_type == 'default':
        for instance in instances:
            print(f'Instance ID: {instance.id}, State: {instance.state["Name"]}, Type: {instance.instance_type}, Launch Time: {instance.launch_time}')
    elif f_type == 'csv':
        if instances:
            print('InstanceID, State, Type, LaunchTime')
            for instance in instances:
                print(f'{instance.id}, {instance.state["Name"]}, {instance.instance_type}, {instance.launch_time}')
    else:
        print(f'Unsupported format {f_type}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', action='store', default='default', choices=('csv', 'default'))

    args = parser.parse_args()

    format_type = args.format

    instances = list_running_instances()
    print_instances(instances, format_type)


if __name__ == "__main__":
    main()
