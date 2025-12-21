"""
누락된 테이블 플레이스홀더 찾아서 테이블로 교체
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


def find_table_placeholders(docs_service, doc_id):
    """테이블 플레이스홀더 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    placeholders = []

    for element in content:
        if 'paragraph' not in element:
            continue
        para_text = ''
        for elem in element['paragraph'].get('elements', []):
            if 'textRun' in elem:
                para_text += elem['textRun'].get('content', '')

        if '[TBL:' in para_text:
            match = re.search(r'\[TBL:(\d+)x(\d+)\]', para_text)
            if match:
                placeholders.append({
                    'start': element['startIndex'],
                    'end': element['endIndex'],
                    'rows': int(match.group(1)),
                    'cols': int(match.group(2)),
                    'text': para_text.strip()
                })

    return placeholders


def get_tables_from_markdown():
    """마크다운에서 테이블 데이터 추출"""
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()

    lines = md_content.split('\n')
    tables = []
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
                tables.append(rows)
            continue

        i += 1

    return tables


def insert_table_at_position(docs_service, doc_id, position, data):
    """테이블 삽입"""
    num_rows = len(data)
    num_cols = min(len(data[0]), 3) if data else 0

    if num_cols == 0:
        return False

    try:
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
            if abs(element['startIndex'] - position) < 10:
                table = element['table']
                cell_requests = []

                for row_idx, row in enumerate(table.get('tableRows', [])):
                    if row_idx >= len(data):
                        break
                    for col_idx, cell in enumerate(row.get('tableCells', [])):
                        if col_idx >= min(len(data[row_idx]), 3):
                            break
                        cell_content = cell.get('content', [])
                        if cell_content:
                            cell_start = cell_content[0].get('startIndex', 0)
                            cell_text = data[row_idx][col_idx][:30]
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
                                            'textStyle': {'bold': True, 'fontSize': {'magnitude': 9, 'unit': 'PT'}},
                                            'fields': 'bold,fontSize'
                                        }
                                    })
                                else:
                                    cell_requests.append({
                                        'updateTextStyle': {
                                            'range': {'startIndex': cell_start, 'endIndex': cell_start + len(cell_text)},
                                            'textStyle': {'fontSize': {'magnitude': 9, 'unit': 'PT'}},
                                            'fields': 'fontSize'
                                        }
                                    })

                if cell_requests:
                    cell_requests.reverse()
                    docs_service.documents().batchUpdate(
                        documentId=doc_id,
                        body={'requests': cell_requests}
                    ).execute()

                return True

        return True

    except Exception as e:
        print(f"    오류: {str(e)[:40]}")
        return False


def main():
    print("=" * 60)
    print("누락된 테이블 삽입")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 플레이스홀더 찾기
    print("\n[1/3] 플레이스홀더 검색...")
    placeholders = find_table_placeholders(docs_service, DOC_ID)
    print(f"  발견: {len(placeholders)}개")

    if not placeholders:
        print("  모든 테이블이 삽입되었습니다!")
        return

    for p in placeholders[:5]:
        print(f"    - {p['text']}")

    # 마크다운에서 테이블 추출
    print("\n[2/3] 마크다운 테이블 추출...")
    md_tables = get_tables_from_markdown()
    print(f"  총 {len(md_tables)}개 테이블")

    # 플레이스홀더를 테이블로 교체 (역순)
    print(f"\n[3/3] 테이블 삽입 ({len(placeholders)}개)...")

    placeholders.sort(key=lambda x: x['start'], reverse=True)
    table_idx = len(md_tables) - 1

    for i, ph in enumerate(placeholders):
        if table_idx < 0:
            break

        # 크기가 맞는 테이블 찾기
        target_rows = ph['rows']
        target_cols = ph['cols']

        # 가장 가까운 크기의 테이블 사용
        best_match = None
        for j, tbl in enumerate(md_tables):
            if len(tbl) == target_rows and min(len(tbl[0]), 3) == min(target_cols, 3):
                best_match = tbl
                md_tables.pop(j)
                break

        if not best_match and md_tables:
            best_match = md_tables.pop()

        if not best_match:
            continue

        # 플레이스홀더 삭제
        try:
            docs_service.documents().batchUpdate(
                documentId=DOC_ID,
                body={'requests': [{
                    'deleteContentRange': {
                        'range': {'startIndex': ph['start'], 'endIndex': ph['end'] - 1}
                    }
                }]}
            ).execute()
        except Exception as e:
            print(f"    삭제 실패: {str(e)[:30]}")
            continue

        time.sleep(1)

        # 테이블 삽입
        if insert_table_at_position(docs_service, DOC_ID, ph['start'], best_match):
            print(f"  [{i+1}/{len(placeholders)}] OK ({len(best_match)}x{len(best_match[0])})")
        else:
            print(f"  [{i+1}/{len(placeholders)}] FAIL")

        time.sleep(2)  # Rate limit 방지

    # 남은 플레이스홀더 확인
    remaining = find_table_placeholders(docs_service, DOC_ID)
    print(f"\n남은 플레이스홀더: {len(remaining)}개")

    print("\n" + "=" * 60)
    print(f"문서: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
