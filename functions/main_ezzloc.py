import os
from firebase_functions import https_fn, scheduler_fn
from dotenv import load_dotenv

from src.ezzloc.main import generate_local_file
from src.gdrive.oauth_uploader import GoogleDriveOAuthUploader
from src.ezzloc.config import PREFIX

from zoneinfo import ZoneInfo
from datetime import datetime

load_dotenv()


# @https_fn.on_request()
@scheduler_fn.on_schedule(
    schedule="every 60 minutes",
    timezone="America/Santiago",
    max_instances=1,
    timeout_sec=300              # 5 mins
)
def run_ezzloc_process(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Cloud Function that orchestrates Ezzloc data extraction and Google Drive upload.
    
    Flow:
    1. Check if file already exists for today
    2. Generate local CSV file from Ezzloc data
    3. Upload/Update the file in Google Drive
    """
    try:
        # Configuration from environment variables (OAuth)
        gdrive_client_id        = os.getenv('GDRIVE_CLIENT_ID')
        gdrive_client_secret    = os.getenv('GDRIVE_CLIENT_SECRET')
        gdrive_refresh_token    = os.getenv('GDRIVE_REFRESH_TOKEN')
        gdrive_folder_id        = os.getenv('GDRIVE_FOLDER_ID')
        start_hour              = os.getenv('GDRIVE_START_HOUR', 8)
        timezone                = os.getenv('TIMEZONE', 'America/Santiago')
        now = datetime.now(ZoneInfo(timezone))
        
        # Validate required OAuth credentials
        if not all([gdrive_client_id, gdrive_client_secret, gdrive_refresh_token, gdrive_folder_id]):
            print("Missing environment variables for GDrive")
            return
        
        # Prepare uploader
        uploader = GoogleDriveOAuthUploader(
            client_id=gdrive_client_id,
            client_secret=gdrive_client_secret,
            refresh_token=gdrive_refresh_token,
            folder_id=gdrive_folder_id
        )
        
        # Check if file already generated today
        try:
            if uploader.check_if_file_exists_today('historico', int(start_hour), now):
                print("File already generated today. Skipping.")
                return
        except: pass
        
        # Step 1: Generate local CSV file
        print("Step 1: Generating local CSV file...")
        csv_filepath = generate_local_file(now)
        print(f"CSV file generated: {csv_filepath}")
        
        # Step 2: Upload to Google Drive using OAuth (with history)
        print("Step 2: Uploading to Google Drive (with history)...")
        upload_result = uploader.upload_with_history(csv_filepath)
        
        print(f"Success! Root: {upload_result['root_url']}, Historic: {upload_result['historic_url']}")
    
    except Exception as e:
        print(f"Error in run_ezzloc_process: {e}")
