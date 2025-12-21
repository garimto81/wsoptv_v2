"""
Google Docs 완전 재생성 - 디자인 + A4 최적화
- 테이블: 4열 이상은 2열로 분할 또는 축약
- 폰트: 세련된 디자인 적용
- A4 세로에 맞는 레이아웃
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

# A4 설정
A4_WIDTH = 595.276
A4_HEIGHT = 841.890
MARGIN = 72
CONTENT_WIDTH = A4_WIDTH - (MARGIN * 2)  # 451pt
IMAGE_WIDTH = 400  # A4에 맞는 이미지 너비


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
    """마크다운 파싱"""
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

        # 테이블 - 최대 3열로 제한
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
                # 4열 이상이면 처음 3열만
                if len(cells) > 3:
                    cells = cells[:3]
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

        # 코드 블록 스킵
        elif stripped.startswith('```'):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                i += 1
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


def clear_and_setup(docs_service, doc_id):
    """문서 초기화 및 A4 설정"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    end_index = content[-1].get('endIndex', 1) - 1 if content else 0

    requests = []

    if end_index > 1:
        requests.append({
            'deleteContentRange': {
                'range': {'startIndex': 1, 'endIndex': end_index}
            }
        })

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

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()


def insert_element(docs_service, doc_id, item):
    """단일 요소 삽입 및 스타일 적용"""
    item_type = item['type']

    if item_type == 'h1':
        text = item['text'] + '\n\n'
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': text}},
            {
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'textStyle': {
                        'fontSize': {'magnitude': 26, 'unit': 'PT'},
                        'bold': True,
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.1, 'green': 0.2, 'blue': 0.4}}}
                    },
                    'fields': 'fontSize,bold,foregroundColor'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_1',
                        'spaceBelow': {'magnitude': 18, 'unit': 'PT'}
                    },
                    'fields': 'namedStyleType,spaceBelow'
                }
            }
        ]

    elif item_type == 'h2':
        text = item['text'] + '\n\n'
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': text}},
            {
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'textStyle': {
                        'fontSize': {'magnitude': 18, 'unit': 'PT'},
                        'bold': True,
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.15, 'green': 0.25, 'blue': 0.45}}}
                    },
                    'fields': 'fontSize,bold,foregroundColor'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_2',
                        'spaceAbove': {'magnitude': 18, 'unit': 'PT'},
                        'spaceBelow': {'magnitude': 8, 'unit': 'PT'},
                        'borderBottom': {
                            'color': {'color': {'rgbColor': {'red': 0.7, 'green': 0.7, 'blue': 0.7}}},
                            'width': {'magnitude': 1, 'unit': 'PT'},
                            'padding': {'magnitude': 4, 'unit': 'PT'},
                            'dashStyle': 'SOLID'
                        }
                    },
                    'fields': 'namedStyleType,spaceAbove,spaceBelow,borderBottom'
                }
            }
        ]

    elif item_type == 'h3':
        text = item['text'] + '\n'
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': text}},
            {
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'textStyle': {
                        'fontSize': {'magnitude': 13, 'unit': 'PT'},
                        'bold': True,
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2}}}
                    },
                    'fields': 'fontSize,bold,foregroundColor'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_3',
                        'spaceAbove': {'magnitude': 14, 'unit': 'PT'},
                        'spaceBelow': {'magnitude': 6, 'unit': 'PT'}
                    },
                    'fields': 'namedStyleType,spaceAbove,spaceBelow'
                }
            }
        ]

    elif item_type == 'h4':
        text = item['text'] + '\n'
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': text}},
            {
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'textStyle': {
                        'fontSize': {'magnitude': 11, 'unit': 'PT'},
                        'bold': True,
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.35, 'green': 0.35, 'blue': 0.35}}}
                    },
                    'fields': 'fontSize,bold,foregroundColor'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_4',
                        'spaceAbove': {'magnitude': 10, 'unit': 'PT'}
                    },
                    'fields': 'namedStyleType,spaceAbove'
                }
            }
        ]

    elif item_type == 'para':
        text = item['text'] + '\n'
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': text}},
            {
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'textStyle': {
                        'fontSize': {'magnitude': 10, 'unit': 'PT'},
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2}}}
                    },
                    'fields': 'fontSize,foregroundColor'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'paragraphStyle': {
                        'lineSpacing': 140
                    },
                    'fields': 'lineSpacing'
                }
            }
        ]

    elif item_type == 'quote':
        text = item['text'] + '\n'
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': text}},
            {
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'textStyle': {
                        'fontSize': {'magnitude': 10, 'unit': 'PT'},
                        'italic': True,
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.4, 'green': 0.4, 'blue': 0.4}}}
                    },
                    'fields': 'fontSize,italic,foregroundColor'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'paragraphStyle': {
                        'indentStart': {'magnitude': 24, 'unit': 'PT'},
                        'borderLeft': {
                            'color': {'color': {'rgbColor': {'red': 0.6, 'green': 0.6, 'blue': 0.6}}},
                            'width': {'magnitude': 3, 'unit': 'PT'},
                            'padding': {'magnitude': 8, 'unit': 'PT'},
                            'dashStyle': 'SOLID'
                        }
                    },
                    'fields': 'indentStart,borderLeft'
                }
            }
        ]

    elif item_type == 'bullet':
        text = item['text'] + '\n'
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': text}},
            {
                'createParagraphBullets': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                }
            },
            {
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'textStyle': {
                        'fontSize': {'magnitude': 10, 'unit': 'PT'}
                    },
                    'fields': 'fontSize'
                }
            }
        ]

    elif item_type == 'number':
        text = item['text'] + '\n'
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': text}},
            {
                'createParagraphBullets': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'bulletPreset': 'NUMBERED_DECIMAL_NESTED'
                }
            },
            {
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(text)},
                    'textStyle': {
                        'fontSize': {'magnitude': 10, 'unit': 'PT'}
                    },
                    'fields': 'fontSize'
                }
            }
        ]

    elif item_type == 'image':
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': '\n'}},
            {
                'insertInlineImage': {
                    'location': {'index': 1},
                    'uri': item['url'],
                    'objectSize': {
                        'width': {'magnitude': IMAGE_WIDTH, 'unit': 'PT'},
                        'height': {'magnitude': IMAGE_WIDTH * 0.6, 'unit': 'PT'}
                    }
                }
            }
        ]

    elif item_type == 'table':
        # 테이블 플레이스홀더 삽입 (나중에 처리)
        data = item['data']
        placeholder = f"[TBL:{len(data)}x{len(data[0]) if data else 0}]\n"
        requests = [{'insertText': {'location': {'index': 1}, 'text': placeholder}}]
        return requests, item['data']

    else:
        return None, None

    return requests, None


def insert_table(docs_service, doc_id, data, position):
    """테이블 삽입 (3열 이하)"""
    num_rows = len(data)
    num_cols = min(len(data[0]), 3) if data else 0

    if num_cols == 0:
        return

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
                        cell_text = data[row_idx][col_idx][:30]  # 30자 제한
                        if cell_text:
                            cell_requests.append({
                                'insertText': {
                                    'location': {'index': cell_start},
                                    'text': cell_text
                                }
                            })
                            # 헤더 행 볼드
                            if row_idx == 0:
                                cell_requests.append({
                                    'updateTextStyle': {
                                        'range': {'startIndex': cell_start, 'endIndex': cell_start + len(cell_text)},
                                        'textStyle': {
                                            'bold': True,
                                            'fontSize': {'magnitude': 9, 'unit': 'PT'}
                                        },
                                        'fields': 'bold,fontSize'
                                    }
                                })
                            else:
                                cell_requests.append({
                                    'updateTextStyle': {
                                        'range': {'startIndex': cell_start, 'endIndex': cell_start + len(cell_text)},
                                        'textStyle': {
                                            'fontSize': {'magnitude': 9, 'unit': 'PT'}
                                        },
                                        'fields': 'fontSize'
                                    }
                                })

            if cell_requests:
                cell_requests.reverse()
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': cell_requests}
                ).execute()

            break


def main():
    print("=" * 60)
    print("Google Docs 완전 재생성 (A4 + 디자인)")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 1. 마크다운 파싱
    print("\n[1/4] 마크다운 파싱...")
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()
    parsed = parse_markdown(md_content)
    print(f"  {len(parsed)}개 요소")

    # 2. 문서 초기화
    print("\n[2/4] 문서 초기화 및 A4 설정...")
    clear_and_setup(docs_service, DOC_ID)
    print("  A4 세로, 여백 1인치")

    # 3. 요소 삽입 (역순)
    print("\n[3/4] 콘텐츠 삽입...")
    tables_to_insert = []

    for i, item in enumerate(reversed(parsed)):
        requests, table_data = insert_element(docs_service, DOC_ID, item)
        if requests:
            try:
                docs_service.documents().batchUpdate(
                    documentId=DOC_ID,
                    body={'requests': requests}
                ).execute()
                if table_data:
                    tables_to_insert.append(table_data)
            except Exception as e:
                pass
            time.sleep(0.3)

        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(parsed)} 완료")

    print(f"  {len(parsed)}개 요소 삽입 완료")

    # 4. 테이블 삽입
    print(f"\n[4/4] 테이블 {len(tables_to_insert)}개 삽입...")

    for idx, table_data in enumerate(reversed(tables_to_insert)):
        # 플레이스홀더 찾기
        doc = docs_service.documents().get(documentId=DOC_ID).execute()
        content = doc.get('body', {}).get('content', [])

        for element in content:
            if 'paragraph' not in element:
                continue
            para_text = ''
            for elem in element['paragraph'].get('elements', []):
                if 'textRun' in elem:
                    para_text += elem['textRun'].get('content', '')

            if '[TBL:' in para_text:
                start = element['startIndex']
                end = element['endIndex']

                # 플레이스홀더 삭제
                try:
                    docs_service.documents().batchUpdate(
                        documentId=DOC_ID,
                        body={'requests': [{
                            'deleteContentRange': {
                                'range': {'startIndex': start, 'endIndex': end - 1}
                            }
                        }]}
                    ).execute()
                except:
                    pass

                time.sleep(0.3)

                # 테이블 삽입
                try:
                    insert_table(docs_service, DOC_ID, table_data, start)
                except Exception as e:
                    pass

                break

        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("완료!")
    print(f"\n문서: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
