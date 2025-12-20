"""
Google Drive 문서 이름에서 버전 번호 제거
v1.0.0, v2.0.0 등 제거
"""

import os
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Google API 설정
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'

# 폴더 설정
ROOT_FOLDER_ID = '19Sbq1_K-fJOEN2LnMEaMTE9fYjAEFoou'


def get_credentials():
    """Google API 인증"""
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


def list_documents_in_folder(drive_service, folder_id):
    """폴더 내 문서 목록 조회"""
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get('files', [])


def remove_version_from_name(name):
    """이름에서 버전 번호 제거"""
    # 패턴: _v1.0.0, _v2.0.0, v1.0, v2 등
    new_name = re.sub(r'[_\s]*[vV]\d+(\.\d+)*(\.\d+)*', '', name)
    # 연속 공백/언더스코어 정리
    new_name = re.sub(r'_+', '_', new_name)
    new_name = re.sub(r'\s+', ' ', new_name)
    new_name = new_name.strip('_ ')
    return new_name


def rename_file(drive_service, file_id, new_name):
    """파일 이름 변경"""
    drive_service.files().update(
        fileId=file_id,
        body={'name': new_name}
    ).execute()


def main():
    print("=" * 60)
    print("Google Drive 문서 이름에서 버전 번호 제거")
    print("=" * 60)

    # 인증
    print("\n[1/2] Google API 인증...")
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    # 문서 목록 조회
    print("\n[2/2] 문서 이름 변경...")
    documents = list_documents_in_folder(drive_service, ROOT_FOLDER_ID)

    renamed_count = 0

    for doc in documents:
        old_name = doc['name']
        new_name = remove_version_from_name(old_name)

        if old_name != new_name:
            try:
                rename_file(drive_service, doc['id'], new_name)
                print(f"  {old_name}")
                print(f"    → {new_name}")
                renamed_count += 1
            except Exception as e:
                print(f"  실패: {old_name} - {e}")
        else:
            print(f"  유지: {old_name}")

    print("\n" + "=" * 60)
    print(f"완료! 이름 변경된 문서: {renamed_count}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
