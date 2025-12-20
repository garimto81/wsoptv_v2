"""
이전 Google Drive 폴더 정리 스크립트
- 기존 폴더의 모든 파일 삭제 (휴지통으로 이동)
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Google API 설정
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'

# 이전 폴더 ID (삭제 대상)
OLD_FOLDER_ID = '1kHuCfqD7PPkybWXRL3pqeNISTPT7LUTB'


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


def list_files_in_folder(drive_service, folder_id):
    """폴더 내 모든 파일 목록 조회"""
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get('files', [])


def delete_file(drive_service, file_id):
    """파일 삭제 (휴지통으로 이동)"""
    drive_service.files().update(
        fileId=file_id,
        body={'trashed': True}
    ).execute()


def main():
    print("=" * 60)
    print("이전 Google Drive 폴더 정리")
    print(f"폴더 ID: {OLD_FOLDER_ID}")
    print("=" * 60)

    # 인증
    print("\n[1/3] Google API 인증...")
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    # 파일 목록 조회
    print("\n[2/3] 파일 목록 조회...")
    files = list_files_in_folder(drive_service, OLD_FOLDER_ID)
    print(f"  발견된 파일: {len(files)}개")

    if not files:
        print("\n폴더가 이미 비어 있습니다.")
        return

    # 파일 삭제
    print("\n[3/3] 파일 삭제 중...")
    deleted_count = 0

    for file in files:
        file_name = file['name']
        file_id = file['id']
        file_type = file['mimeType']

        try:
            delete_file(drive_service, file_id)
            print(f"  삭제: {file_name}")
            deleted_count += 1
        except Exception as e:
            print(f"  실패: {file_name} - {e}")

    print("\n" + "=" * 60)
    print(f"정리 완료!")
    print(f"  삭제된 파일: {deleted_count}개")
    print(f"  (휴지통에서 30일 후 영구 삭제)")
    print("=" * 60)


if __name__ == "__main__":
    main()
