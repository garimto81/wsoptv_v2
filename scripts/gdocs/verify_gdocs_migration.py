"""
Google Docs 마이그레이션 검증 스크립트
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
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


def analyze_document(docs_service, doc_id):
    """문서 구조 분석"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    stats = {
        'title': doc.get('title', 'N/A'),
        'total_elements': len(content),
        'paragraphs': 0,
        'tables': 0,
        'images': 0,
        'headings': {'HEADING_1': 0, 'HEADING_2': 0, 'HEADING_3': 0, 'HEADING_4': 0},
        'total_chars': 0,
        'placeholders': []
    }

    for element in content:
        if 'paragraph' in element:
            stats['paragraphs'] += 1
            para = element['paragraph']

            # 헤딩 카운트
            style = para.get('paragraphStyle', {}).get('namedStyleType', '')
            if style in stats['headings']:
                stats['headings'][style] += 1

            # 텍스트 길이 계산
            for elem in para.get('elements', []):
                if 'textRun' in elem:
                    text = elem['textRun'].get('content', '')
                    stats['total_chars'] += len(text)

                    # 플레이스홀더 체크
                    if '[TABLE_PLACEHOLDER' in text or '[IMAGE_PLACEHOLDER' in text:
                        stats['placeholders'].append(text.strip())

                # 인라인 이미지 카운트
                if 'inlineObjectElement' in elem:
                    stats['images'] += 1

        elif 'table' in element:
            stats['tables'] += 1

    return stats


def main():
    print("=" * 60)
    print("Google Docs 마이그레이션 검증")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    stats = analyze_document(docs_service, DOC_ID)

    print(f"\n[Document Info]")
    print(f"  Title: {stats['title']}")
    print(f"  URL: https://docs.google.com/document/d/{DOC_ID}/edit")

    print(f"\n[Content Stats]")
    print(f"  Total Elements: {stats['total_elements']}")
    print(f"  Paragraphs: {stats['paragraphs']}")
    print(f"  Tables: {stats['tables']}")
    print(f"  Images: {stats['images']}")
    print(f"  Total Characters: {stats['total_chars']:,}")

    print(f"\n[Headings]")
    for h, count in stats['headings'].items():
        print(f"  {h}: {count}")

    if stats['placeholders']:
        print(f"\n[WARNING] Remaining Placeholders: {len(stats['placeholders'])}")
        for p in stats['placeholders'][:5]:
            print(f"  - {p}")
    else:
        print(f"\n[OK] No remaining placeholders!")

    # 검증 요약
    print("\n" + "=" * 60)
    print("[Verification Summary]")

    issues = []
    if stats['tables'] < 28:
        issues.append(f"Tables: {stats['tables']}/28 (some missing)")
    if stats['images'] < 9:
        issues.append(f"Images: {stats['images']}/9 (some missing)")
    if stats['placeholders']:
        issues.append(f"Placeholders remaining: {len(stats['placeholders'])}")

    if not issues:
        print("  [PASS] All checks passed!")
        print(f"    - Tables: {stats['tables']} (target: 28+)")
        print(f"    - Images: {stats['images']} (target: 9)")
        print(f"    - No placeholders remaining")
    else:
        print("  [ISSUES]")
        for issue in issues:
            print(f"    - {issue}")

    print("=" * 60)


if __name__ == "__main__":
    main()
