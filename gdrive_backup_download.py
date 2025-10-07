from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import re
from datetime import datetime

# ========================
# CONFIGURATION
# ========================
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DOWNLOAD_DIR = "/root/restore"  # Where backups will be saved
BACKUP_NAME_PATTERN = r"server_backup_\d{8}_\d{6}\.zip"  # match your uploaded file names
# ========================


def get_drive_service():
    """Authenticate and build Google Drive API client."""
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('drive', 'v3', credentials=creds)


def list_backups(service):
    """List all backup files on Google Drive that match the naming pattern."""
    print("[*] Searching for backup files on Google Drive...")
    results = service.files().list(
        q="mimeType='application/zip'",
        spaces='drive',
        fields="files(id, name, createdTime)",
        orderBy="createdTime desc"
    ).execute()

    files = results.get('files', [])
    backups = [f for f in files if re.match(BACKUP_NAME_PATTERN, f['name'])]

    if not backups:
        print("[x] No backup files found on Google Drive.")
        return []

    print(f"[+] Found {len(backups)} backup(s):")
    for f in backups:
        print(f"   - {f['name']} (created: {f['createdTime']})")
    return backups


def download_file(service, file_id, file_name):
    """Download a single file from Google Drive."""
    from googleapiclient.http import MediaIoBaseDownload
    import io

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    local_path = os.path.join(DOWNLOAD_DIR, file_name)

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(local_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"[*] Downloading {file_name}: {int(status.progress() * 100)}%")
    print(f"[+] Download completed: {local_path}")
    return local_path


def main():
    print("🚀 Starting Google Drive backup downloader...")
    service = get_drive_service()
    backups = list_backups(service)

    if not backups:
        return

    # Automatically select the latest backup
    latest = backups[0]
    print(f"[*] Downloading latest backup: {latest['name']}")
    download_file(service, latest['id'], latest['name'])

    print("✅ Latest backup downloaded successfully.")


if __name__ == "__main__":
    main()
