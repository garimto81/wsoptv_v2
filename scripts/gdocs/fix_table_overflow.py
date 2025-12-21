"""
테이블 오버플로우 수정
- 4열 이상 테이블 → 3열로 축소 (재생성)
- 셀 내용 길이 제한
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


def analyze_tables(docs_service, doc_id):
    """테이블 분석 - 4열 이상 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    tables = []
    for element in content:
        if 'table' not in element:
            continue

        table = element['table']
        rows = table.get('tableRows', [])
        if not rows:
            continue

        num_cols = len(rows[0].get('tableCells', []))
        num_rows = len(rows)

        # 셀 내용 추출
        table_data = []
        for row in rows:
            row_data = []
            for cell in row.get('tableCells', []):
                cell_text = ''
                for content_elem in cell.get('content', []):
                    if 'paragraph' in content_elem:
                        for para_elem in content_elem['paragraph'].get('elements', []):
                            if 'textRun' in para_elem:
                                cell_text += para_elem['textRun'].get('content', '').strip()
                row_data.append(cell_text)
            table_data.append(row_data)

        tables.append({
            'start': element['startIndex'],
            'end': element['endIndex'],
            'rows': num_rows,
            'cols': num_cols,
            'data': table_data,
            'overflow': num_cols > 3
        })

    return tables


def recreate_table(docs_service, doc_id, table_info):
    """테이블 재생성 (3열 이하로)"""
    data = table_info['data']
    start = table_info['start']
    end = table_info['end']

    # 3열로 축소
    new_data = []
    for row in data:
        new_row = row[:3]  # 처음 3열만
        # 셀 내용 길이 제한 (25자)
        new_row = [cell[:25] if len(cell) > 25 else cell for cell in new_row]
        new_data.append(new_row)

    num_rows = len(new_data)
    num_cols = min(3, len(new_data[0]) if new_data else 0)

    if num_cols == 0:
        return False

    try:
        # 기존 테이블 삭제
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{
                'deleteContentRange': {
                    'range': {'startIndex': start, 'endIndex': end}
                }
            }]}
        ).execute()

        time.sleep(1)

        # 새 테이블 삽입
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{
                'insertTable': {
                    'rows': num_rows,
                    'columns': num_cols,
                    'location': {'index': start}
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
            if abs(element['startIndex'] - start) < 20:
                table = element['table']
                cell_requests = []

                for row_idx, row in enumerate(table.get('tableRows', [])):
                    if row_idx >= len(new_data):
                        break
                    for col_idx, cell in enumerate(row.get('tableCells', [])):
                        if col_idx >= len(new_data[row_idx]):
                            break
                        cell_content = cell.get('content', [])
                        if cell_content:
                            cell_start = cell_content[0].get('startIndex', 0)
                            cell_text = new_data[row_idx][col_idx]
                            if cell_text:
                                cell_requests.append({
                                    'insertText': {
                                        'location': {'index': cell_start},
                                        'text': cell_text
                                    }
                                })
                                # 헤더 볼드
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

    except Exception as e:
        print(f"    오류: {str(e)[:50]}")
        return False


def main():
    print("=" * 60)
    print("테이블 오버플로우 수정")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 테이블 분석
    print("\n[1/2] 테이블 분석...")
    tables = analyze_tables(docs_service, DOC_ID)

    overflow_tables = [t for t in tables if t['overflow']]
    print(f"  총 테이블: {len(tables)}개")
    print(f"  오버플로우 (4열+): {len(overflow_tables)}개")

    for t in overflow_tables:
        print(f"    - {t['rows']}x{t['cols']} (위치: {t['start']})")

    if not overflow_tables:
        print("  수정할 테이블이 없습니다!")
        return

    # 오버플로우 테이블 수정 (역순)
    print(f"\n[2/2] 테이블 수정 ({len(overflow_tables)}개)...")

    overflow_tables.sort(key=lambda x: x['start'], reverse=True)

    for i, table in enumerate(overflow_tables):
        print(f"  [{i+1}/{len(overflow_tables)}] {table['rows']}x{table['cols']} -> {table['rows']}x3...")

        if recreate_table(docs_service, DOC_ID, table):
            print(f"    OK")
        else:
            print(f"    FAIL")

        time.sleep(2)

    print("\n" + "=" * 60)
    print(f"문서: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
