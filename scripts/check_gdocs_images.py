"""
Google Docs 문서의 이미지 삽입 상태 확인
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '1431Dz71jRV78o6-bwgR6sVM573bnGKf9-9Ozyo6hKpg'


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


def check_images():
    """문서 내 이미지 확인"""
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    doc = docs_service.documents().get(documentId=DOC_ID).execute()

    print("=" * 60)
    print(f"문서 제목: {doc.get('title')}")
    print("=" * 60)

    # 인라인 이미지 찾기
    inline_objects = doc.get('inlineObjects', {})
    print(f"\n인라인 이미지 수: {len(inline_objects)}")

    if inline_objects:
        for obj_id, obj in inline_objects.items():
            props = obj.get('inlineObjectProperties', {})
            embedded = props.get('embeddedObject', {})

            title = embedded.get('title', '(제목 없음)')
            description = embedded.get('description', '(설명 없음)')

            size = embedded.get('size', {})
            width = size.get('width', {}).get('magnitude', 0)
            height = size.get('height', {}).get('magnitude', 0)

            image_props = embedded.get('imageProperties', {})
            content_uri = image_props.get('contentUri', '(URI 없음)')

            print(f"\n이미지 ID: {obj_id}")
            print(f"  제목: {title}")
            print(f"  크기: {width:.0f} x {height:.0f} pt")
            print(f"  URI: {content_uri[:80]}...")
    else:
        print("\n⚠️ 문서에 삽입된 이미지가 없습니다.")

    # 플레이스홀더 텍스트 확인
    print("\n" + "=" * 60)
    print("플레이스홀더 텍스트 확인")
    print("=" * 60)

    content = doc.get('body', {}).get('content', [])
    placeholders_found = []

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
        if text.startswith('[이미지:'):
            placeholders_found.append(text)

    if placeholders_found:
        print(f"\n⚠️ 아직 교체되지 않은 플레이스홀더: {len(placeholders_found)}개")
        for p in placeholders_found:
            print(f"  - {p}")
    else:
        print("\n✓ 모든 플레이스홀더가 교체되었습니다.")

    print(f"\n문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")


if __name__ == "__main__":
    check_images()
