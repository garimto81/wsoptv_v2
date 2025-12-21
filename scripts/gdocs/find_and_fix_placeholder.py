"""
[TBL_0] 플레이스홀더 찾아서 수정
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
MD_FILE = r'D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\03-content-strategy.md'


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


def find_placeholder(docs_service, doc_id):
    """TBL_0 플레이스홀더 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'paragraph' not in element:
            continue
        para_text = ''
        for elem in element['paragraph'].get('elements', []):
            if 'textRun' in elem:
                para_text += elem['textRun'].get('content', '')

        if '[TBL_0]' in para_text or '[TBL_' in para_text:
            print(f"  발견: '{para_text.strip()}'")
            print(f"  위치: {element['startIndex']} - {element['endIndex']}")
            return {
                'start': element['startIndex'],
                'end': element['endIndex'],
                'text': para_text.strip()
            }

    return None


def get_first_table_from_md():
    """마크다운에서 첫 번째 테이블 가져오기"""
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()

    lines = md_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1

            rows = []
            for tl in table_lines:
                tl = tl.strip()
                if re.match(r'^\|[\s\-:|]+\|$', tl):
                    continue
                cells = [re.sub(r'\*\*([^*]+)\*\*', r'\1', c.strip()) for c in tl.strip('|').split('|')]
                if len(cells) > 3:
                    cells = cells[:3]
                if any(c for c in cells):
                    rows.append(cells)

            if rows:
                return rows

        i += 1

    return None


def insert_table(docs_service, doc_id, position, data):
    """테이블 삽입"""
    num_rows = len(data)
    num_cols = min(len(data[0]), 3) if data else 0

    # 테이블 삽입
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{
            'insertTable': {
                'rows': num_rows,
                'columns': num_cols,
                'location': {'index': position}
            }
        }]}
    ).execute()

    time.sleep(1)

    # 셀 내용 삽입
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'table' not in element:
            continue
        if abs(element['startIndex'] - position) < 20:
            table = element['table']
            cell_requests = []

            for row_idx, row in enumerate(table.get('tableRows', [])):
                if row_idx >= len(data):
                    break
                for col_idx, cell in enumerate(row.get('tableCells', [])):
                    if col_idx >= len(data[row_idx]):
                        break
                    cell_content = cell.get('content', [])
                    if cell_content:
                        cell_start = cell_content[0].get('startIndex', 0)
                        cell_text = data[row_idx][col_idx][:25]
                        if cell_text:
                            cell_requests.append({
                                'insertText': {
                                    'location': {'index': cell_start},
                                    'text': cell_text
                                }
                            })
                            if row_idx == 0:
                                cell_requests.append({
                                    'updateTextStyle': {
                                        'range': {'startIndex': cell_start, 'endIndex': cell_start + len(cell_text)},
                                        'textStyle': {'bold': True},
                                        'fields': 'bold'
                                    }
                                })

            if cell_requests:
                cell_requests.reverse()
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': cell_requests}
                ).execute()

            return True

    return False


def main():
    print("=" * 50)
    print("[TBL_0] 플레이스홀더 수정")
    print("=" * 50)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 플레이스홀더 찾기
    print("\n[1/3] 플레이스홀더 검색...")
    placeholder = find_placeholder(docs_service, DOC_ID)

    if not placeholder:
        print("  플레이스홀더 없음!")
        return

    # 마크다운에서 첫 번째 테이블 가져오기
    print("\n[2/3] 테이블 데이터 로드...")
    table_data = get_first_table_from_md()
    if table_data:
        print(f"  테이블: {len(table_data)}x{len(table_data[0])}")
        for row in table_data[:3]:
            print(f"    {row}")
    else:
        print("  테이블 데이터 없음!")
        return

    # 플레이스홀더 삭제 및 테이블 삽입
    print("\n[3/3] 테이블 삽입...")

    # 삭제
    try:
        docs_service.documents().batchUpdate(
            documentId=DOC_ID,
            body={'requests': [{
                'deleteContentRange': {
                    'range': {'startIndex': placeholder['start'], 'endIndex': placeholder['end'] - 1}
                }
            }]}
        ).execute()
        print("  플레이스홀더 삭제 완료")
    except Exception as e:
        print(f"  삭제 실패: {e}")
        return

    time.sleep(1)

    # 삽입
    if insert_table(docs_service, DOC_ID, placeholder['start'], table_data):
        print("  테이블 삽입 완료!")
    else:
        print("  테이블 삽입 실패")

    print(f"\n문서: https://docs.google.com/document/d/{DOC_ID}/edit")


if __name__ == "__main__":
    main()
