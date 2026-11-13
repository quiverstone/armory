#!/usr/bin/env bash
# Delete the default VPC (internet gateways, subnets, VPC) in every enabled region of the current account.
# Lists the default VPCs first and asks for confirmation before deleting anything.
#
# Requires: aws CLI, jq. Environment: AWS_PROFILE (optional).
set -euo pipefail

mapfile -t REGIONS < <(aws ec2 describe-regions --query 'Regions[].RegionName' --output text | tr '\t' '\n')

default_vpcs() {
  aws --region "$1" ec2 describe-vpcs --filters Name=is-default,Values=true --query 'Vpcs[].VpcId' --output text
}

for region in "${REGIONS[@]}"; do
  echo "${region}: $(default_vpcs "${region}")"
done

read -r -p "Delete the default VPCs listed above? [y/N] " -n 1 REPLY
echo
[[ "${REPLY}" =~ ^[Yy]$ ]] || exit 0

for region in "${REGIONS[@]}"; do
  for vpc_id in $(default_vpcs "${region}"); do
    for igw in $(aws --region "${region}" ec2 describe-internet-gateways \
      --filters "Name=attachment.vpc-id,Values=${vpc_id}" --query 'InternetGateways[].InternetGatewayId' --output text); do
      echo "Deleting internet gateway ${region} ${vpc_id} ${igw}"
      aws --region "${region}" ec2 detach-internet-gateway --internet-gateway-id "${igw}" --vpc-id "${vpc_id}"
      aws --region "${region}" ec2 delete-internet-gateway --internet-gateway-id "${igw}"
    done

    for subnet in $(aws --region "${region}" ec2 describe-subnets \
      --filters "Name=vpc-id,Values=${vpc_id}" --query 'Subnets[].SubnetId' --output text); do
      echo "Deleting subnet ${region} ${vpc_id} ${subnet}"
      aws --region "${region}" ec2 delete-subnet --subnet-id "${subnet}"
    done

    echo "Deleting VPC ${region} ${vpc_id}"
    aws --region "${region}" ec2 delete-vpc --vpc-id "${vpc_id}"
  done
done
