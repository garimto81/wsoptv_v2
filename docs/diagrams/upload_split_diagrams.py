"""분리된 캘린더/로드맵 이미지 업로드"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
TARGET_FOLDER_ID = '1NqPboT9HsAfF2XPI9Xfot-nc0wcVA2uR'

# 업로드할 파일 목록
FILES_TO_UPLOAD = [
    '04a-calendar-h1.png',
    '04b-calendar-h2.png',
    '06a-roadmap-h1.png',
    '06b-roadmap-h2.png',
]


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds


def upload_file(service, file_path, folder_id):
    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='image/png')
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    return file


def make_public(service, file_id):
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()


def main():
    print("Uploading split calendar/roadmap images...")
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)

    diagrams_dir = r'D:\AI\claude01\wsoptv_v2\docs\diagrams'

    uploaded = []
    for file_name in FILES_TO_UPLOAD:
        file_path = os.path.join(diagrams_dir, file_name)
        if not os.path.exists(file_path):
            print(f"  SKIP: {file_name} (not found)")
            continue
        print(f"  Uploading: {file_name}...", end=' ')
        result = upload_file(service, file_path, TARGET_FOLDER_ID)
        make_public(service, result['id'])
        uploaded.append(result)
        print("OK")

    print(f"\n=== Uploaded {len(uploaded)} images ===\n")

    for file in uploaded:
        print(f"  {file['name']}")
        print(f"    ID: {file['id']}")
        print(f"    lh3 URL: https://lh3.googleusercontent.com/d/{file['id']}")

    # 결과 저장
    with open(os.path.join(diagrams_dir, 'split_image_ids.txt'), 'w') as f:
        for file in uploaded:
            f.write(f"{file['name']}:{file['id']}\n")

    print(f"\nResults saved to: split_image_ids.txt")


if __name__ == '__main__':
    main()
