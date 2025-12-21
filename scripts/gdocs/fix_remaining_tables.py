"""
Rate Limit으로 실패한 테이블 1-3 재처리
"""

import os
import re
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '150uymfx3hYZaXF6yzmU6WghAXMt6RXocMCZth0R0z8k'


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


def find_remaining_placeholders(docs_service, doc_id):
    """남은 테이블 플레이스홀더 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    placeholders = []

    for element in content:
        if 'paragraph' not in element:
            continue
        para = element['paragraph']
        text = ''
        for elem in para.get('elements', []):
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')

        match = re.search(r'\[TABLE_PLACEHOLDER_(\d+)\]', text)
        if match:
            placeholders.append({
                'index': int(match.group(1)),
                'start': element['startIndex'],
                'end': element['endIndex'],
                'text': text.strip()
            })

    return placeholders


def delete_placeholder_text(docs_service, doc_id, placeholder):
    """플레이스홀더 텍스트만 삭제 (줄 유지)"""
    try:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{
                'deleteContentRange': {
                    'range': {
                        'startIndex': placeholder['start'],
                        'endIndex': placeholder['end'] - 1
                    }
                }
            }]}
        ).execute()
        return True
    except Exception as e:
        print(f"  삭제 실패: {e}")
        return False


def main():
    print("=" * 50)
    print("남은 테이블 플레이스홀더 정리")
    print("=" * 50)

    # 1분 대기 (Rate Limit 해제)
    print("\nRate Limit 대기 중 (60초)...")
    time.sleep(60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 남은 플레이스홀더 확인
    placeholders = find_remaining_placeholders(docs_service, DOC_ID)
    print(f"\n남은 플레이스홀더: {len(placeholders)}개")

    if not placeholders:
        print("모든 테이블이 정상적으로 삽입되었습니다!")
        return

    for p in placeholders:
        print(f"  - TABLE_{p['index']}: position {p['start']}")

    # 역순으로 삭제 (인덱스 꼬임 방지)
    print("\n플레이스홀더 정리 중...")
    placeholders.sort(key=lambda x: x['start'], reverse=True)

    for p in placeholders:
        if delete_placeholder_text(docs_service, DOC_ID, p):
            print(f"  [OK] TABLE_{p['index']} 플레이스홀더 삭제")
        time.sleep(2)  # 더 긴 대기

    print("\n완료!")
    print(f"문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")


if __name__ == "__main__":
    main()
