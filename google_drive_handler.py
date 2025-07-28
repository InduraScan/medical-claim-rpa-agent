import os
import io
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import logging

logger = logging.getLogger(__name__)

class GoogleDriveHandler:
    """Handles Google Drive operations for the RPA agent"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            creds = None
            
            # Check if token.pickle exists
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if os.path.exists('credentials.json'):
                        flow = Flow.from_client_secrets_file(
                            'credentials.json', self.SCOPES)
                        flow.redirect_uri = 'http://localhost:8080/callback'
                        
                        # For deployment, we'll use environment variables
                        if os.getenv('GOOGLE_CLIENT_ID'):
                            creds = self._create_credentials_from_env()
                        else:
                            logger.warning("No credentials.json found and no environment variables set")
                            return
                    else:
                        logger.warning("No credentials.json file found")
                        return
                
                # Save the credentials for the next run
                if creds:
                    with open('token.pickle', 'wb') as token:
                        pickle.dump(creds, token)
            
            self.credentials = creds
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Drive")
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            self.service = None
    
    def _create_credentials_from_env(self):
        """Create credentials from environment variables (for deployment)"""
        try:
            from google.oauth2.credentials import Credentials
            
            # This is a simplified approach for demo purposes
            # In production, you'd want a more secure token management system
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
            
            if all([client_id, client_secret, refresh_token]):
                creds = Credentials(
                    token=None,
                    refresh_token=refresh_token,
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=self.SCOPES
                )
                creds.refresh(Request())
                return creds
            
        except Exception as e:
            logger.error(f"Failed to create credentials from environment: {str(e)}")
        
        return None
    
    def is_authenticated(self) -> bool:
        """Check if authenticated with Google Drive"""
        return self.service is not None
    
    def download_file(self, file_id: str) -> tuple:
        """Download a file from Google Drive and return its content and name"""
        if not self.service:
            raise Exception("Not authenticated with Google Drive")
        
        try:
            # Get file metadata
            file_metadata = self.service.files().get(fileId=file_id).execute()
            filename = file_metadata.get('name', 'unknown_file')
            
            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Return content as string and filename
            file_content.seek(0)
            content_str = file_content.read().decode('utf-8')
            
            logger.info(f"Successfully downloaded file: {filename}")
            return content_str, filename
            
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {str(e)}")
            raise Exception(f"Failed to download file: {str(e)}")
    
    def upload_file(self, file_content: io.BytesIO, filename: str, parent_folder_id: str = None) -> str:
        """Upload a file to Google Drive and return the file ID"""
        if not self.service:
            raise Exception("Not authenticated with Google Drive")
        
        try:
            # Prepare file metadata
            file_metadata = {'name': filename}
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            # Create MediaIoBaseUpload object
            file_content.seek(0)
            media = MediaIoBaseUpload(
                file_content,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                resumable=True
            )
            
            # Upload file
            file_result = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file_result.get('id')
            logger.info(f"Successfully uploaded file: {filename} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {str(e)}")
            raise Exception(f"Failed to upload file: {str(e)}")
    
    def list_files(self, folder_id: str = None, file_type: str = 'csv') -> list:
        """List files in Google Drive"""
        if not self.service:
            raise Exception("Not authenticated with Google Drive")
        
        try:
            query = f"mimeType='text/csv'" if file_type == 'csv' else ""
            if folder_id:
                query += f" and '{folder_id}' in parents" if query else f"'{folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} files")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """Create a folder in Google Drive"""
        if not self.service:
            raise Exception("Not authenticated with Google Drive")
        
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created folder: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except Exception as e:
            logger.error(f"Failed to create folder {folder_name}: {str(e)}")
            raise Exception(f"Failed to create folder: {str(e)}")
    
    def get_file_info(self, file_id: str) -> dict:
        """Get file information"""
        if not self.service:
            raise Exception("Not authenticated with Google Drive")
        
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields='id, name, size, mimeType, modifiedTime, createdTime'
            ).execute()
            
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_id}: {str(e)}")
            return {}
    
    def share_file(self, file_id: str, email: str = None, role: str = 'reader') -> bool:
        """Share a file with specific permissions"""
        if not self.service:
            raise Exception("Not authenticated with Google Drive")
        
        try:
            permission = {
                'type': 'user' if email else 'anyone',
                'role': role
            }
            
            if email:
                permission['emailAddress'] = email
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            logger.info(f"Successfully shared file {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to share file {file_id}: {str(e)}")
            return False