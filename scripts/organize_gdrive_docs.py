"""
Google Drive 문서 정리 스크립트
- 루트 폴더에 _archive 서브폴더 생성
- 이전 버전 문서를 _archive로 이동
- 최종 버전만 루트에 유지
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


def list_documents_in_folder(drive_service, folder_id):
    """폴더 내 문서 목록 조회 (폴더 제외)"""
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name, mimeType, createdTime, modifiedTime)",
        orderBy="name"
    ).execute()
    return results.get('files', [])


def extract_version(name):
    """문서 이름에서 버전 추출"""
    # 패턴: v1, v2, v3, V1.0, v4.0 등
    match = re.search(r'[vV](\d+(?:\.\d+)?)', name)
    if match:
        version_str = match.group(1)
        return float(version_str)
    return None


def extract_base_name(name):
    """버전 정보를 제외한 기본 이름 추출"""
    # 버전 패턴 제거
    base = re.sub(r'\s*[vV]\d+(?:\.\d+)?\s*', ' ', name)
    # 연속 공백 정리
    base = re.sub(r'\s+', ' ', base).strip()
    return base


def group_documents_by_base_name(documents):
    """문서를 기본 이름으로 그룹화"""
    groups = {}

    for doc in documents:
        name = doc['name']
        base_name = extract_base_name(name)
        version = extract_version(name)

        if base_name not in groups:
            groups[base_name] = []

        groups[base_name].append({
            'id': doc['id'],
            'name': name,
            'version': version,
            'mimeType': doc['mimeType'],
            'modifiedTime': doc['modifiedTime']
        })

    return groups


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
    print("Google Drive 문서 정리")
    print("=" * 60)

    # 인증
    print("\n[1/4] Google API 인증...")
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    # _archive 폴더 생성
    print("\n[2/4] _archive 폴더 생성...")
    archive_folder_id = create_subfolder(drive_service, ROOT_FOLDER_ID, "_archive")

    # 루트 폴더 문서 목록 조회
    print("\n[3/4] 루트 폴더 문서 조회...")
    documents = list_documents_in_folder(drive_service, ROOT_FOLDER_ID)
    print(f"  발견된 문서: {len(documents)}개")

    for doc in documents:
        print(f"    - {doc['name']}")

    if not documents:
        print("\n정리할 문서가 없습니다.")
        return

    # 문서 그룹화
    print("\n[4/4] 문서 정리...")
    groups = group_documents_by_base_name(documents)

    moved_count = 0
    kept_count = 0

    for base_name, docs in groups.items():
        if len(docs) == 1:
            # 단일 문서는 그대로 유지
            print(f"  유지: {docs[0]['name']}")
            kept_count += 1
            continue

        # 여러 버전이 있는 경우, 최신 버전만 유지
        # 버전 번호가 있으면 가장 높은 것, 없으면 수정 시간 기준
        docs_with_version = [d for d in docs if d['version'] is not None]
        docs_without_version = [d for d in docs if d['version'] is None]

        if docs_with_version:
            # 버전 번호로 정렬
            docs_with_version.sort(key=lambda x: x['version'], reverse=True)
            latest = docs_with_version[0]
            old_docs = docs_with_version[1:] + docs_without_version
        else:
            # 수정 시간으로 정렬
            docs.sort(key=lambda x: x['modifiedTime'], reverse=True)
            latest = docs[0]
            old_docs = docs[1:]

        print(f"\n  그룹: {base_name}")
        print(f"    최신 유지: {latest['name']}")
        kept_count += 1

        for old_doc in old_docs:
            try:
                move_file(drive_service, old_doc['id'], ROOT_FOLDER_ID, archive_folder_id)
                print(f"    아카이브: {old_doc['name']}")
                moved_count += 1
            except Exception as e:
                print(f"    이동 실패: {old_doc['name']} - {e}")

    print("\n" + "=" * 60)
    print(f"정리 완료!")
    print(f"  유지된 문서: {kept_count}개")
    print(f"  아카이브된 문서: {moved_count}개")
    print(f"\n폴더 구조:")
    print(f"  루트: https://drive.google.com/drive/folders/{ROOT_FOLDER_ID}")
    print(f"  아카이브: https://drive.google.com/drive/folders/{archive_folder_id}")
    print("=" * 60)

    return archive_folder_id


if __name__ == "__main__":
    main()
