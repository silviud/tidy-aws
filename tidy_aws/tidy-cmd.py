import boto3
import os
import logging
from boto3.session import Session
from pprint import pprint
from typing import Dict, List


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_aws_client(service: str, region: str = 'us-east-1') -> Session:

    return boto3.client('ec2', region_name=os.environ.get('AWS_REGION', region))


def list_unattached_ebs_volumes() -> List[Dict]:
    """ Filter volumes that are not attached """

    ec2_client = get_aws_client('ec2')

    volumes = ec2_client.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
    unattached_volumes = []
    for volume in volumes['Volumes']:
        volume_info = {
            'VolumeId': volume['VolumeId'],
            'Size': volume['Size'],
            'Name': 'N/A',
            'Description': 'N/A'
        }
        if 'Tags' in volume:
            for tag in volume['Tags']:
                if tag['Key'] == 'Name':
                    volume_info['Name'] = tag['Value']
                if tag['Key'] == 'Description':
                    volume_info['Description'] = tag['Value']
        unattached_volumes.append(volume_info)
    return unattached_volumes

def main():
    volumes = list_unattached_ebs_volumes()

    if len(volumes):
        pprint(volumes)
    else:
        logger.info('No unattached volumes.')



if __name__ == "__main__":
    main()
