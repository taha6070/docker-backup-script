import os
import subprocess
import shutil
import time
from datetime import datetime
from zipfile import ZipFile
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

# ============ CONFIGURATION ============
ROOT_PATH = "/root"
BACKUP_BASE = "/tmp/server_backup"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
ZIP_FILE = f"/tmp/server_backup_{TIMESTAMP}.zip"
MAX_RETRIES = 5
SCOPES = ['https://www.googleapis.com/auth/drive.file']
# =======================================


def run_command(cmd):
    """Safely run shell commands and handle errors."""
    try:
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Command failed: {e}")
        return False
    return True


def backup_root_folder():
    """Backup all files under /root."""
    print("[*] Backing up /root directory...")
    dest_dir = os.path.join(BACKUP_BASE, "root_backup")
    os.makedirs(dest_dir, exist_ok=True)

    run_command(["rsync", "-a", "--exclude", "*.zip", "--exclude", "venv", f"{ROOT_PATH}/", dest_dir])
    print("[+] /root backup completed.")


def backup_docker_volumes():
    """Export all Docker volumes as .tar.gz files."""
    print("[*] Exporting Docker volumes...")
    dest_dir = os.path.join(BACKUP_BASE, "docker_volumes")
    os.makedirs(dest_dir, exist_ok=True)

    result = subprocess.run(["docker", "volume", "ls", "-q"], capture_output=True, text=True)
    volumes = result.stdout.strip().splitlines()

    if not volumes:
        print("[!] No Docker volumes found.")
        return

    for vol in volumes:
        out_file = os.path.join(dest_dir, f"{vol}.tar.gz")
        print(f"  - Exporting volume: {vol}")
        run_command([
            "docker", "run", "--rm",
            "-v", f"{vol}:/volume",
            "-v", f"{dest_dir}:/backup",
            "alpine",
            "tar", "czf", f"/backup/{vol}.tar.gz", "-C", "/volume", "."
        ])
    print("[+] Docker volumes backup completed.")


def compress_backup():
    """Compress the backup directory into a zip."""
    print("[*] Compressing backup into zip...")
    with ZipFile(ZIP_FILE, "w") as zipf:
        for root, _, files in os.walk(BACKUP_BASE):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BACKUP_BASE)
                zipf.write(file_path, arcname)
    shutil.rmtree(BACKUP_BASE)
    print(f"[+] Backup compressed at {ZIP_FILE}")


def upload_to_gdrive(file_path):
    """Upload backup to Google Drive with retry logic."""
    print("[*] Uploading to Google Drive...")
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('drive', 'v3', credentials=creds)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            file_metadata = {'name': os.path.basename(file_path)}
            media = MediaFileUpload(file_path, resumable=True)
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"[+] Upload successful: {file.get('id')}")
            return
        except Exception as e:
            print(f"[!] Upload failed (attempt {attempt}/{MAX_RETRIES}): {e}")
            wait = attempt * 10
            print(f"[*] Retrying in {wait}s...")
            time.sleep(wait)
    print("[x] All retries failed. Upload aborted.")


def main():
    start_time = time.time()
    print("🚀 Starting full server backup...")

    os.makedirs(BACKUP_BASE, exist_ok=True)
    backup_root_folder()
    backup_docker_volumes()
    compress_backup()
    upload_to_gdrive(ZIP_FILE)

    duration = time.time() - start_time
    print(f"✅ Backup process completed in {round(duration/60, 2)} minutes.")


if __name__ == "__main__":
    main()
