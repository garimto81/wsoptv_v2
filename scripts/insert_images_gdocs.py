"""
Google Docs에 이미지 삽입 - 다른 방식 시도
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '1431Dz71jRV78o6-bwgR6sVM573bnGKf9-9Ozyo6hKpg'
FOLDER_ID = '1kHuCfqD7PPkybWXRL3pqeNISTPT7LUTB'

IMAGE_DIR = r'D:\AI\claude01\wsoptv_v2\docs\wireframes\v2'


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


def get_public_image_url(drive_service, file_path, folder_id):
    """이미지를 Drive에 업로드하고 공개 URL 반환"""
    file_name = os.path.basename(file_path)

    # 기존 파일 검색
    results = drive_service.files().list(
        q=f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
        fields="files(id, webContentLink)"
    ).execute()

    files = results.get('files', [])

    if files:
        file_id = files[0]['id']
        print(f"  기존 파일 사용: {file_name} ({file_id})")
    else:
        # 새 파일 업로드
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='image/png')
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        file_id = file['id']
        print(f"  새 파일 업로드: {file_name} ({file_id})")

    # 공개 권한 설정
    try:
        drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
    except:
        pass  # 이미 공개 상태일 수 있음

    # 직접 접근 가능한 URL 반환
    return f"https://drive.google.com/uc?export=view&id={file_id}"


def find_placeholder_positions(docs_service, doc_id):
    """플레이스홀더 텍스트 위치 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    placeholders = []

    for element in content:
        if 'paragraph' not in element:
            continue

        paragraph = element['paragraph']
        elements = paragraph.get('elements', [])

        text = ''
        for elem in elements:
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')

        text = text.strip()
        if text.startswith('[') and ':' in text and ']' in text:
            placeholders.append({
                'text': text,
                'start': element['startIndex'],
                'end': element['endIndex']
            })

    return placeholders


def insert_images():
    """이미지 삽입"""
    print("=" * 60)
    print("Google Docs 이미지 삽입")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # 이미지 매핑
    image_mapping = {
        '[이미지: 콘텐츠 구성 차트]': 'cs-content-composition.png',
        '[이미지: 콘텐츠 상세 차트]': 'cs-content-detail.png',
        '[이미지: YouTube vs WSOPTV 비교]': 'cs-youtube-vs-wsoptv.png',
        '[이미지: 시즌 캘린더]': 'cs-season-calendar.png',
        '[이미지: 로드맵]': 'cs-curation-roadmap.png',
    }

    # 플레이스홀더 찾기
    placeholders = find_placeholder_positions(docs_service, DOC_ID)
    print(f"\n플레이스홀더 발견: {len(placeholders)}개")

    for p in placeholders:
        print(f"  - {p['text']} (index: {p['start']}-{p['end']})")

    if not placeholders:
        print("플레이스홀더가 없습니다.")
        return

    # 이미지 URL 준비
    print("\n이미지 URL 준비 중...")
    image_urls = {}
    for placeholder_text, filename in image_mapping.items():
        file_path = os.path.join(IMAGE_DIR, filename)
        if os.path.exists(file_path):
            url = get_public_image_url(drive_service, file_path, FOLDER_ID)
            image_urls[placeholder_text] = url
        else:
            print(f"  파일 없음: {file_path}")

    # 역순으로 이미지 삽입 (인덱스 꼬임 방지)
    placeholders.sort(key=lambda x: x['start'], reverse=True)

    print("\n이미지 삽입 중...")
    for p in placeholders:
        if p['text'] not in image_urls:
            continue

        url = image_urls[p['text']]

        try:
            # 1. 플레이스홀더 텍스트 삭제
            docs_service.documents().batchUpdate(
                documentId=DOC_ID,
                body={'requests': [{
                    'deleteContentRange': {
                        'range': {
                            'startIndex': p['start'],
                            'endIndex': p['end'] - 1
                        }
                    }
                }]}
            ).execute()

            # 2. 이미지 삽입
            docs_service.documents().batchUpdate(
                documentId=DOC_ID,
                body={'requests': [{
                    'insertInlineImage': {
                        'location': {'index': p['start']},
                        'uri': url,
                        'objectSize': {
                            'width': {'magnitude': 468, 'unit': 'PT'},  # 6.5 인치
                            'height': {'magnitude': 280, 'unit': 'PT'}  # 비율 유지
                        }
                    }
                }]}
            ).execute()

            print(f"  성공: {p['text']}")

        except Exception as e:
            print(f"  실패: {p['text']} - {e}")

    print(f"\n완료! 문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")


if __name__ == "__main__":
    insert_images()
