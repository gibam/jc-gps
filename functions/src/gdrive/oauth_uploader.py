"""
Google Drive OAuth Uploader Module
Handles uploading files to Google Drive using OAuth 2.0 with refresh token.
"""

import os
from datetime import datetime, timedelta
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io


class GoogleDriveOAuthUploader:
    """Uploader class for Google Drive operations using OAuth."""

    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    TOKEN_URI = 'https://oauth2.googleapis.com/token'

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        folder_id: str = None
    ):
        """
        Initialize the Google Drive OAuth uploader.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.folder_id = folder_id
        self._service = None
        self._credentials = None

    @property
    def credentials(self) -> Credentials:
        if self._credentials is None or not self._credentials.valid:
            self._credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
                token_uri=self.TOKEN_URI,
                scopes=self.SCOPES
            )
            if self._credentials.expired:
                self._credentials.refresh(Request())
        return self._credentials

    @property
    def service(self):
        if self._service is None:
            self._service = build('drive', 'v3', credentials=self.credentials)
        return self._service

    def upload_local_file_to_drive(self, filepath: str, folder_id: str = None) -> str:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        target_folder_id = folder_id or self.folder_id
        
        if not target_folder_id:
            raise ValueError("No folder_id provided for upload")

        filename = os.path.basename(filepath)
        
        file_metadata = {
            'name': filename,
            'parents': [target_folder_id]
        }

        media = MediaFileUpload(filepath)
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return file.get('webViewLink')

    def get_or_create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        target_parent = parent_folder_id or self.folder_id
        
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if target_parent:
            query += f" and '{target_parent}' in parents and trashed=false"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        folders = results.get('files', [])
        
        if folders:
            return folders[0]['id']

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
        }
        
        if target_parent:
            file_metadata['parents'] = [target_parent]

        folder = self.service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()

        return folder.get('id')

    def check_if_file_exists_today(self, folder_name: str, start_hour: int, now: datetime, parent_folder_id: str=None) -> bool:
        historic_folder_id = self.get_or_create_folder(folder_name, parent_folder_id)
        
        query = f"'{historic_folder_id}' in parents and trashed=false"
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(name, createdTime)'
        ).execute()
        
        files = results.get('files', [])
        
        # Pattern to extract yyyy-mm-dd
        pattern = re.compile(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})')
        
        for file in files:
            match = pattern.search(file['name'])
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
                file_dt = datetime.strptime(f"{date_str} {time_str.replace('-', ':')}", "%Y-%m-%d %H:%M:%S")
                
                adjusted_file_dt = file_dt - timedelta(hours=start_hour)
                adjusted_now = now - timedelta(hours=start_hour)
                
                if adjusted_file_dt.date() == adjusted_now.date():
                    print(f"File already exists for today's window: {file['name']}")
                    return True
                
        return False

    def upload_or_update_file(self, filename: str, filepath: str, folder_id: str) -> str:
        """Uploads a new file or updates an existing one by name."""
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        files = results.get('files', [])

        media = MediaFileUpload(filepath)
        
        if files:
            # Update
            file_id = files[0]['id']
            file = self.service.files().update(
                fileId=file_id,
                media_body=media,
                fields='webViewLink'
            ).execute()
        else:
            # Create
            file_metadata = {'name': filename, 'parents': [folder_id]}
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='webViewLink'
            ).execute()
        
        return file.get('webViewLink')

    def upload_with_history(self, filepath: str, folder_id: str = None) -> dict:
        target_folder_id = folder_id or self.folder_id
        
        if not target_folder_id:
            raise ValueError("No folder_id provided for upload")

        filename = os.path.basename(filepath)
        
        # Determine base filename (remove timestamp)
        pattern = r'_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})'
        base_name = re.sub(pattern, '', os.path.splitext(filename)[0])
        root_filename = f"{base_name}{os.path.splitext(filename)[1]}"
        
        # 1. Update/Upload to root folder
        root_url = self.upload_or_update_file(root_filename, filepath, target_folder_id)
        
        # 2. Upload to historic folder
        historic_folder_id = self.get_or_create_folder('historico', target_folder_id)
        historic_file_metadata = {'name': filename, 'parents': [historic_folder_id]}
        historic_file = self.service.files().create(
            body=historic_file_metadata,
            media_body=MediaFileUpload(filepath),
            fields='webViewLink'
        ).execute()
        
        return {
            'root_url': root_url,
            'historic_url': historic_file.get('webViewLink')
        }
