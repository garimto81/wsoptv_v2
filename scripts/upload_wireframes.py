"""Upload wireframe images to Google Drive and update Google Docs."""
import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Paths
TOKEN_PATH = Path(r"D:\AI\claude01\json\token.json")
WIREFRAME_DIR = Path(r"D:\AI\claude01\wsoptv_v2\docs\wireframes\v2")
GOOGLE_DOC_ID = "1tghlhpQiWttpB-0CP5c1DiL5BJa4ttWj-2R77xaoVI8"

# Files to upload
FILES = [
    "00-full-page.png",
    "01-header.png",
    "02-hero-banner.png",
    "03-continue-watching.png",
    "04-recently-added.png",
    "05-series-section.png",
    "06-footer.png",
]


def get_credentials():
    """Load credentials from token.json."""
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)

    return Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )


def upload_to_drive(drive_service, file_path, folder_id=None):
    """Upload a file to Google Drive."""
    file_name = os.path.basename(file_path)

    file_metadata = {"name": file_name}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, mimetype="image/png")

    # Check if file already exists
    query = f"name='{file_name}' and trashed=false"
    if folder_id:
        query += f" and '{folder_id}' in parents"

    results = drive_service.files().list(q=query, fields="files(id)").execute()
    existing_files = results.get("files", [])

    if existing_files:
        # Update existing file
        file_id = existing_files[0]["id"]
        file = drive_service.files().update(
            fileId=file_id,
            media_body=media,
        ).execute()
        print(f"  Updated: {file_name} (ID: {file_id})")
    else:
        # Create new file
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()
        file_id = file.get("id")
        # Make file publicly accessible
        drive_service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()
        print(f"  Created: {file_name} (ID: {file_id})")

    return file_id


def main():
    """Main function."""
    print("Loading credentials...")
    creds = get_credentials()

    print("Building Drive service...")
    drive_service = build("drive", "v3", credentials=creds)

    print("\nUploading wireframe images to Google Drive...")
    image_ids = {}

    for file_name in FILES:
        file_path = WIREFRAME_DIR / file_name
        if file_path.exists():
            image_id = upload_to_drive(drive_service, str(file_path))
            image_ids[file_name] = image_id
        else:
            print(f"  Skipped (not found): {file_name}")

    print("\n--- Image IDs ---")
    for name, id_ in image_ids.items():
        print(f"{name}: {id_}")

    # Save image IDs for later use
    ids_path = WIREFRAME_DIR / "image_ids.json"
    with open(ids_path, "w") as f:
        json.dump(image_ids, f, indent=2)
    print(f"\nSaved image IDs to: {ids_path}")


if __name__ == "__main__":
    main()
