"""
Google Docs 디자인 및 테이블 수정
1. 페이지 설정 확인
2. 테이블 너비 A4에 맞게 조정
3. 폰트 및 색상 스타일 적용
"""

import os
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents']
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '150uymfx3hYZaXF6yzmU6WghAXMt6RXocMCZth0R0z8k'

# A4 본문 영역 (595pt - 72*2 여백 = 451pt)
CONTENT_WIDTH = 451


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


def check_page_setup(docs_service, doc_id):
    """페이지 설정 확인"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    style = doc.get('documentStyle', {})

    page_size = style.get('pageSize', {})
    width = page_size.get('width', {}).get('magnitude', 0)
    height = page_size.get('height', {}).get('magnitude', 0)

    margins = {
        'top': style.get('marginTop', {}).get('magnitude', 0),
        'bottom': style.get('marginBottom', {}).get('magnitude', 0),
        'left': style.get('marginLeft', {}).get('magnitude', 0),
        'right': style.get('marginRight', {}).get('magnitude', 0)
    }

    print(f"  Page: {width:.0f}pt x {height:.0f}pt")
    print(f"  Margins: T={margins['top']:.0f} B={margins['bottom']:.0f} L={margins['left']:.0f} R={margins['right']:.0f}")
    print(f"  Content Width: {width - margins['left'] - margins['right']:.0f}pt")

    return width - margins['left'] - margins['right']


def apply_heading_styles(docs_service, doc_id):
    """헤딩 폰트 스타일 적용"""

    # Named Style 업데이트
    requests = [
        # HEADING_1: 24pt, 볼드, 진한 파란색
        {
            'updateTextStyle': {
                'range': {'startIndex': 1, 'endIndex': 2},  # 임시
                'textStyle': {},
                'fields': '*'
            }
        }
    ]

    # Named Styles 전체 업데이트
    named_style_requests = [{
        'updateDocumentStyle': {
            'documentStyle': {
                'defaultHeaderId': '',
                'defaultFooterId': ''
            },
            'fields': 'defaultHeaderId,defaultFooterId'
        }
    }]

    # 실제 스타일은 updateParagraphStyle로 직접 적용
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    style_requests = []

    for element in content:
        if 'paragraph' not in element:
            continue

        para = element['paragraph']
        style_type = para.get('paragraphStyle', {}).get('namedStyleType', '')
        start = element['startIndex']
        end = element['endIndex']

        if style_type == 'HEADING_1':
            # H1: 24pt, Bold, Dark Blue
            style_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': start, 'endIndex': end - 1},
                    'textStyle': {
                        'fontSize': {'magnitude': 24, 'unit': 'PT'},
                        'bold': True,
                        'foregroundColor': {
                            'color': {'rgbColor': {'red': 0.1, 'green': 0.2, 'blue': 0.5}}
                        }
                    },
                    'fields': 'fontSize,bold,foregroundColor'
                }
            })

        elif style_type == 'HEADING_2':
            # H2: 18pt, Bold, Dark Gray
            style_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': start, 'endIndex': end - 1},
                    'textStyle': {
                        'fontSize': {'magnitude': 18, 'unit': 'PT'},
                        'bold': True,
                        'foregroundColor': {
                            'color': {'rgbColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2}}
                        }
                    },
                    'fields': 'fontSize,bold,foregroundColor'
                }
            })
            # H2 하단 보더 효과 (밑줄)
            style_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'paragraphStyle': {
                        'borderBottom': {
                            'color': {'color': {'rgbColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}}},
                            'width': {'magnitude': 1, 'unit': 'PT'},
                            'padding': {'magnitude': 6, 'unit': 'PT'},
                            'dashStyle': 'SOLID'
                        },
                        'spaceBelow': {'magnitude': 12, 'unit': 'PT'}
                    },
                    'fields': 'borderBottom,spaceBelow'
                }
            })

        elif style_type == 'HEADING_3':
            # H3: 14pt, Bold
            style_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': start, 'endIndex': end - 1},
                    'textStyle': {
                        'fontSize': {'magnitude': 14, 'unit': 'PT'},
                        'bold': True,
                        'foregroundColor': {
                            'color': {'rgbColor': {'red': 0.25, 'green': 0.25, 'blue': 0.25}}
                        }
                    },
                    'fields': 'fontSize,bold,foregroundColor'
                }
            })

        elif style_type == 'HEADING_4':
            # H4: 12pt, Bold, Gray
            style_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': start, 'endIndex': end - 1},
                    'textStyle': {
                        'fontSize': {'magnitude': 12, 'unit': 'PT'},
                        'bold': True,
                        'foregroundColor': {
                            'color': {'rgbColor': {'red': 0.4, 'green': 0.4, 'blue': 0.4}}
                        }
                    },
                    'fields': 'fontSize,bold,foregroundColor'
                }
            })

    # 배치로 적용
    if style_requests:
        for i in range(0, len(style_requests), 30):
            batch = style_requests[i:i+30]
            try:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': batch}
                ).execute()
            except Exception as e:
                print(f"    스타일 적용 오류: {str(e)[:40]}")
            time.sleep(1)

    return len(style_requests)


def fix_table_widths(docs_service, doc_id, content_width):
    """테이블 너비를 본문 영역에 맞게 조정"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    table_count = 0

    for element in content:
        if 'table' not in element:
            continue

        table = element['table']
        table_start = element['startIndex']
        num_cols = len(table.get('tableRows', [{}])[0].get('tableCells', []))

        if num_cols == 0:
            continue

        # 각 열의 너비를 균등하게 설정
        col_width = content_width / num_cols

        # 열 너비 업데이트
        col_requests = []
        for col_idx in range(num_cols):
            col_requests.append({
                'updateTableColumnProperties': {
                    'tableStartLocation': {'index': table_start + 1},
                    'columnIndices': [col_idx],
                    'tableColumnProperties': {
                        'width': {'magnitude': col_width, 'unit': 'PT'},
                        'widthType': 'FIXED_WIDTH'
                    },
                    'fields': 'width,widthType'
                }
            })

        try:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': col_requests}
            ).execute()
            table_count += 1
        except Exception as e:
            print(f"    테이블 너비 조정 실패: {str(e)[:40]}")

        time.sleep(0.5)

    return table_count


def apply_body_font(docs_service, doc_id):
    """본문 폰트 스타일 적용"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    requests = []

    for element in content:
        if 'paragraph' not in element:
            continue

        para = element['paragraph']
        style_type = para.get('paragraphStyle', {}).get('namedStyleType', '')
        start = element['startIndex']
        end = element['endIndex']

        # 헤딩이 아닌 일반 텍스트
        if style_type == 'NORMAL_TEXT' or not style_type:
            # 본문: 11pt
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': start, 'endIndex': end - 1},
                    'textStyle': {
                        'fontSize': {'magnitude': 11, 'unit': 'PT'},
                        'foregroundColor': {
                            'color': {'rgbColor': {'red': 0.15, 'green': 0.15, 'blue': 0.15}}
                        }
                    },
                    'fields': 'fontSize,foregroundColor'
                }
            })
            # 줄 간격
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'paragraphStyle': {
                        'lineSpacing': 130,  # 130%
                        'spaceAbove': {'magnitude': 3, 'unit': 'PT'},
                        'spaceBelow': {'magnitude': 3, 'unit': 'PT'}
                    },
                    'fields': 'lineSpacing,spaceAbove,spaceBelow'
                }
            })

    # 배치로 적용
    if requests:
        for i in range(0, len(requests), 30):
            batch = requests[i:i+30]
            try:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': batch}
                ).execute()
            except Exception as e:
                pass
            time.sleep(1)

    return len(requests) // 2


def style_table_headers(docs_service, doc_id):
    """테이블 헤더 행 스타일 강화"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    styled = 0

    for element in content:
        if 'table' not in element:
            continue

        table = element['table']
        table_start = element['startIndex']

        # 첫 번째 행의 셀들
        first_row = table.get('tableRows', [{}])[0]
        cells = first_row.get('tableCells', [])

        requests = []

        for cell in cells:
            cell_content = cell.get('content', [])
            if cell_content:
                cell_start = cell_content[0].get('startIndex', 0)
                cell_end = cell_content[-1].get('endIndex', cell_start + 1)

                # 헤더 텍스트 스타일: 볼드 + 흰색
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': cell_start, 'endIndex': cell_end - 1},
                        'textStyle': {
                            'bold': True,
                            'fontSize': {'magnitude': 10, 'unit': 'PT'},
                            'foregroundColor': {
                                'color': {'rgbColor': {'red': 1, 'green': 1, 'blue': 1}}
                            }
                        },
                        'fields': 'bold,fontSize,foregroundColor'
                    }
                })

        # 헤더 행 배경색 (진한 파란색)
        requests.append({
            'updateTableCellStyle': {
                'tableStartLocation': {'index': table_start + 1},
                'tableCellStyle': {
                    'backgroundColor': {
                        'color': {'rgbColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5}}
                    },
                    'paddingTop': {'magnitude': 6, 'unit': 'PT'},
                    'paddingBottom': {'magnitude': 6, 'unit': 'PT'},
                    'paddingLeft': {'magnitude': 6, 'unit': 'PT'},
                    'paddingRight': {'magnitude': 6, 'unit': 'PT'}
                },
                'fields': 'backgroundColor,paddingTop,paddingBottom,paddingLeft,paddingRight'
            }
        })

        if requests:
            try:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
                styled += 1
            except Exception as e:
                pass
            time.sleep(0.5)

    return styled


def main():
    print("=" * 60)
    print("Google Docs 디자인 및 테이블 수정")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 1. 페이지 설정 확인
    print("\n[1/5] 페이지 설정 확인...")
    content_width = check_page_setup(docs_service, DOC_ID)

    # 2. 테이블 너비 조정
    print("\n[2/5] 테이블 너비 조정...")
    tables = fix_table_widths(docs_service, DOC_ID, content_width)
    print(f"  {tables}개 테이블 조정")

    time.sleep(2)

    # 3. 헤딩 스타일 적용
    print("\n[3/5] 헤딩 스타일 적용...")
    headings = apply_heading_styles(docs_service, DOC_ID)
    print(f"  {headings}개 스타일 적용")

    time.sleep(2)

    # 4. 본문 폰트 적용
    print("\n[4/5] 본문 폰트 적용...")
    body = apply_body_font(docs_service, DOC_ID)
    print(f"  {body}개 문단 적용")

    time.sleep(2)

    # 5. 테이블 헤더 스타일
    print("\n[5/5] 테이블 헤더 스타일...")
    headers = style_table_headers(docs_service, DOC_ID)
    print(f"  {headers}개 테이블 헤더 스타일")

    print("\n" + "=" * 60)
    print("완료!")
    print(f"\n문서: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
