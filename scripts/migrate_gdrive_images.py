"""
Google Drive 이미지 마이그레이션 스크립트
- 기존 폴더에서 새 폴더로 이미지 이동
- 서브폴더 구조 생성
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

# 폴더 설정
OLD_FOLDER_ID = '1kHuCfqD7PPkybWXRL3pqeNISTPT7LUTB'
NEW_ROOT_FOLDER_ID = '19Sbq1_K-fJOEN2LnMEaMTE9fYjAEFoou'

# 서브폴더 구조
SUBFOLDERS = {
    'content-strategy': 'WSOPTV 콘텐츠 전략 이미지',
    'wireframes': '와이어프레임',
    'architecture': '아키텍처 다이어그램',
}


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


def create_subfolder(drive_service, parent_id, folder_name):
    """서브폴더 생성 (없으면)"""
    # 기존 폴더 검색
    results = drive_service.files().list(
        q=f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()

    files = results.get('files', [])

    if files:
        print(f"  폴더 이미 존재: {folder_name} (ID: {files[0]['id']})")
        return files[0]['id']

    # 새 폴더 생성
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = drive_service.files().create(body=file_metadata, fields='id').execute()
    print(f"  폴더 생성됨: {folder_name} (ID: {folder['id']})")
    return folder['id']


def list_files_in_folder(drive_service, folder_id):
    """폴더 내 파일 목록 조회"""
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get('files', [])


def move_file(drive_service, file_id, old_parent_id, new_parent_id):
    """파일을 새 폴더로 이동"""
    drive_service.files().update(
        fileId=file_id,
        addParents=new_parent_id,
        removeParents=old_parent_id,
        fields='id, parents'
    ).execute()


def main():
    print("=" * 60)
    print("Google Drive 이미지 마이그레이션")
    print("=" * 60)

    # 인증
    print("\n[1/4] Google API 인증...")
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    # 서브폴더 생성
    print("\n[2/4] 서브폴더 생성...")
    subfolder_ids = {}
    for name, desc in SUBFOLDERS.items():
        subfolder_ids[name] = create_subfolder(drive_service, NEW_ROOT_FOLDER_ID, name)

    # 기존 폴더 파일 목록 조회
    print("\n[3/4] 기존 폴더 파일 조회...")
    files = list_files_in_folder(drive_service, OLD_FOLDER_ID)
    print(f"  발견된 파일: {len(files)}개")

    # 파일 분류 및 이동
    print("\n[4/4] 파일 이동 중...")
    moved_count = 0

    for file in files:
        file_name = file['name']
        file_id = file['id']

        # 이미지 파일만 처리 (PNG, JPG 등)
        if not file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
            print(f"  스킵 (이미지 아님): {file_name}")
            continue

        # 콘텐츠 전략 이미지인지 확인 (숫자-이름 패턴)
        if file_name[0:2].isdigit() or 'content' in file_name.lower() or 'strategy' in file_name.lower():
            target_folder = 'content-strategy'
        elif 'wireframe' in file_name.lower() or 'ux' in file_name.lower():
            target_folder = 'wireframes'
        elif 'architecture' in file_name.lower() or 'diagram' in file_name.lower():
            target_folder = 'architecture'
        else:
            target_folder = 'content-strategy'  # 기본값

        try:
            move_file(drive_service, file_id, OLD_FOLDER_ID, subfolder_ids[target_folder])
            print(f"  이동: {file_name} → {target_folder}/")
            moved_count += 1
        except Exception as e:
            print(f"  실패: {file_name} - {e}")

    print("\n" + "=" * 60)
    print(f"마이그레이션 완료!")
    print(f"  이동된 파일: {moved_count}개")
    print(f"\n새 폴더 구조:")
    print(f"  루트: https://drive.google.com/drive/folders/{NEW_ROOT_FOLDER_ID}")
    for name, folder_id in subfolder_ids.items():
        print(f"    └── {name}/: https://drive.google.com/drive/folders/{folder_id}")
    print("=" * 60)

    return subfolder_ids


if __name__ == "__main__":
    subfolder_ids = main()

    # 결과 출력 (스크립트 업데이트용)
    print("\n스크립트 업데이트용 폴더 ID:")
    print(f"  NEW_ROOT_FOLDER_ID = '{NEW_ROOT_FOLDER_ID}'")
    for name, folder_id in subfolder_ids.items():
        print(f"  {name.upper().replace('-', '_')}_FOLDER_ID = '{folder_id}'")
