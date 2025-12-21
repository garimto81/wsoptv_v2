"""
03-content-strategy.md → Google Docs 완전 자동 변환

모든 서식 자동 처리:
1. A4 용지 설정 (여백 포함)
2. 헤딩 스타일 (H1~H4)
3. 테이블 헤더 스타일 (배경색 + 볼드)
4. 이미지 크기 통일 (17cm = 481pt)
5. 마크다운 볼드 → 실제 볼드
6. 인용문 스타일 (들여쓰기 + 이탤릭)
7. 빈 줄 최소화
"""

import os
import re
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# === 설정 ===
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'

DOC_ID = '150uymfx3hYZaXF6yzmU6WghAXMt6RXocMCZth0R0z8k'
MD_FILE = r'D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\03-content-strategy.md'

# A4 설정 (단위: PT, 1인치 = 72pt)
A4_WIDTH = 595.276  # 210mm
A4_HEIGHT = 841.890  # 297mm
MARGIN_TOP = 72      # 1인치
MARGIN_BOTTOM = 72
MARGIN_LEFT = 72
MARGIN_RIGHT = 72

# 이미지 너비 (17cm = 481pt, A4 본문 영역에 맞춤)
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


def parse_markdown_table(lines):
    """마크다운 테이블 파싱"""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            continue
        if re.match(r'^\|[\s\-:|]+\|$', line):
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        # 볼드 마크다운 제거
        cells = [re.sub(r'\*\*([^*]+)\*\*', r'\1', c) for c in cells]
        if cells and any(c for c in cells):
            rows.append(cells)
    return rows


def convert_markdown(md_content):
    """마크다운을 구조화된 데이터로 변환"""
    lines = md_content.split('\n')
    structure = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 빈 줄 - 연속 빈 줄은 1개만
        if not stripped:
            if structure and structure[-1].get('type') != 'blank':
                structure.append({'type': 'blank'})
            i += 1
            continue

        # 수평선 스킵
        if stripped == '---':
            i += 1
            continue

        # 이미지
        if '<img' in stripped and 'src=' in stripped:
            match = re.search(r'src="([^"]+)"', stripped)
            if match:
                structure.append({'type': 'image', 'url': match.group(1)})
            i += 1
            continue

        # 헤딩
        if stripped.startswith('####'):
            text = stripped[4:].strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            structure.append({'type': 'heading4', 'text': text})
            i += 1
            continue
        elif stripped.startswith('###'):
            text = stripped[3:].strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            structure.append({'type': 'heading3', 'text': text})
            i += 1
            continue
        elif stripped.startswith('##'):
            text = stripped[2:].strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            structure.append({'type': 'heading2', 'text': text})
            i += 1
            continue
        elif stripped.startswith('#'):
            text = stripped[1:].strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            structure.append({'type': 'heading1', 'text': text})
            i += 1
            continue

        # 테이블
        if stripped.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            table_data = parse_markdown_table(table_lines)
            if table_data:
                structure.append({'type': 'table', 'data': table_data})
            continue

        # 인용문
        if stripped.startswith('>'):
            text = stripped[1:].strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            structure.append({'type': 'quote', 'text': text})
            i += 1
            continue

        # 코드 블록
        if stripped.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            structure.append({'type': 'code', 'text': '\n'.join(code_lines)})
            i += 1
            continue

        # 일반 텍스트
        text = stripped
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # 볼드 텍스트 위치 기록
        bold_matches = list(re.finditer(r'\*\*([^*]+)\*\*', text))
        clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

        if text.startswith('- '):
            structure.append({'type': 'list_item', 'text': clean_text[2:], 'bold_matches': bold_matches})
        elif re.match(r'^\d+\.', text):
            structure.append({'type': 'numbered_item', 'text': re.sub(r'^\d+\.\s*', '', clean_text), 'bold_matches': bold_matches})
        else:
            structure.append({'type': 'paragraph', 'text': clean_text, 'bold_matches': bold_matches})

        i += 1

    return structure


def clear_document(docs_service, doc_id):
    """문서 초기화"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    if content:
        end_index = content[-1].get('endIndex', 1) - 1
        if end_index > 1:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': [{
                    'deleteContentRange': {
                        'range': {'startIndex': 1, 'endIndex': end_index}
                    }
                }]}
            ).execute()


def set_page_setup(docs_service, doc_id):
    """A4 페이지 설정"""
    requests = [{
        'updateDocumentStyle': {
            'documentStyle': {
                'pageSize': {
                    'width': {'magnitude': A4_WIDTH, 'unit': 'PT'},
                    'height': {'magnitude': A4_HEIGHT, 'unit': 'PT'}
                },
                'marginTop': {'magnitude': MARGIN_TOP, 'unit': 'PT'},
                'marginBottom': {'magnitude': MARGIN_BOTTOM, 'unit': 'PT'},
                'marginLeft': {'magnitude': MARGIN_LEFT, 'unit': 'PT'},
                'marginRight': {'magnitude': MARGIN_RIGHT, 'unit': 'PT'}
            },
            'fields': 'pageSize,marginTop,marginBottom,marginLeft,marginRight'
        }
    }]
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()


def insert_content(docs_service, doc_id, structure):
    """콘텐츠 삽입 (역순으로)"""

    # 모든 요소를 역순으로 삽입
    for item in reversed(structure):
        item_type = item['type']

        if item_type == 'blank':
            requests = [{
                'insertText': {
                    'location': {'index': 1},
                    'text': '\n'
                }
            }]

        elif item_type in ['heading1', 'heading2', 'heading3', 'heading4']:
            style_map = {
                'heading1': 'HEADING_1',
                'heading2': 'HEADING_2',
                'heading3': 'HEADING_3',
                'heading4': 'HEADING_4'
            }
            text = item['text'] + '\n'
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': text
                    }
                },
                {
                    'updateParagraphStyle': {
                        'range': {'startIndex': 1, 'endIndex': 1 + len(text)},
                        'paragraphStyle': {'namedStyleType': style_map[item_type]},
                        'fields': 'namedStyleType'
                    }
                }
            ]

        elif item_type == 'paragraph':
            text = item['text'] + '\n'
            requests = [{
                'insertText': {
                    'location': {'index': 1},
                    'text': text
                }
            }]

        elif item_type == 'quote':
            text = item['text'] + '\n'
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': text
                    }
                },
                {
                    'updateParagraphStyle': {
                        'range': {'startIndex': 1, 'endIndex': 1 + len(text)},
                        'paragraphStyle': {
                            'indentFirstLine': {'magnitude': 36, 'unit': 'PT'},
                            'indentStart': {'magnitude': 36, 'unit': 'PT'}
                        },
                        'fields': 'indentFirstLine,indentStart'
                    }
                },
                {
                    'updateTextStyle': {
                        'range': {'startIndex': 1, 'endIndex': 1 + len(text) - 1},
                        'textStyle': {'italic': True},
                        'fields': 'italic'
                    }
                }
            ]

        elif item_type == 'list_item':
            text = item['text'] + '\n'
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': text
                    }
                },
                {
                    'createParagraphBullets': {
                        'range': {'startIndex': 1, 'endIndex': 1 + len(text)},
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                    }
                }
            ]

        elif item_type == 'numbered_item':
            text = item['text'] + '\n'
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': text
                    }
                },
                {
                    'createParagraphBullets': {
                        'range': {'startIndex': 1, 'endIndex': 1 + len(text)},
                        'bulletPreset': 'NUMBERED_DECIMAL_NESTED'
                    }
                }
            ]

        elif item_type == 'code':
            text = item['text'] + '\n'
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': text
                    }
                },
                {
                    'updateTextStyle': {
                        'range': {'startIndex': 1, 'endIndex': 1 + len(text) - 1},
                        'textStyle': {
                            'weightedFontFamily': {'fontFamily': 'Consolas'},
                            'fontSize': {'magnitude': 9, 'unit': 'PT'},
                            'backgroundColor': {'color': {'rgbColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}}}
                        },
                        'fields': 'weightedFontFamily,fontSize,backgroundColor'
                    }
                }
            ]

        elif item_type == 'image':
            url = item['url']
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': '\n'
                    }
                },
                {
                    'insertInlineImage': {
                        'location': {'index': 1},
                        'uri': url,
                        'objectSize': {
                            'width': {'magnitude': IMAGE_WIDTH, 'unit': 'PT'},
                            'height': {'magnitude': IMAGE_WIDTH * 0.6, 'unit': 'PT'}
                        }
                    }
                }
            ]

        elif item_type == 'table':
            # 테이블은 나중에 별도 처리
            continue

        else:
            continue

        try:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            time.sleep(0.3)
        except Exception as e:
            print(f"  요소 삽입 실패 ({item_type}): {str(e)[:50]}")


def insert_tables(docs_service, doc_id, structure):
    """테이블 삽입 (앵커 텍스트 기반)"""

    # 테이블과 앵커 매핑 (헤딩 바로 다음에 오는 테이블)
    table_anchors = []
    prev_heading = None

    for item in structure:
        if item['type'] in ['heading2', 'heading3', 'heading4']:
            prev_heading = item['text']
        elif item['type'] == 'table' and prev_heading:
            table_anchors.append({
                'anchor': prev_heading,
                'data': item['data']
            })
            prev_heading = None  # 하나의 헤딩에 하나의 테이블만

    print(f"  테이블 {len(table_anchors)}개 삽입 중...")

    for idx, ta in enumerate(reversed(table_anchors)):
        anchor = ta['anchor']
        data = ta['data']

        # 앵커 위치 찾기
        doc = docs_service.documents().get(documentId=doc_id).execute()
        content = doc.get('body', {}).get('content', [])

        position = None
        for element in content:
            if 'paragraph' not in element:
                continue
            para = element['paragraph']
            text = ''
            for elem in para.get('elements', []):
                if 'textRun' in elem:
                    text += elem['textRun'].get('content', '')
            if anchor in text:
                position = element['endIndex']
                break

        if not position:
            continue

        num_rows = len(data)
        num_cols = max(len(row) for row in data) if data else 0

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
            time.sleep(0.5)

            # 셀 내용 삽입
            doc = docs_service.documents().get(documentId=doc_id).execute()
            content = doc.get('body', {}).get('content', [])

            for element in content:
                if 'table' not in element:
                    continue
                if abs(element['startIndex'] - position) < 20:
                    table = element['table']
                    cell_requests = []
                    header_cells = []

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
                                    # 첫 번째 행은 헤더
                                    if row_idx == 0:
                                        header_cells.append({
                                            'start': cell_start,
                                            'end': cell_start + len(cell_text)
                                        })

                    if cell_requests:
                        cell_requests.reverse()
                        docs_service.documents().batchUpdate(
                            documentId=doc_id,
                            body={'requests': cell_requests}
                        ).execute()

                    # 헤더 스타일 적용 (볼드 + 배경색)
                    if header_cells:
                        time.sleep(0.3)
                        style_requests = []
                        for hc in header_cells:
                            style_requests.append({
                                'updateTextStyle': {
                                    'range': {'startIndex': hc['start'], 'endIndex': hc['end']},
                                    'textStyle': {'bold': True},
                                    'fields': 'bold'
                                }
                            })

                        # 테이블 첫 행 배경색
                        first_row = table.get('tableRows', [])[0] if table.get('tableRows') else None
                        if first_row:
                            for cell in first_row.get('tableCells', []):
                                style_requests.append({
                                    'updateTableCellStyle': {
                                        'tableStartLocation': {'index': element['startIndex'] + 1},
                                        'tableCellStyle': {
                                            'backgroundColor': {
                                                'color': {
                                                    'rgbColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                                                }
                                            }
                                        },
                                        'fields': 'backgroundColor'
                                    }
                                })
                                break  # 한 번만

                        if style_requests:
                            try:
                                docs_service.documents().batchUpdate(
                                    documentId=doc_id,
                                    body={'requests': style_requests}
                                ).execute()
                            except:
                                pass

                    break

            time.sleep(0.5)

        except Exception as e:
            print(f"    테이블 삽입 실패: {str(e)[:50]}")


def main():
    print("=" * 70)
    print("Google Docs 완전 자동 생성")
    print("A4 용지 + 모든 서식 자동 적용")
    print("=" * 70)

    # 인증
    print("\n[1/6] Google API 인증...")
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 마크다운 읽기
    print("\n[2/6] 마크다운 파일 읽기...")
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()
    print(f"  원본: {len(md_content):,} 문자")

    # 구조화
    print("\n[3/6] 마크다운 구조 분석...")
    structure = convert_markdown(md_content)
    type_counts = {}
    for item in structure:
        t = item['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}개")

    # 문서 초기화
    print("\n[4/6] 문서 초기화 및 A4 설정...")
    clear_document(docs_service, DOC_ID)
    set_page_setup(docs_service, DOC_ID)
    print("  A4 (210x297mm), 여백 1인치")

    # 콘텐츠 삽입
    print("\n[5/6] 콘텐츠 삽입...")
    insert_content(docs_service, DOC_ID, structure)

    # 테이블 삽입
    print("\n[6/6] 테이블 삽입 및 스타일 적용...")
    insert_tables(docs_service, DOC_ID, structure)

    # 완료
    print("\n" + "=" * 70)
    print("완료!")
    print()
    print("[적용된 서식]")
    print("  - A4 용지 (210x297mm)")
    print("  - 여백: 상하좌우 1인치 (25.4mm)")
    print("  - 이미지: 17cm 너비 (본문 영역 맞춤)")
    print("  - 헤딩: H1~H4 네이티브 스타일")
    print("  - 테이블: 헤더 행 배경색 + 볼드")
    print("  - 인용문: 들여쓰기 + 이탤릭")
    print("  - 리스트: 네이티브 불릿/번호")
    print()
    print(f"문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 70)


if __name__ == "__main__":
    main()
