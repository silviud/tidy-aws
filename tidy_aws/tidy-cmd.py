import boto3
import os
import logging
from boto3.session import Session
from datetime import datetime, timedelta, timezone
from pprint import pprint
from typing import Dict, List


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_aws_client(service: str, region: str = "us-east-1") -> Session:
    return boto3.client("ec2", region_name=os.environ.get("AWS_REGION", region))


# ec2 helpers
def get_active_amis(ec2_client: Session = None):
    """
    Retrieve all AMIs currently used by running EC2 instances.
    """

    ec2_client = ec2_client or get_aws_client("ec2")

    active_amis = set()
    paginator = ec2_client.get_paginator("describe_instances")
    try:
        for page in paginator.paginate(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        ):
            for reservation in page["Reservations"]:
                for instance in reservation["Instances"]:
                    ami_id = instance["ImageId"]
                    active_amis.add(ami_id)
                    logger.info(f"Found active AMI: {ami_id}")
    except Exception as e:
        logger.error("Error retrieving active AMIs: {}".format(e))
        raise
    return active_amis


# ec2
def list_unattached_ebs_volumes(ec2_client: Session = None) -> List[Dict]:
    """Filter volumes that are not attached"""

    ec2_client = ec2_client or get_aws_client("ec2")

    volumes = ec2_client.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )
    unattached_volumes = []
    for volume in volumes["Volumes"]:
        volume_info = {
            "VolumeId": volume["VolumeId"],
            "Size": volume["Size"],
            "Name": "N/A",
            "Description": "N/A",
        }
        if "Tags" in volume:
            for tag in volume["Tags"]:
                if tag["Key"] == "Name":
                    volume_info["Name"] = tag["Value"]
                if tag["Key"] == "Description":
                    volume_info["Description"] = tag["Value"]
        unattached_volumes.append(volume_info)
    return unattached_volumes


def list_unused_elastic_ips(ec2_client: Session = None) -> List[Dict]:
    ec2_client = ec2_client or get_aws_client("ec2")

    addresses = ec2_client.describe_addresses()["Addresses"]
    return [
        {"PublicIp": address["PublicIp"]}
        for address in addresses
        if "InstanceId" not in address
        and "NetworkInterfaceId" not in address
        and "AssociationId" not in address
    ]


def list_old_ebs_snapshots(ec2_client: Session = None) -> List[Dict]:
    """
    List EBS snapshots older than 30 days, excluding those linked to AMIs currently in use.
    """

    ec2_client = ec2_client or get_aws_client("ec2")

    snapshots = ec2_client.describe_snapshots(OwnerIds=["self"])["Snapshots"]
    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    active_amis = get_active_amis(
        ec2_client
    )  # Retrieve active AMIs in use by EC2 instances

    # Retrieve snapshots used by active AMIs from block device mappings
    active_snapshot_ids = set()
    for ami_id in active_amis:
        ami_details = ec2_client.describe_images(ImageIds=[ami_id])
        if ami_details["Images"]:  # Check if list is not empty
            ami_image = ami_details["Images"][0]
            for block_device in ami_image.get("BlockDeviceMappings", []):
                if "Ebs" in block_device and "SnapshotId" in block_device["Ebs"]:
                    active_snapshot_ids.add(block_device["Ebs"]["SnapshotId"])

    snapshot_details = []
    for snap in snapshots:
        if (
            snap["StartTime"] < one_month_ago
            and snap["SnapshotId"] not in active_snapshot_ids
        ):
            # Only list snapshots that are not in active_snapshot_ids
            name = next(
                (tag["Value"] for tag in snap.get("Tags", []) if tag["Key"] == "Name"),
                "N/A",
            )

            snapshot_details.append(
                {
                    "SnapshotId": snap["SnapshotId"],
                    "Name": name,
                    "StartTime": snap["StartTime"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),  # formatting date
                    "AmiId": "N/A",  # Not directly relevant here
                }
            )

    return snapshot_details


def list_old_amis(ec2_client: Session = None) -> List[Dict]:
    """
    List AMIs that are older than 30 days and not in use by any EC2 instances.
    """

    ec2_client = ec2_client or get_aws_client("ec2")

    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    old_images = []
    active_amis = get_active_amis(
        ec2_client
    )  # Retrieve active AMIs in use by EC2 instances

    logger.info(f"Active AMIs: {active_amis}")

    images = ec2_client.describe_images(Owners=["self"])["Images"]
    for image in images:
        creation_date = datetime.strptime(
            image["CreationDate"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).replace(tzinfo=timezone.utc)
        if creation_date < one_month_ago and image["ImageId"] not in active_amis:
            name = next(
                (tag["Value"] for tag in image.get("Tags", []) if tag["Key"] == "Name"),
                "N/A",
            )
            old_images.append(
                {
                    "ImageId": image["ImageId"],
                    "Name": name,
                    "CreationDate": image["CreationDate"],
                }
            )
            logger.info(f"Listing old, unused AMI: {image['ImageId']}")
        else:
            logger.info(f"Skipping AMI in use: {image['ImageId']}")

    return old_images


# elb
def list_unassociated_elbs(elb_client: Session = None) -> List[Dict]:
    elb_client = elb_client or get_aws_client("elb")

    elbs = elb_client.describe_load_balancers()["LoadBalancerDescriptions"]
    return [
        {"LoadBalancerName": elb["LoadBalancerName"]}
        for elb in elbs
        if not elb["Instances"]
    ]


# elbv2
def list_unused_elbv2(elbv2_client: Session = None) -> List[Dict]:
    elbv2_client = elbv2_client or get_aws_client("elbv2")

    load_balancers = elbv2_client.describe_load_balancers()["LoadBalancers"]
    unused_load_balancers = []

    for lb in load_balancers:
        target_groups = elbv2_client.describe_target_groups(
            LoadBalancerArn=lb["LoadBalancerArn"]
        )["TargetGroups"]
        targets_exist = any(
            elbv2_client.describe_target_health(TargetGroupArn=tg["TargetGroupArn"])[
                "TargetHealthDescriptions"
            ]
            for tg in target_groups
        )

        if not targets_exist:
            lb_info = {
                "LoadBalancerName": lb["LoadBalancerName"],
                "Name": "N/A",
                "Description": "N/A",
            }
            # Fetch tags for the load balancer
            tags_response = elbv2_client.describe_tags(
                ResourceArns=[lb["LoadBalancerArn"]]
            )
            for tag_description in tags_response["TagDescriptions"]:
                for tag in tag_description["Tags"]:
                    if tag["Key"] == "Name":
                        lb_info["Name"] = tag["Value"]
                    if tag["Key"] == "Description":
                        lb_info["Description"] = tag["Value"]
            unused_load_balancers.append(lb_info)

    return unused_load_balancers


def main():
    volumes = list_unattached_ebs_volumes()
    if volumes:
        pprint(volumes)
    else:
        logger.info("No unattached volumes.")
    #
    # snapshots = list_old_ebs_snapshots()
    # if snapshots:
    #     pprint(snapshots)
    # else:
    #     logger.info("No old snaphots.")
    # old_amis = list_old_amis()
    # if old_amis:
    #     pprint(old_amis)
    # else:
    #     logger.info("No old ami.")


if __name__ == "__main__":
    main()
