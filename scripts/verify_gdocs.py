"""
Google Docs 최종 상태 확인
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


def verify():
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    doc = docs_service.documents().get(documentId=DOC_ID).execute()

    print("=" * 60)
    print(f"Document: {doc.get('title')}")
    print("=" * 60)

    # 인라인 이미지 수
    inline_objects = doc.get('inlineObjects', {})
    print(f"\nInline Images: {len(inline_objects)}")

    if inline_objects:
        for i, (obj_id, obj) in enumerate(inline_objects.items(), 1):
            props = obj.get('inlineObjectProperties', {})
            embedded = props.get('embeddedObject', {})
            size = embedded.get('size', {})
            width = size.get('width', {}).get('magnitude', 0)
            height = size.get('height', {}).get('magnitude', 0)
            print(f"  {i}. {width:.0f} x {height:.0f} pt")

    # 플레이스홀더 확인
    content = doc.get('body', {}).get('content', [])
    remaining_placeholders = []

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
        if text.startswith('[') and ':' in text and text.endswith(']'):
            remaining_placeholders.append(text)

    print(f"\nRemaining Placeholders: {len(remaining_placeholders)}")
    for p in remaining_placeholders:
        print(f"  - {p}")

    # 문서 통계
    body_content = doc.get('body', {}).get('content', [])
    total_paragraphs = sum(1 for e in body_content if 'paragraph' in e)
    total_tables = sum(1 for e in body_content if 'table' in e)

    print(f"\nDocument Stats:")
    print(f"  Paragraphs: {total_paragraphs}")
    print(f"  Tables: {total_tables}")
    print(f"  Images: {len(inline_objects)}")

    print(f"\nURL: https://docs.google.com/document/d/{DOC_ID}/edit")


if __name__ == "__main__":
    verify()
