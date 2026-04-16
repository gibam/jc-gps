from datetime import datetime
import os
import pandas as pd
from pandas import DataFrame
# from scripts.ezzloc.config import STATUS_CODES


class DataProcessor:
    @staticmethod
    def process_data_to_df(data, prefix:str=None):
        """Process raw device data into clean DataFrame."""
        if not data:
            raise ValueError("No device data to process")

        # Create DataFrame
        df = pd.DataFrame.from_records(data)
        for col in df.columns:
            try:
                tmp_df = pd.json_normalize(df[col])
                if not tmp_df.empty:
                    for tmp_col in tmp_df.columns:
                        if tmp_col in df.columns:
                            df.drop(tmp_col, axis=1, inplace=True)
                    df = df.drop(col, axis=1)
                    df = pd.concat([df, tmp_df], axis=1)
            except Exception as e:
                # print(f"EXCEPTION df[{col}]: {e}")
                # print(df[col])
                continue

        # Normalize column names (snake_case)
        df.columns = [x.replace("ID", "Id") if "ID" in x else x for x in df.columns]
        df.columns = ["".join(["_"+c.lower() if c.isalpha and c.isupper() else c for c in x]) for x in df.columns]
        new_cols = []
        for col in df.columns:
            new_col = []
            for i in range(len(col)):
                if i > 0 and col[i].isdigit() and col[i-1].isalpha(): new_col.append("_")
                new_col.append(col[i])
            new_cols.append("".join(new_col))
        df.columns = new_cols

        if prefix:
            df.columns = [ prefix+"_"+x if not x.startswith(prefix) else x for x in df.columns]

        # Ensure no duplicate columns
        if len(df.columns) != len(set(df.columns)):
            raise ValueError("Duplicate columns found after processing")

        return df

    @staticmethod
    def add_details_data(df:DataFrame, details_dict):
        """Add location data to DataFrame."""
        # Ezzloc currently doesn't have location API implementation
        # Add placeholder location data
        df["details"] = df["id"].map(details_dict)
        return df

    @staticmethod
    def add_process_timestamps(df, start_time):
        """Add process start and end timestamps."""
        df["process_start_time"] = start_time.replace(microsecond=0)
        df["process_end_time"] = datetime.now().replace(microsecond=0)
        return df

    @staticmethod
    def export_to_csv(df, base_filename="devices", process_start_time:datetime=None):
        """Export DataFrame to CSV with timestamped filename in output folder."""
        # Create output directory if it doesn't exist
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        # Generate timestamped filename
        timestamp = process_start_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{base_filename}_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)

        # Export to CSV
        df.to_csv(filepath, index=False, lineterminator='\r\n')
        print(f"Data exported to {filepath}")
        return filepath

    @staticmethod
    def validate_data(df):
        """Basic data validation."""
        if df.empty:
            raise ValueError("DataFrame is empty")
        # Ezzloc devices use "id" instead of "imei"
        if "id" not in df.columns:
            raise ValueError("DataFrame must contain 'id' column for Ezzloc devices")
        return True
