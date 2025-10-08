"""
This is for downloading file


"""

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=8080)
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    return creds

def test_drive():
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)
    results = service.files().list(pageSize=5).execute()
    for f in results.get("files", []):
        print(f['name'], f['id'])

if __name__ == "__main__":
    test_drive()
