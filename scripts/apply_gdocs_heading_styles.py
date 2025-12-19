"""
Google Docs 문서에 헤딩 스타일 적용
"""

import os
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# OAuth 설정
SCOPES = ['https://www.googleapis.com/auth/documents']

CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'

# 문서 ID
DOC_ID = '1431Dz71jRV78o6-bwgR6sVM573bnGKf9-9Ozyo6hKpg'


def get_credentials():
    """OAuth 2.0 인증 처리"""
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


def find_headings_in_doc(doc):
    """문서에서 헤딩 패턴 찾기"""
    headings = []
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'paragraph' not in element:
            continue

        paragraph = element['paragraph']
        elements = paragraph.get('elements', [])

        if not elements:
            continue

        # 텍스트 추출
        text = ''
        for elem in elements:
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')

        text = text.strip()
        if not text:
            continue

        start_index = element['startIndex']
        end_index = element['endIndex']

        # 헤딩 패턴 매칭
        # TITLE: "WSOPTV 콘텐츠 전략"
        if text == 'WSOPTV 콘텐츠 전략':
            headings.append({
                'text': text,
                'start': start_index,
                'end': end_index,
                'style': 'TITLE'
            })

        # HEADING_1: 주요 섹션 (숫자로 시작하는 대제목, Executive Summary 등)
        elif text == 'Executive Summary':
            headings.append({
                'text': text,
                'start': start_index,
                'end': end_index,
                'style': 'HEADING_1'
            })
        elif re.match(r'^[1-6]\.\s+[가-힣\w]', text) and not re.match(r'^[1-6]\.[1-9]', text):
            headings.append({
                'text': text,
                'start': start_index,
                'end': end_index,
                'style': 'HEADING_1'
            })

        # HEADING_2: 하위 섹션 (1.1, 2.1 등으로 시작)
        elif re.match(r'^[1-6]\.[1-9]\s+', text):
            headings.append({
                'text': text,
                'start': start_index,
                'end': end_index,
                'style': 'HEADING_2'
            })

        # HEADING_3: 소제목 (핵심 지표, Main Event 등)
        elif text in ['핵심 지표', '역대 브레이슬릿 레전드', 'Moneymaker의 여정', '포커 붐 촉발 효과',
                      '전체 콘텐츠 구성', 'Main Event (35%)', 'Bracelet Events (30%)',
                      'Best Hands 큐레이션 (15%)', '콘텐츠 전환 흐름', '기능 1: Hand Skip (시간 효율화)',
                      '기능 2: Best Hands 컬렉션 (큐레이션)', '기능 3: 4K Remaster (아카이브 복원)']:
            headings.append({
                'text': text,
                'start': start_index,
                'end': end_index,
                'style': 'HEADING_3'
            })

        # SUBTITLE: 슬로건
        elif text == '포커의 50년 역사, 하나의 플랫폼':
            headings.append({
                'text': text,
                'start': start_index,
                'end': end_index,
                'style': 'SUBTITLE'
            })

    return headings


def apply_heading_styles():
    """헤딩 스타일 적용"""
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 문서 가져오기
    doc = docs_service.documents().get(documentId=DOC_ID).execute()
    print(f"문서 로드 완료: {doc.get('title')}")

    # 헤딩 찾기
    headings = find_headings_in_doc(doc)
    print(f"\n발견된 헤딩: {len(headings)}개")

    for h in headings:
        print(f"  [{h['style']}] {h['text'][:50]}...")

    if not headings:
        print("적용할 헤딩이 없습니다.")
        return

    # 스타일 적용 요청 생성
    requests = []
    for heading in headings:
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': heading['start'],
                    'endIndex': heading['end']
                },
                'paragraphStyle': {
                    'namedStyleType': heading['style']
                },
                'fields': 'namedStyleType'
            }
        })

    # 배치 업데이트 실행
    if requests:
        result = docs_service.documents().batchUpdate(
            documentId=DOC_ID,
            body={'requests': requests}
        ).execute()
        print(f"\n스타일 적용 완료: {len(requests)}개 헤딩")

    print(f"\n문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")


if __name__ == "__main__":
    apply_heading_styles()
