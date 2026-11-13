import boto3


def get_all_regions():
    """
    Get a list of all regions.
    :return: List of regions.
    """
    ec2_client = boto3.client("ec2")
    regions = [region["RegionName"] for region in ec2_client.describe_regions()["Regions"]]
    return regions


def remove_config_recorders(client):
    """
    Stop and remove AWS Config configuration recorders.
    :param client: boto3 AWS Config client.
    """
    recorders = client.describe_configuration_recorders()
    for recorder in recorders.get("ConfigurationRecorders", []):
        recorder_name = recorder["name"]

        # Stop the configuration recorder
        status = client.describe_configuration_recorder_status(ConfigurationRecorderNames=[recorder_name])
        if status["ConfigurationRecordersStatus"][0]["recording"]:
            print(f"Stopping configuration recorder: {recorder_name}")
            client.stop_configuration_recorder(ConfigurationRecorderName=recorder_name)

        # Delete the configuration recorder
        print(f"Deleting configuration recorder: {recorder_name}")
        client.delete_configuration_recorder(ConfigurationRecorderName=recorder_name)


def remove_delivery_channels(client):
    """
    Remove AWS Config delivery channels.
    :param client: boto3 AWS Config client.
    """
    channels = client.describe_delivery_channels()
    for channel in channels.get("DeliveryChannels", []):
        channel_name = channel["name"]
        print(f"Deleting delivery channel: {channel_name}")
        client.delete_delivery_channel(DeliveryChannelName=channel_name)


def main():
    """
    Main function to delete AWS Config resources in the current account across all regions.
    """
    session = boto3.Session()

    for region in get_all_regions():
        print(f"Processing region: {region}")

        config_client = session.client("config", region_name=region)
        try:
            remove_config_recorders(config_client)
            remove_delivery_channels(config_client)
            print(f"Successfully deleted AWS Config configuration recorders and delivery channels in {region}.")
        except Exception as e:
            print(f"An error occurred in {region}: {e}")


if __name__ == "__main__":
    print("Deleting AWS Config resources in current account across all regions...")
    main()
