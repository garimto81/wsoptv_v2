"""
Google Docs 서식 이슈 자동 수정
1. 마크다운 볼드(**text**) 제거 및 실제 볼드 적용
2. 이미지 크기 통일 (400pt)
"""

import os
import re
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents']
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


def find_markdown_bold_patterns(docs_service, doc_id):
    """마크다운 볼드 패턴(**text**) 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    patterns = []

    for element in content:
        if 'paragraph' not in element:
            continue

        para = element['paragraph']
        for elem in para.get('elements', []):
            if 'textRun' not in elem:
                continue

            text = elem['textRun'].get('content', '')
            start_index = elem.get('startIndex', 0)

            # **text** 패턴 찾기
            for match in re.finditer(r'\*\*([^*]+)\*\*', text):
                patterns.append({
                    'start': start_index + match.start(),
                    'end': start_index + match.end(),
                    'full_match': match.group(0),
                    'inner_text': match.group(1)
                })

    return patterns


def fix_markdown_bold(docs_service, doc_id, patterns):
    """마크다운 볼드를 실제 볼드로 변환"""
    if not patterns:
        return 0

    # 역순으로 처리 (인덱스 꼬임 방지)
    patterns.sort(key=lambda x: x['start'], reverse=True)

    fixed = 0
    for p in patterns:
        try:
            # 1. **text** 삭제
            # 2. text 삽입
            # 3. 볼드 스타일 적용

            requests = [
                # **text** 삭제
                {
                    'deleteContentRange': {
                        'range': {
                            'startIndex': p['start'],
                            'endIndex': p['end']
                        }
                    }
                },
                # text 삽입
                {
                    'insertText': {
                        'location': {'index': p['start']},
                        'text': p['inner_text']
                    }
                },
                # 볼드 적용
                {
                    'updateTextStyle': {
                        'range': {
                            'startIndex': p['start'],
                            'endIndex': p['start'] + len(p['inner_text'])
                        },
                        'textStyle': {'bold': True},
                        'fields': 'bold'
                    }
                }
            ]

            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()

            fixed += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"  볼드 변환 실패: {p['inner_text'][:20]}... - {e}")

    return fixed


def resize_small_images(docs_service, doc_id, target_width=400):
    """작은 이미지 크기 조정"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    inline_objects = doc.get('inlineObjects', {})

    resized = 0
    requests = []

    for element in content:
        if 'paragraph' not in element:
            continue

        para = element['paragraph']
        for elem in para.get('elements', []):
            if 'inlineObjectElement' not in elem:
                continue

            obj_id = elem['inlineObjectElement'].get('inlineObjectId', '')
            if obj_id not in inline_objects:
                continue

            obj = inline_objects[obj_id]
            props = obj.get('inlineObjectProperties', {}).get('embeddedObject', {})
            size = props.get('size', {})
            width = size.get('width', {}).get('magnitude', 0)
            height = size.get('height', {}).get('magnitude', 0)

            # 작은 이미지만 조정 (300pt 미만)
            if width < 300 and width > 0:
                # 비율 유지하면서 확대
                ratio = height / width if width > 0 else 1
                new_width = target_width
                new_height = new_width * ratio

                requests.append({
                    'updateInlineObjectProperties': {
                        'objectId': obj_id,
                        'inlineObjectProperties': {
                            'embeddedObject': {
                                'size': {
                                    'width': {'magnitude': new_width, 'unit': 'PT'},
                                    'height': {'magnitude': new_height, 'unit': 'PT'}
                                }
                            }
                        },
                        'fields': 'embeddedObject.size'
                    }
                })
                resized += 1

    if requests:
        try:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
        except Exception as e:
            print(f"  이미지 크기 조정 실패: {e}")
            return 0

    return resized


def main():
    print("=" * 60)
    print("Google Docs 서식 이슈 자동 수정")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 1. 마크다운 볼드 수정
    print("\n[1/2] 마크다운 볼드 패턴 검색...")
    patterns = find_markdown_bold_patterns(docs_service, DOC_ID)
    print(f"  발견: {len(patterns)}개")

    if patterns:
        print("  수정 중...")
        fixed = fix_markdown_bold(docs_service, DOC_ID, patterns)
        print(f"  완료: {fixed}개 변환")
    else:
        print("  수정 불필요")

    time.sleep(2)

    # 2. 이미지 크기 조정
    print("\n[2/2] 작은 이미지 크기 조정...")
    resized = resize_small_images(docs_service, DOC_ID)
    print(f"  조정: {resized}개 이미지")

    # 완료
    print("\n" + "=" * 60)
    print("자동 수정 완료!")
    print()
    print("[수동 조정 권장 사항]")
    print("  1. 테이블 첫 행: 배경색 추가 (회색 계열)")
    print("  2. 테이블 첫 행: 볼드 적용")
    print("  3. 연속 빈 줄: 1줄로 축소")
    print("  4. 인용문 블록: 들여쓰기 또는 배경색")
    print()
    print(f"문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
