import os
import subprocess
import tarfile
from pathlib import Path
"""

This is only for backup converter 


"""



# Base directory where all backups are stored
BACKUP_DIR = Path.home() / "restore" / "docker_volumes"

# List of volumes and their corresponding backup files
VOLUME_BACKUPS = {
    "n8n_n8n_data": "n8n_n8n_data.tar.gz",
    "n8n_n8n_pg_data": "n8n_n8n_pg_data.tar.gz",
    "nginx-npm_npm_data": "nginx-npm_npm_data.tar.gz",
    "nginx-npm_npm_db_data": "nginx-npm_npm_db_data.tar.gz",
    "nginx-npm_npm_letsencrypt": "nginx-npm_npm_letsencrypt.tar.gz",
}


def create_volume(volume_name):
    """Create a Docker volume if it doesn't already exist"""
    print(f"🔹 Checking volume: {volume_name}")
    result = subprocess.run(
        ["docker", "volume", "ls", "-q", "--filter", f"name={volume_name}"],
        capture_output=True, text=True
    )
    if volume_name not in result.stdout.strip().split("\n"):
        print(f"📦 Creating volume: {volume_name}")
        subprocess.run(["docker", "volume", "create", volume_name], check=True)
    else:
        print(f"✅ Volume already exists: {volume_name}")


def restore_volume(volume_name, backup_file):
    """Extract backup into the Docker volume"""
    print(f"♻️ Restoring {volume_name} from {backup_file}")

    backup_path = BACKUP_DIR / backup_file
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_path}")
        return

    mount_point = Path(f"/var/lib/docker/volumes/{volume_name}/_data")

    if not mount_point.exists():
        print(f"❌ Volume mount point not found: {mount_point}")
        return

    print(f"📂 Extracting {backup_path} → {mount_point}")
    with tarfile.open(backup_path, "r:gz") as tar:
        tar.extractall(path=mount_point)
    print(f"✅ Restored {volume_name} successfully!")


def main():
    print(f"🚀 Starting restore from directory: {BACKUP_DIR}\n")
    if not BACKUP_DIR.exists():
        print(f"❌ Backup directory not found: {BACKUP_DIR}")
        return

    for volume, backup in VOLUME_BACKUPS.items():
        create_volume(volume)
        restore_volume(volume, backup)

    print("\n🎉 All Docker volumes have been restored successfully!")


if __name__ == "__main__":
    main()

