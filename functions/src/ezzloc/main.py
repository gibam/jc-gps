#!/usr/bin/env python3
"""
Ezzloc Data Pipeline
Main orchestrator for fetching GPS device data from Ezzloc, processing, and loading to BigQuery.
"""

from datetime import datetime
import sys
# import pytz
from zoneinfo import ZoneInfo
import pandas as pd
from src.ezzloc.config import USERNAME, PREFIX
from src.ezzloc.auth import EzzlocAuth
from src.ezzloc.client import EzzlocClient
from src.ezzloc.processor import DataProcessor
# from src.bigquery.loader import BigQueryLoader

zoneinfo = ZoneInfo('America/Santiago')

def generate_local_file(process_start_time: datetime) -> str:
    """
    Generate local CSV file from Ezzloc data.
    
    Returns:
        str: Path to the generated CSV file.
    """
    # process_start_time = datetime.now(zoneinfo)

    try:
        filter_size = None
        print("Starting Ezzloc data pipeline...")

        # Authentication
        print("Authenticating...")
        auth = EzzlocAuth()
        token = auth.login()
        print("Authentication successful")

        api_client = EzzlocClient(username=USERNAME, token=token)
        processor = DataProcessor()

        # Fetch groups data
        print()
        print("Fetching org_groups data...")
        org_groups_data = api_client.get_org_groups()
        # print(f"   groups_data: {groups_data}")
        print("Processing org_groups data...")
        org_groups_df = processor.process_data_to_df(org_groups_data)
        print(f"Fetched {len(org_groups_data)} org_groups")
        # print(f"    org_groups_df.shape: {org_groups_df.shape}")
        # print(f"    org_groups_df.columns: {org_groups_df.columns}")
        # print(f"    org_groups_df.head(): {org_groups_df.head()}")
        
        # filter_size = 5
        groups_ids = list(set(org_groups_df["org_group_id"].tolist()))
        groups_ids = groups_ids[:filter_size] if filter_size and len(groups_ids) > filter_size else groups_ids
        
        print()
        print("Fetching groups details...")
        print(f"Getting details for {len(groups_ids)} groups...")  # Debug print
        groups_data = api_client.get_group_details_bulk(groups_ids)
        
        print("Processing groups data...")
        groups_df = processor.process_data_to_df(groups_data)
        print(f"Fetched {len(groups_data)} groups")

        # filter_size = 5
        devices_ids = list(set(groups_df["device_id"].tolist()))
        devices_ids = devices_ids[:filter_size] if filter_size and len(devices_ids) > filter_size else devices_ids
        devices_ids = [x for x in devices_ids if x.isdigit()]

        print()
        print("Fetching devices details...")
        print(f"Getting details for {len(devices_ids)} devices...")
        devices_data = api_client.get_device_details_bulk(devices_ids)
        print("Processing devices data...")
        devices_df = processor.process_data_to_df(devices_data)
        print(f"Fetched {len(devices_data)} devices")
        
        devices_df['device_id'] = devices_df['device_id'].astype(str)
        devices_df['vehicle_id'] = devices_df['vehicle_id'].astype(str)
        devices_df['vehicle_id'] = devices_df.apply(lambda row: row['device_id'] if (pd.isna(row['vehicle_id']) or row['vehicle_id'] == '0') else row['vehicle_id'], axis=1)

        result_df = pd.merge(org_groups_df, groups_df, left_on="org_group_id", right_on="org_group_id", how="outer")
        result_df = pd.merge(result_df, devices_df, left_on="device_id", right_on="vehicle_id", how="left")
        
        # Add timestamps
        print("Adding process timestamps...")
        result_df = processor.add_process_timestamps(result_df, process_start_time)

        print("Data processing completed")

        # Export to CSV
        csv_file = processor.export_to_csv(result_df, base_filename=PREFIX, process_start_time=process_start_time)

        print("Ezzloc pipeline completed successfully")
        return csv_file

    except Exception as e:
        print(f"Ezzloc pipeline failed: {e}")
        sys.exit(1)


# if __name__ == "__main__":
#     csv_path = generate_local_file()
#     print(f"Generated file: {csv_path}")
