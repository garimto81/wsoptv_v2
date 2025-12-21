"""
Google Docs 배치 생성 스크립트
- 모든 요청을 배치로 묶어 Rate Limit 회피
- A4 용지 + 완전 자동 서식
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
MD_FILE = r'D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\03-content-strategy.md'

# A4 설정
A4_WIDTH = 595.276
A4_HEIGHT = 841.890
MARGIN = 72
IMAGE_WIDTH = 481


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


def parse_markdown(md_content):
    """마크다운 파싱 - 테이블과 이미지 위치 기록"""
    lines = md_content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped == '---':
            i += 1
            continue

        # 이미지
        if '<img' in stripped:
            match = re.search(r'src="([^"]+)"', stripped)
            if match:
                result.append({'type': 'image', 'url': match.group(1)})
            i += 1
            continue

        # 헤딩
        if stripped.startswith('####'):
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', stripped[4:].strip())
            result.append({'type': 'h4', 'text': text})
        elif stripped.startswith('###'):
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', stripped[3:].strip())
            result.append({'type': 'h3', 'text': text})
        elif stripped.startswith('##'):
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', stripped[2:].strip())
            result.append({'type': 'h2', 'text': text})
        elif stripped.startswith('#'):
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', stripped[1:].strip())
            result.append({'type': 'h1', 'text': text})

        # 테이블
        elif stripped.startswith('|'):
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
                if any(c for c in cells):
                    rows.append(cells)
            if rows:
                result.append({'type': 'table', 'data': rows})
            continue

        # 인용문
        elif stripped.startswith('>'):
            text = stripped[1:].strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            result.append({'type': 'quote', 'text': text})

        # 코드 블록
        elif stripped.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i])
                i += 1
            result.append({'type': 'code', 'text': '\n'.join(code)})
            i += 1
            continue

        # 리스트
        elif stripped.startswith('- '):
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', stripped[2:])
            result.append({'type': 'bullet', 'text': text})
        elif re.match(r'^\d+\.', stripped):
            text = re.sub(r'^\d+\.\s*', '', stripped)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            result.append({'type': 'number', 'text': text})

        # 일반 텍스트
        else:
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', stripped)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            if text:
                result.append({'type': 'para', 'text': text})

        i += 1

    return result


def build_text_and_styles(parsed):
    """텍스트와 스타일 정보 분리"""
    text_parts = []
    styles = []
    tables = []
    images = []

    current_pos = 1  # Google Docs는 1부터 시작

    for item in parsed:
        item_type = item['type']

        if item_type == 'image':
            # 이미지 플레이스홀더
            placeholder = f"[IMG_{len(images)}]\n"
            images.append({'pos': current_pos, 'url': item['url']})
            text_parts.append(placeholder)
            current_pos += len(placeholder)

        elif item_type == 'table':
            # 테이블 플레이스홀더
            placeholder = f"[TBL_{len(tables)}]\n"
            tables.append({'pos': current_pos, 'data': item['data']})
            text_parts.append(placeholder)
            current_pos += len(placeholder)

        elif item_type in ['h1', 'h2', 'h3', 'h4']:
            text = item['text'] + '\n'
            style_map = {'h1': 'HEADING_1', 'h2': 'HEADING_2', 'h3': 'HEADING_3', 'h4': 'HEADING_4'}
            styles.append({
                'type': 'heading',
                'start': current_pos,
                'end': current_pos + len(text),
                'style': style_map[item_type]
            })
            text_parts.append(text)
            current_pos += len(text)

        elif item_type == 'quote':
            text = item['text'] + '\n'
            styles.append({
                'type': 'quote',
                'start': current_pos,
                'end': current_pos + len(text)
            })
            text_parts.append(text)
            current_pos += len(text)

        elif item_type == 'bullet':
            text = item['text'] + '\n'
            styles.append({
                'type': 'bullet',
                'start': current_pos,
                'end': current_pos + len(text)
            })
            text_parts.append(text)
            current_pos += len(text)

        elif item_type == 'number':
            text = item['text'] + '\n'
            styles.append({
                'type': 'number',
                'start': current_pos,
                'end': current_pos + len(text)
            })
            text_parts.append(text)
            current_pos += len(text)

        elif item_type == 'code':
            text = item['text'] + '\n'
            styles.append({
                'type': 'code',
                'start': current_pos,
                'end': current_pos + len(text)
            })
            text_parts.append(text)
            current_pos += len(text)

        else:  # para
            text = item['text'] + '\n'
            text_parts.append(text)
            current_pos += len(text)

        # 섹션 간 빈 줄
        text_parts.append('\n')
        current_pos += 1

    return ''.join(text_parts), styles, tables, images


def main():
    print("=" * 70)
    print("Google Docs 배치 생성 (Rate Limit 최적화)")
    print("=" * 70)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 1. 마크다운 파싱
    print("\n[1/5] 마크다운 파싱...")
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()
    parsed = parse_markdown(md_content)
    print(f"  요소: {len(parsed)}개")

    # 2. 텍스트와 스타일 분리
    print("\n[2/5] 텍스트/스타일 분리...")
    full_text, styles, tables, images = build_text_and_styles(parsed)
    print(f"  텍스트: {len(full_text):,}자")
    print(f"  스타일: {len(styles)}개")
    print(f"  테이블: {len(tables)}개")
    print(f"  이미지: {len(images)}개")

    # 3. 문서 초기화 + A4 설정 + 텍스트 삽입 (1 batch)
    print("\n[3/5] 문서 초기화 및 텍스트 삽입...")

    # 기존 내용 확인
    doc = docs_service.documents().get(documentId=DOC_ID).execute()
    content = doc.get('body', {}).get('content', [])
    end_index = content[-1].get('endIndex', 1) - 1 if content else 0

    requests = []

    # 기존 내용 삭제
    if end_index > 1:
        requests.append({
            'deleteContentRange': {
                'range': {'startIndex': 1, 'endIndex': end_index}
            }
        })

    # A4 페이지 설정
    requests.append({
        'updateDocumentStyle': {
            'documentStyle': {
                'pageSize': {
                    'width': {'magnitude': A4_WIDTH, 'unit': 'PT'},
                    'height': {'magnitude': A4_HEIGHT, 'unit': 'PT'}
                },
                'marginTop': {'magnitude': MARGIN, 'unit': 'PT'},
                'marginBottom': {'magnitude': MARGIN, 'unit': 'PT'},
                'marginLeft': {'magnitude': MARGIN, 'unit': 'PT'},
                'marginRight': {'magnitude': MARGIN, 'unit': 'PT'}
            },
            'fields': 'pageSize,marginTop,marginBottom,marginLeft,marginRight'
        }
    })

    # 텍스트 삽입
    requests.append({
        'insertText': {
            'location': {'index': 1},
            'text': full_text
        }
    })

    docs_service.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': requests}
    ).execute()
    print("  완료")

    time.sleep(2)

    # 4. 스타일 적용 (배치)
    print("\n[4/5] 스타일 적용...")

    # 헤딩 스타일
    heading_requests = []
    for s in styles:
        if s['type'] == 'heading':
            heading_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': s['start'], 'endIndex': s['end']},
                    'paragraphStyle': {'namedStyleType': s['style']},
                    'fields': 'namedStyleType'
                }
            })

    if heading_requests:
        # 배치 크기 제한 (50개씩)
        for i in range(0, len(heading_requests), 50):
            batch = heading_requests[i:i+50]
            try:
                docs_service.documents().batchUpdate(
                    documentId=DOC_ID,
                    body={'requests': batch}
                ).execute()
            except Exception as e:
                print(f"  헤딩 스타일 오류: {str(e)[:40]}")
            time.sleep(1)
        print(f"  헤딩 {len(heading_requests)}개 적용")

    # 인용문 스타일
    quote_requests = []
    for s in styles:
        if s['type'] == 'quote':
            quote_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': s['start'], 'endIndex': s['end']},
                    'paragraphStyle': {
                        'indentStart': {'magnitude': 36, 'unit': 'PT'},
                        'indentFirstLine': {'magnitude': 36, 'unit': 'PT'}
                    },
                    'fields': 'indentStart,indentFirstLine'
                }
            })
            quote_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': s['start'], 'endIndex': s['end'] - 1},
                    'textStyle': {'italic': True},
                    'fields': 'italic'
                }
            })

    if quote_requests:
        for i in range(0, len(quote_requests), 50):
            batch = quote_requests[i:i+50]
            try:
                docs_service.documents().batchUpdate(
                    documentId=DOC_ID,
                    body={'requests': batch}
                ).execute()
            except Exception as e:
                print(f"  인용문 스타일 오류: {str(e)[:40]}")
            time.sleep(1)
        print(f"  인용문 {len(quote_requests)//2}개 적용")

    # 불릿 리스트
    bullet_requests = []
    for s in styles:
        if s['type'] == 'bullet':
            bullet_requests.append({
                'createParagraphBullets': {
                    'range': {'startIndex': s['start'], 'endIndex': s['end']},
                    'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                }
            })

    if bullet_requests:
        for i in range(0, len(bullet_requests), 50):
            batch = bullet_requests[i:i+50]
            try:
                docs_service.documents().batchUpdate(
                    documentId=DOC_ID,
                    body={'requests': batch}
                ).execute()
            except Exception as e:
                print(f"  불릿 스타일 오류: {str(e)[:40]}")
            time.sleep(1)
        print(f"  불릿 {len(bullet_requests)}개 적용")

    # 번호 리스트
    number_requests = []
    for s in styles:
        if s['type'] == 'number':
            number_requests.append({
                'createParagraphBullets': {
                    'range': {'startIndex': s['start'], 'endIndex': s['end']},
                    'bulletPreset': 'NUMBERED_DECIMAL_NESTED'
                }
            })

    if number_requests:
        for i in range(0, len(number_requests), 50):
            batch = number_requests[i:i+50]
            try:
                docs_service.documents().batchUpdate(
                    documentId=DOC_ID,
                    body={'requests': batch}
                ).execute()
            except Exception as e:
                print(f"  번호 스타일 오류: {str(e)[:40]}")
            time.sleep(1)
        print(f"  번호 리스트 {len(number_requests)}개 적용")

    time.sleep(2)

    # 5. 이미지 및 테이블 삽입 (플레이스홀더 교체)
    print("\n[5/5] 이미지 및 테이블 삽입...")

    # 이미지 삽입 (역순)
    print(f"  이미지 {len(images)}개...")
    for idx in range(len(images) - 1, -1, -1):
        img = images[idx]
        placeholder = f"[IMG_{idx}]"

        # 플레이스홀더 위치 찾기
        doc = docs_service.documents().get(documentId=DOC_ID).execute()
        content = doc.get('body', {}).get('content', [])

        for element in content:
            if 'paragraph' not in element:
                continue
            para_text = ''
            for elem in element['paragraph'].get('elements', []):
                if 'textRun' in elem:
                    para_text += elem['textRun'].get('content', '')

            if placeholder in para_text:
                start = element['startIndex']
                end = element['endIndex']

                try:
                    # 플레이스홀더 삭제 + 이미지 삽입
                    docs_service.documents().batchUpdate(
                        documentId=DOC_ID,
                        body={'requests': [
                            {
                                'deleteContentRange': {
                                    'range': {'startIndex': start, 'endIndex': end - 1}
                                }
                            },
                            {
                                'insertInlineImage': {
                                    'location': {'index': start},
                                    'uri': img['url'],
                                    'objectSize': {
                                        'width': {'magnitude': IMAGE_WIDTH, 'unit': 'PT'},
                                        'height': {'magnitude': IMAGE_WIDTH * 0.625, 'unit': 'PT'}
                                    }
                                }
                            }
                        ]}
                    ).execute()
                except Exception as e:
                    print(f"    이미지 {idx} 실패: {str(e)[:30]}")
                break

        time.sleep(1)

    # 테이블 삽입 (역순)
    print(f"  테이블 {len(tables)}개...")
    for idx in range(len(tables) - 1, -1, -1):
        tbl = tables[idx]
        placeholder = f"[TBL_{idx}]"
        data = tbl['data']

        # 플레이스홀더 위치 찾기
        doc = docs_service.documents().get(documentId=DOC_ID).execute()
        content = doc.get('body', {}).get('content', [])

        for element in content:
            if 'paragraph' not in element:
                continue
            para_text = ''
            for elem in element['paragraph'].get('elements', []):
                if 'textRun' in elem:
                    para_text += elem['textRun'].get('content', '')

            if placeholder in para_text:
                start = element['startIndex']
                end = element['endIndex']
                num_rows = len(data)
                num_cols = max(len(row) for row in data) if data else 0

                try:
                    # 플레이스홀더 삭제
                    docs_service.documents().batchUpdate(
                        documentId=DOC_ID,
                        body={'requests': [{
                            'deleteContentRange': {
                                'range': {'startIndex': start, 'endIndex': end - 1}
                            }
                        }]}
                    ).execute()

                    time.sleep(0.5)

                    # 테이블 삽입
                    docs_service.documents().batchUpdate(
                        documentId=DOC_ID,
                        body={'requests': [{
                            'insertTable': {
                                'rows': num_rows,
                                'columns': num_cols,
                                'location': {'index': start}
                            }
                        }]}
                    ).execute()

                    time.sleep(0.5)

                    # 셀 내용 삽입
                    doc = docs_service.documents().get(documentId=DOC_ID).execute()
                    content2 = doc.get('body', {}).get('content', [])

                    for el in content2:
                        if 'table' not in el:
                            continue
                        if abs(el['startIndex'] - start) < 10:
                            table = el['table']
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
                                        cell_text = data[row_idx][col_idx]
                                        if cell_text:
                                            cell_requests.append({
                                                'insertText': {
                                                    'location': {'index': cell_start},
                                                    'text': cell_text
                                                }
                                            })
                                            # 첫 행 볼드
                                            if row_idx == 0:
                                                cell_requests.append({
                                                    'updateTextStyle': {
                                                        'range': {
                                                            'startIndex': cell_start,
                                                            'endIndex': cell_start + len(cell_text)
                                                        },
                                                        'textStyle': {'bold': True},
                                                        'fields': 'bold'
                                                    }
                                                })

                            if cell_requests:
                                cell_requests.reverse()
                                docs_service.documents().batchUpdate(
                                    documentId=DOC_ID,
                                    body={'requests': cell_requests}
                                ).execute()

                            # 첫 행 배경색
                            try:
                                docs_service.documents().batchUpdate(
                                    documentId=DOC_ID,
                                    body={'requests': [{
                                        'updateTableCellStyle': {
                                            'tableStartLocation': {'index': el['startIndex'] + 1},
                                            'tableCellStyle': {
                                                'backgroundColor': {
                                                    'color': {'rgbColor': {'red': 0.92, 'green': 0.92, 'blue': 0.92}}
                                                }
                                            },
                                            'fields': 'backgroundColor'
                                        }
                                    }]}
                                ).execute()
                            except:
                                pass

                            break

                except Exception as e:
                    print(f"    테이블 {idx} 실패: {str(e)[:30]}")

                break

        time.sleep(1)

    print("\n" + "=" * 70)
    print("완료!")
    print(f"문서: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 70)


if __name__ == "__main__":
    main()
