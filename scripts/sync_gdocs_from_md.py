"""
원본 마크다운 파일을 읽어서 Google Docs에 동기화
마크다운 구문을 Google Docs용 텍스트로 변환
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

# 원본 마크다운 파일 경로
MD_FILE = r'D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\03-content-strategy-gdocs.md'


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


def convert_md_to_plain_text(md_content: str) -> str:
    """마크다운을 Google Docs용 플레인 텍스트로 변환"""

    # 마크다운 헤딩을 일반 텍스트로 변환
    # # -> 제목, ## -> 섹션, ### -> 소제목, #### -> 하위제목
    lines = md_content.split('\n')
    converted_lines = []

    for line in lines:
        # 마크다운 헤딩 제거 (# 기호)
        if line.startswith('####'):
            converted_lines.append(line[5:].strip())
        elif line.startswith('###'):
            converted_lines.append(line[4:].strip())
        elif line.startswith('##'):
            converted_lines.append(line[3:].strip())
        elif line.startswith('#'):
            converted_lines.append(line[2:].strip())

        # 볼드 마크다운 (**text**) 제거 -> text
        elif '**' in line:
            converted_lines.append(re.sub(r'\*\*([^*]+)\*\*', r'\1', line))

        # 인용문 (>) 제거
        elif line.startswith('>'):
            converted_lines.append(line[1:].strip())

        # 수평선 (---) 제거
        elif line.strip() == '---':
            continue

        # HTML 태그 제거
        elif '<div' in line or '</div>' in line:
            continue

        # 마크다운 링크 변환 [text](url) -> text (url)
        elif '[' in line and '](' in line:
            converted_lines.append(re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', line))

        # 이미지 삽입 위치 주석 유지
        elif line.startswith('[그래프') or line.startswith('[이미지'):
            converted_lines.append(line)

        else:
            converted_lines.append(line)

    return '\n'.join(converted_lines)


def sync_to_gdocs():
    """마크다운 파일을 Google Docs로 동기화"""

    # 마크다운 파일 읽기
    print(f"마크다운 파일 읽기: {MD_FILE}")
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()

    print(f"원본 파일 길이: {len(md_content)} 문자, {len(md_content.splitlines())} 줄")

    # 마크다운 -> 플레인 텍스트 변환
    plain_text = convert_md_to_plain_text(md_content)
    print(f"변환된 텍스트 길이: {len(plain_text)} 문자")

    # Google Docs 연결
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 기존 문서 내용 가져오기
    doc = docs_service.documents().get(documentId=DOC_ID).execute()
    print(f"문서 로드 완료: {doc.get('title')}")

    # 기존 내용 삭제
    content = doc.get('body', {}).get('content', [])
    if content:
        end_index = content[-1].get('endIndex', 1) - 1
        if end_index > 1:
            requests = [{
                'deleteContentRange': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': end_index
                    }
                }
            }]
            docs_service.documents().batchUpdate(
                documentId=DOC_ID,
                body={'requests': requests}
            ).execute()
            print("기존 내용 삭제 완료")

    # 새 내용 삽입
    requests = [{
        'insertText': {
            'location': {'index': 1},
            'text': plain_text
        }
    }]

    docs_service.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': requests}
    ).execute()

    print("콘텐츠 삽입 완료!")
    print(f"\n문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")

    return DOC_ID


if __name__ == "__main__":
    sync_to_gdocs()
