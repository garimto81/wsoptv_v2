"""
03-content-strategy.md → Google Docs 마이그레이션 스크립트

마크다운 원본을 Google Docs 네이티브 포맷으로 변환:
- 헤딩 스타일 적용 (H1, H2, H3, H4)
- 마크다운 테이블 → Google Docs 네이티브 테이블
- 이미지 URL → 인라인 이미지 삽입
- 볼드/이탤릭 서식 적용
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

# 대상 문서 (WSOPTV 콘텐츠 전략)
DOC_ID = '150uymfx3hYZaXF6yzmU6WghAXMt6RXocMCZth0R0z8k'

# 원본 마크다운 파일
MD_FILE = r'D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\03-content-strategy.md'


def get_credentials():
    """Google API 인증"""
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


def extract_image_urls(md_content):
    """마크다운에서 이미지 URL 추출"""
    # <img src="..."> 패턴
    pattern = r'<img\s+src="([^"]+)"[^>]*>'
    return re.findall(pattern, md_content)


def parse_markdown_table(lines):
    """마크다운 테이블 파싱 → 2D 배열"""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            continue
        # 구분자 라인 스킵 (|---|---|)
        if re.match(r'^\|[\s\-:|]+\|$', line):
            continue
        # 셀 추출
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if cells and any(c for c in cells):
            rows.append(cells)
    return rows


def convert_markdown_to_structure(md_content):
    """
    마크다운을 구조화된 데이터로 변환

    Returns:
        list of dict: [
            {'type': 'heading1', 'text': '...'},
            {'type': 'heading2', 'text': '...'},
            {'type': 'paragraph', 'text': '...'},
            {'type': 'table', 'data': [[...], [...]]},
            {'type': 'image', 'url': '...'},
            ...
        ]
    """
    lines = md_content.split('\n')
    structure = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 빈 줄 스킵
        if not stripped:
            i += 1
            continue

        # 수평선 스킵
        if stripped == '---':
            i += 1
            continue

        # 이미지 태그
        if '<img' in stripped and 'src=' in stripped:
            match = re.search(r'src="([^"]+)"', stripped)
            if match:
                structure.append({'type': 'image', 'url': match.group(1)})
            i += 1
            continue

        # 헤딩 처리
        if stripped.startswith('####'):
            structure.append({'type': 'heading4', 'text': stripped[4:].strip()})
            i += 1
            continue
        elif stripped.startswith('###'):
            structure.append({'type': 'heading3', 'text': stripped[3:].strip()})
            i += 1
            continue
        elif stripped.startswith('##'):
            structure.append({'type': 'heading2', 'text': stripped[2:].strip()})
            i += 1
            continue
        elif stripped.startswith('#'):
            structure.append({'type': 'heading1', 'text': stripped[1:].strip()})
            i += 1
            continue

        # 테이블 감지
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
            structure.append({'type': 'quote', 'text': text})
            i += 1
            continue

        # 코드 블록
        if stripped.startswith('```'):
            code_lines = []
            lang = stripped[3:].strip()
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            structure.append({'type': 'code', 'text': '\n'.join(code_lines), 'lang': lang})
            i += 1  # 닫는 ``` 스킵
            continue

        # 일반 텍스트/리스트
        text = stripped
        # 볼드 처리 (나중에 서식 적용)
        # 링크 텍스트만 추출 [text](url) → text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        if text.startswith('- '):
            structure.append({'type': 'list_item', 'text': text[2:]})
        elif re.match(r'^\d+\.', text):
            structure.append({'type': 'numbered_item', 'text': re.sub(r'^\d+\.\s*', '', text)})
        else:
            structure.append({'type': 'paragraph', 'text': text})

        i += 1

    return structure


def clear_document(docs_service, doc_id):
    """문서 내용 완전 삭제"""
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
    return True


def build_insert_requests(structure):
    """
    구조화된 데이터를 Google Docs API 요청으로 변환
    텍스트와 서식을 분리하여 처리
    """
    # 먼저 모든 텍스트를 역순으로 삽입 (index 1부터)
    # 그 다음 서식 적용

    text_content = ""
    style_ranges = []  # (start, end, style_type)
    table_placeholders = []  # (position_in_text, table_data)
    image_placeholders = []  # (position_in_text, url)

    current_pos = 0

    for item in structure:
        item_type = item['type']

        if item_type == 'heading1':
            text = item['text'] + '\n'
            style_ranges.append((current_pos, current_pos + len(text) - 1, 'HEADING_1'))
            text_content += text
            current_pos += len(text)

        elif item_type == 'heading2':
            text = item['text'] + '\n'
            style_ranges.append((current_pos, current_pos + len(text) - 1, 'HEADING_2'))
            text_content += text
            current_pos += len(text)

        elif item_type == 'heading3':
            text = item['text'] + '\n'
            style_ranges.append((current_pos, current_pos + len(text) - 1, 'HEADING_3'))
            text_content += text
            current_pos += len(text)

        elif item_type == 'heading4':
            text = item['text'] + '\n'
            style_ranges.append((current_pos, current_pos + len(text) - 1, 'HEADING_4'))
            text_content += text
            current_pos += len(text)

        elif item_type == 'paragraph':
            text = item['text'] + '\n'
            text_content += text
            current_pos += len(text)

        elif item_type == 'quote':
            text = '❝ ' + item['text'] + ' ❞\n'
            text_content += text
            current_pos += len(text)

        elif item_type == 'list_item':
            text = '• ' + item['text'] + '\n'
            text_content += text
            current_pos += len(text)

        elif item_type == 'numbered_item':
            text = item['text'] + '\n'
            text_content += text
            current_pos += len(text)

        elif item_type == 'code':
            text = item['text'] + '\n\n'
            text_content += text
            current_pos += len(text)

        elif item_type == 'table':
            # 테이블 위치 기록 (나중에 삽입)
            placeholder = f"[TABLE_PLACEHOLDER_{len(table_placeholders)}]\n"
            table_placeholders.append((current_pos, item['data']))
            text_content += placeholder
            current_pos += len(placeholder)

        elif item_type == 'image':
            # 이미지 위치 기록 (나중에 삽입)
            placeholder = f"[IMAGE_PLACEHOLDER_{len(image_placeholders)}]\n"
            image_placeholders.append((current_pos, item['url']))
            text_content += placeholder
            current_pos += len(placeholder)

    return text_content, style_ranges, table_placeholders, image_placeholders


def apply_heading_styles(docs_service, doc_id, style_ranges):
    """헤딩 스타일 적용"""
    if not style_ranges:
        return

    requests = []
    for start, end, style_type in style_ranges:
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': start + 1,  # 문서 인덱스는 1부터
                    'endIndex': end + 1
                },
                'paragraphStyle': {
                    'namedStyleType': style_type
                },
                'fields': 'namedStyleType'
            }
        })

    # 배치 크기 제한 (Google API 제한)
    batch_size = 50
    for i in range(0, len(requests), batch_size):
        batch = requests[i:i + batch_size]
        try:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': batch}
            ).execute()
        except Exception as e:
            print(f"  스타일 적용 오류 (배치 {i//batch_size + 1}): {e}")
        time.sleep(0.5)  # Rate limiting


def insert_image_at_placeholder(docs_service, doc_id, placeholder_text, image_url):
    """플레이스홀더를 이미지로 교체"""
    # 문서에서 플레이스홀더 위치 찾기
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'paragraph' not in element:
            continue
        para = element['paragraph']
        para_text = ''
        for elem in para.get('elements', []):
            if 'textRun' in elem:
                para_text += elem['textRun'].get('content', '')

        if placeholder_text in para_text:
            start_idx = element['startIndex']
            end_idx = element['endIndex']

            # 플레이스홀더 삭제 후 이미지 삽입
            requests = [
                {
                    'deleteContentRange': {
                        'range': {
                            'startIndex': start_idx,
                            'endIndex': end_idx - 1
                        }
                    }
                },
                {
                    'insertInlineImage': {
                        'location': {'index': start_idx},
                        'uri': image_url,
                        'objectSize': {
                            'width': {'magnitude': 400, 'unit': 'PT'},
                            'height': {'magnitude': 250, 'unit': 'PT'}
                        }
                    }
                }
            ]

            try:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
                return True
            except Exception as e:
                print(f"  이미지 삽입 실패: {e}")
                return False

    return False


def insert_table_at_placeholder(docs_service, doc_id, placeholder_text, table_data):
    """플레이스홀더를 테이블로 교체"""
    if not table_data or len(table_data) == 0:
        return False

    # 문서에서 플레이스홀더 위치 찾기
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'paragraph' not in element:
            continue
        para = element['paragraph']
        para_text = ''
        for elem in para.get('elements', []):
            if 'textRun' in elem:
                para_text += elem['textRun'].get('content', '')

        if placeholder_text in para_text:
            start_idx = element['startIndex']
            end_idx = element['endIndex']

            num_rows = len(table_data)
            num_cols = max(len(row) for row in table_data)

            # 플레이스홀더 삭제
            try:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': [{
                        'deleteContentRange': {
                            'range': {
                                'startIndex': start_idx,
                                'endIndex': end_idx - 1
                            }
                        }
                    }]}
                ).execute()
            except Exception as e:
                print(f"  플레이스홀더 삭제 실패: {e}")
                return False

            # 테이블 삽입
            try:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': [{
                        'insertTable': {
                            'rows': num_rows,
                            'columns': num_cols,
                            'location': {'index': start_idx}
                        }
                    }]}
                ).execute()
            except Exception as e:
                print(f"  테이블 삽입 실패: {e}")
                return False

            time.sleep(0.3)

            # 테이블 셀에 내용 삽입
            doc = docs_service.documents().get(documentId=doc_id).execute()
            content = doc.get('body', {}).get('content', [])

            for elem in content:
                if 'table' not in elem:
                    continue
                if elem['startIndex'] < start_idx + 10:
                    table = elem['table']
                    cell_requests = []

                    for row_idx, row in enumerate(table.get('tableRows', [])):
                        if row_idx >= len(table_data):
                            break
                        for col_idx, cell in enumerate(row.get('tableCells', [])):
                            if col_idx >= len(table_data[row_idx]):
                                break

                            cell_content = cell.get('content', [])
                            if cell_content:
                                cell_start = cell_content[0].get('startIndex', 0)
                                cell_text = table_data[row_idx][col_idx]
                                # 볼드 마크다운 제거
                                cell_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell_text)
                                if cell_text:
                                    cell_requests.append({
                                        'insertText': {
                                            'location': {'index': cell_start},
                                            'text': cell_text
                                        }
                                    })

                    if cell_requests:
                        cell_requests.reverse()
                        try:
                            docs_service.documents().batchUpdate(
                                documentId=doc_id,
                                body={'requests': cell_requests}
                            ).execute()
                        except Exception as e:
                            print(f"  셀 내용 삽입 실패: {e}")

                    return True

            return False

    return False


def main():
    print("=" * 70)
    print("03-content-strategy.md → Google Docs 마이그레이션")
    print("=" * 70)

    # 1. 인증
    print("\n[1/6] Google API 인증...")
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 2. 마크다운 읽기
    print("\n[2/6] 마크다운 파일 읽기...")
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()
    print(f"  원본: {len(md_content):,} 문자, {len(md_content.splitlines())} 줄")

    # 이미지 URL 확인
    image_urls = extract_image_urls(md_content)
    print(f"  이미지: {len(image_urls)}개 감지")

    # 3. 구조화
    print("\n[3/6] 마크다운 구조 분석...")
    structure = convert_markdown_to_structure(md_content)

    type_counts = {}
    for item in structure:
        t = item['type']
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"  총 {len(structure)}개 요소:")
    for t, count in sorted(type_counts.items()):
        print(f"    - {t}: {count}개")

    # 4. 문서 초기화
    print("\n[4/6] 기존 문서 초기화...")
    clear_document(docs_service, DOC_ID)
    print("  문서 내용 삭제 완료")

    # 5. 텍스트 빌드 및 삽입
    print("\n[5/6] 콘텐츠 변환 및 삽입...")
    text_content, style_ranges, table_placeholders, image_placeholders = build_insert_requests(structure)

    print(f"  텍스트: {len(text_content):,} 문자")
    print(f"  스타일 범위: {len(style_ranges)}개")
    print(f"  테이블: {len(table_placeholders)}개")
    print(f"  이미지: {len(image_placeholders)}개")

    # 텍스트 삽입
    docs_service.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': [{
            'insertText': {
                'location': {'index': 1},
                'text': text_content
            }
        }]}
    ).execute()
    print("  텍스트 삽입 완료")

    # 헤딩 스타일 적용
    print("  헤딩 스타일 적용 중...")
    apply_heading_styles(docs_service, DOC_ID, style_ranges)

    # 6. 테이블 및 이미지 삽입 (역순)
    print("\n[6/6] 테이블 및 이미지 삽입...")

    # 이미지 삽입 (역순)
    print(f"  이미지 {len(image_placeholders)}개 처리 중...")
    for idx in range(len(image_placeholders) - 1, -1, -1):
        _, url = image_placeholders[idx]
        placeholder = f"[IMAGE_PLACEHOLDER_{idx}]"
        if insert_image_at_placeholder(docs_service, DOC_ID, placeholder, url):
            print(f"    [OK] 이미지 {idx + 1}/{len(image_placeholders)}")
        else:
            print(f"    [FAIL] 이미지 {idx + 1} 실패")
        time.sleep(0.5)

    # 테이블 삽입 (역순)
    print(f"  테이블 {len(table_placeholders)}개 처리 중...")
    for idx in range(len(table_placeholders) - 1, -1, -1):
        _, table_data = table_placeholders[idx]
        placeholder = f"[TABLE_PLACEHOLDER_{idx}]"
        if insert_table_at_placeholder(docs_service, DOC_ID, placeholder, table_data):
            print(f"    [OK] 테이블 {idx + 1}/{len(table_placeholders)}")
        else:
            print(f"    [FAIL] 테이블 {idx + 1} 실패")
        time.sleep(0.5)

    # 완료
    print()
    print("=" * 70)
    print("마이그레이션 완료!")
    print(f"  문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 70)


if __name__ == "__main__":
    main()
