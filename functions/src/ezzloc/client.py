import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.ezzloc.config import BASE_URL, ACCOUNT_ID, NEED_COUNT, STATUS, PAGESIZE_DEVICES, LANGUANGE


class EzzlocClient:
    def __init__(self, username, token):
        self.username = username
        self.token = token
        self.base_url = BASE_URL

    def get_org_groups(self, page_size=None, current_page=1):
        """Fetch device list from tree API and return flattened device data."""
        org_groups_url = f"{self.base_url}/system/user/treeListSingleUser"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.get(org_groups_url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        if response_data.get("code") != 200:
            raise RuntimeError(f"API error: {response_data.get('msg', 'Unknown error')}")
        groups_data = response_data.get('data', [])

        # Parse tree to get flattened devices
        flattened_groups_data = self._parse_org_group_data(groups_data)
        # print(f"type(flattened_groups_data): {type(flattened_groups_data)}")
        return flattened_groups_data

    def _parse_org_group_data(self, tree_data, current_path=None):
        """Recursively parse the device tree and return flattened device list"""
        groups = []
        if current_path is None: current_path = []

        if isinstance(tree_data, dict): nodes = [tree_data]
        elif isinstance(tree_data, list):nodes = tree_data
        else: return groups

        for node in nodes:
            id = node.get("id")
            label = node.get("label", "").split("(")[0]
            node_path = current_path + [label]
            children = node.get("children", [])

            if not children:
                groups.append({
                    "org_group_id": id,
                    "org_group_label": label,
                    "org_group_path": "/".join(current_path)
                })
            else:
                groups.extend(self._parse_org_group_data(children, node_path))

        return groups


    def get_group_details_bulk(self, groups_ids):
        """Fetch locations for multiple IMEIs in parallel."""
        all_group_data = []
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.get_group_details, group_id): group_id for group_id in groups_ids}
            for future in as_completed(futures):
                group_id = futures[future]
                try:
                    group_detail_data = future.result()
                    for detail in group_detail_data:
                        detail['org_group_id'] = group_id
                    all_group_data.extend(group_detail_data)
                except Exception as e:
                    print(f"Error fetching details for ID {group_id}: {e}")
                    all_group_data[group_id] = None
        # print(f"all_group_data: {all_group_data}")
        return all_group_data
    

    def get_group_details(self, group_id):
        """Fetch devices details for a group ID."""
        details_url = f"{self.base_url}/monitor/AiTrackM/getUserGroupVehicles?userIDStr={group_id}&type=0"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        response = None
        while True:
            response = requests.get(details_url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get("code") == 200: break
        
        groups_details_data = response.json()
        groups_details_data = groups_details_data.get("data", {}).get("data",[])
        flattened_groups_details_data = self._parse_group_detail_data(groups_details_data)
        return flattened_groups_details_data

    
    def _parse_group_detail_data(self, tree_data, level=0, group_id=None, group_name=None):
        """Recursively parse the device tree and return flattened device list"""
        groups_details = []
        
        if isinstance(tree_data, dict): nodes = [tree_data]
        elif isinstance(tree_data, list):nodes = tree_data
        else: return groups_details

        for node in nodes:
            children = node.get("children", [])
            if not children:
                if level == 0: continue
                device_id = node.get("id")
                groups_details.append({
                    "group_id": group_id,
                    "group_name": group_name,
                    "device_id": device_id
                })
            else: 
                if not group_id: group_id = node.get("id")
                if not group_name: group_name = node.get("name")
                groups_details.extend(self._parse_group_detail_data(children, level+1, group_id, group_name))
        return groups_details
    




    def get_device_details_bulk(self, device_ids):
        """Fetch locations for multiple devices id in parallel."""
        all_device_data = []
        chunk_size = 20
        chunks = [device_ids[i:i+chunk_size] for i in range(0, len(device_ids), chunk_size)]
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = {executor.submit(self.get_device_details, chunk): chunk for chunk in chunks}
            for future in as_completed(futures):
                device_id = futures[future]
                try:
                    device_detail_data = future.result()
                    all_device_data.extend(device_detail_data)
                except Exception as e:
                    print(f"Error fetching details for device ID {device_id}: {e}")
                    all_device_data[device_id] = None
        return all_device_data
    

    def get_device_details(self, devices_ids):
        """Fetch devices details for a device ID."""
        devices_str = ",".join([x.strip() for x in devices_ids]) if isinstance(devices_ids, list) else devices_ids.strip()
        
        devices_url = f"{self.base_url}/monitor/AiTrackM/getVehiclesLocation?vehicleIDs={devices_str}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        response = None
        while True:
            response = requests.get(devices_url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get("code") == 200: break

        devices_data = response.json()
        devices_data = devices_data.get("data", {})
        
        return devices_data

    
    # def _parse_device_detail_data(self, tree_data, group_id=None, group_name=None):
    #     """Recursively parse the device tree and return flattened device list"""
    #     groups_details = []
        
    #     if isinstance(tree_data, dict): nodes = [tree_data]
    #     elif isinstance(tree_data, list):nodes = tree_data
    #     else: return groups_details

    #     for node in nodes:
    #         children = node.get("children", [])
    #         if not children:
    #             device_id = node.get("id")
    #             groups_details.append({
    #                 # "group_id": group_id,
    #                 # "group_name": group_name,
    #                 # "device_id": device_id
    #             })
    #         else: 
    #             if not group_id: group_id = node.get("id")
    #             if not group_name: group_name = node.get("name")
    #             groups_details.extend(self._parse_group_detail_data(children, group_id, group_name))
    #     return groups_details
    
