# """
# Google Drive Uploader Module
# Handles uploading files to Google Drive using a service account.
# """

# import os
# from google.auth.transport.requests import Request
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload


# class GoogleDriveUploader:
#     """Uploader class for Google Drive operations."""

#     SCOPES = ['https://www.googleapis.com/auth/drive.file']

#     def __init__(self, credentials_path: str, folder_id: str):
#         """
#         Initialize the Google Drive uploader.

#         Args:
#             credentials_path: Path to the service account JSON file.
#             folder_id: Google Drive folder ID to upload files to.
#         """
#         self.credentials_path = credentials_path
#         self.folder_id = folder_id
#         self._service = None

#     @property
#     def service(self):
#         """Lazy initialization of the Drive service."""
#         if self._service is None:
#             credentials = service_account.Credentials.from_service_account_file(
#                 self.credentials_path, scopes=self.SCOPES
#             )
#             self._service = build('drive', 'v3', credentials=credentials)
#         return self._service

#     def upload_local_file_to_drive(self, filepath: str) -> str:
#         """
#         Upload a local file to Google Drive.

#         Args:
#             filepath: Path to the local file to upload.

#         Returns:
#             str: Web view URL of the uploaded file.

#         Raises:
#             FileNotFoundError: If the local file does not exist.
#             Exception: If the upload fails.
#         """
#         if not os.path.exists(filepath):
#             raise FileNotFoundError(f"File not found: {filepath}")

#         filename = os.path.basename(filepath)
        
#         file_metadata = {
#             'name': filename,
#             'parents': [self.folder_id]
#         }

#         media = MediaFileUpload(filepath)
        
#         file = self.service.files().create(
#             body=file_metadata,
#             media_body=media,
#             fields='id, webViewLink',
#             supportsAllDrives=True  # Add this line
#         ).execute()

#         print(f"File uploaded successfully: {filename}")
#         print(f"File ID: {file.get('id')}")
#         print(f"URL: {file.get('webViewLink')}")
        
#         return file.get('webViewLink')

#     def get_or_create_folder(self, folder_name: str) -> str:
#         """
#         Get or create a folder in Google Drive.

#         Args:
#             folder_name: Name of the folder to get or create.

#         Returns:
#             str: Folder ID.
#         """
#         # Search for existing folder
#         results = self.service.files().list(
#             q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{self.folder_id}' in parents",
#             spaces='drive',
#             fields='files(id, name)'
#         ).execute()

#         folders = results.get('files', [])
        
#         if folders:
#             folder_id = folders[0]['id']
#             print(f"Folder already exists: {folder_name} (ID: {folder_id})")
#             return folder_id

#         # Create new folder
#         file_metadata = {
#             'name': folder_name,
#             'mimeType': 'application/vnd.google-apps.folder',
#             'parents': [self.folder_id]
#         }

#         folder = self.service.files().create(
#             body=file_metadata,
#             fields='id'
#         ).execute()

#         folder_id = folder.get('id')
#         print(f"Folder created: {folder_name} (ID: {folder_id})")
#         return folder_id
