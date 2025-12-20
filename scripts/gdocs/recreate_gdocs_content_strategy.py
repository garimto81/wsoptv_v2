"""
Google Docs 콘텐츠 전략 문서 재생성 스크립트
- 마크다운 테이블 → Google Docs 네이티브 테이블 변환
- 이미지 중복 없이 정확히 18개 삽입
- Issue #7 해결
"""

import os
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Google API 설정
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'

# 문서 설정
DOC_ID = '150uymfx3hYZaXF6yzmU6WghAXMt6RXocMCZth0R0z8k'
MD_FILE = r'D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\03-content-strategy-gdocs.md'
IMAGE_DIR = r'D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\images'
# Google Drive 이미지 저장 위치 (새 폴더 구조)
# 루트: https://drive.google.com/drive/folders/19Sbq1_K-fJOEN2LnMEaMTE9fYjAEFoou
DRIVE_FOLDER_ID = '1NqPboT9HsAfF2XPI9Xfot-nc0wcVA2uR'  # content-strategy 서브폴더

# 이미지-앵커 매핑 (정확히 18개)
IMAGE_MAPPINGS = [
    {'filename': '01-mindmap-core-metrics.png', 'anchor': '최대 우승 상금'},
    {'filename': '02-xychart-bracelet-legends.png', 'anchor': '역대 브레이슬릿 레전드'},
    {'filename': '03-journey-moneymaker.png', 'anchor': 'Moneymaker의 여정'},
    {'filename': '04-xychart-participants.png', 'anchor': '12배 성장'},
    {'filename': '05-pie-content-composition.png', 'anchor': '전체 콘텐츠 구성'},
    {'filename': '06-pie-wsop-lv-content.png', 'anchor': 'WSOP Las Vegas 콘텐츠 내역'},
    {'filename': '07-flowchart-main-event.png', 'anchor': '토너먼트 구조'},
    {'filename': '08-flowchart-bracelet-events.png', 'anchor': '80개 이상의 독립 챔피언십'},
    {'filename': '09-flowchart-best-hands.png', 'anchor': 'Best Hands 큐레이션'},
    {'filename': '10-flowchart-other-events.png', 'anchor': '2.3 기타 대회'},
    {'filename': '11-flowchart-youtube-vs-wsoptv.png', 'anchor': '콘텐츠 전환 흐름'},
    {'filename': '12-flowchart-exclusive-features.png', 'anchor': '3.3 WSOPTV 독점 기능 상세'},
    {'filename': '13-pie-best-hands-criteria.png', 'anchor': '선정 기준 가중치'},
    {'filename': '14-gantt-annual-calendar.png', 'anchor': '연간 콘텐츠 캘린더'},
    {'filename': '15-timeline-global-expansion.png', 'anchor': '4.4 글로벌 확장 로드맵 (2026~)'},
    {'filename': '16-timeline-service-evolution.png', 'anchor': '5.1 4단계 진화'},
    {'filename': '17-quadrant-feature-phases.png', 'anchor': '5.2 Feature Matrix'},
    {'filename': '18-timeline-archive-eras.png', 'anchor': '6.1 시대 타임라인'},
]


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


def upload_image_to_drive(drive_service, file_path, folder_id):
    """이미지를 Drive에 업로드하고 공개 URL 반환"""
    file_name = os.path.basename(file_path)

    # 기존 파일 검색
    results = drive_service.files().list(
        q=f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
        fields="files(id)"
    ).execute()

    files = results.get('files', [])

    if files:
        file_id = files[0]['id']
        # 기존 파일 업데이트
        media = MediaFileUpload(file_path, mimetype='image/png')
        drive_service.files().update(fileId=file_id, media_body=media).execute()
    else:
        # 새 파일 업로드
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, mimetype='image/png')
        file = drive_service.files().create(
            body=file_metadata, media_body=media, fields='id'
        ).execute()
        file_id = file['id']

        # 공개 권한 설정
        try:
            drive_service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
        except Exception:
            pass

    return f"https://drive.google.com/uc?export=view&id={file_id}"


def parse_markdown_table(lines):
    """마크다운 테이블을 파싱하여 2D 배열로 반환"""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            continue
        # 구분자 라인 스킵
        if re.match(r'^\|[\s\-:|]+\|$', line):
            continue
        # 셀 추출
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if cells and any(c for c in cells):
            rows.append(cells)
    return rows


def convert_md_to_content(md_content):
    """
    마크다운을 변환하여 텍스트와 테이블 정보를 분리
    테이블 위치에는 플레이스홀더 삽입
    """
    lines = md_content.split('\n')
    result_lines = []
    tables = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # 테이블 시작 감지 (| 로 시작)
        if line.strip().startswith('|') and i + 1 < len(lines):
            # 테이블 라인들 수집
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1

            # 테이블 파싱
            table_data = parse_markdown_table(table_lines)
            if table_data and len(table_data) > 0:
                # 플레이스홀더 추가
                placeholder = f"__TABLE_{len(tables)}__"
                result_lines.append(placeholder)
                tables.append(table_data)
            continue

        # 마크다운 헤딩 변환
        if line.startswith('####'):
            result_lines.append(line[5:].strip())
        elif line.startswith('###'):
            result_lines.append(line[4:].strip())
        elif line.startswith('##'):
            result_lines.append(line[3:].strip())
        elif line.startswith('#'):
            result_lines.append(line[2:].strip())
        # 볼드 제거
        elif '**' in line:
            result_lines.append(re.sub(r'\*\*([^*]+)\*\*', r'\1', line))
        # 인용문 제거
        elif line.startswith('>'):
            result_lines.append(line[1:].strip())
        # 수평선 스킵
        elif line.strip() == '---':
            pass
        # HTML 태그 스킵
        elif '<div' in line or '</div>' in line:
            pass
        # 마크다운 링크 변환
        elif '[' in line and '](' in line:
            result_lines.append(re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', line))
        else:
            result_lines.append(line)

        i += 1

    return '\n'.join(result_lines), tables


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
            print("  기존 문서 내용 삭제 완료")


def insert_text(docs_service, doc_id, text):
    """텍스트 삽입"""
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{
            'insertText': {
                'location': {'index': 1},
                'text': text
            }
        }]}
    ).execute()


def find_placeholder_positions(docs_service, doc_id, num_tables):
    """플레이스홀더 위치 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    positions = {}

    for element in content:
        if 'paragraph' not in element:
            continue
        para = element['paragraph']
        text = ''
        for elem in para.get('elements', []):
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')

        for i in range(num_tables):
            placeholder = f"__TABLE_{i}__"
            if placeholder in text:
                positions[i] = {
                    'start': element['startIndex'],
                    'end': element['endIndex'],
                    'text': text.strip()
                }

    return positions


def insert_table_at_position(docs_service, doc_id, position, table_data):
    """테이블을 특정 위치에 삽입"""
    if not table_data or len(table_data) == 0:
        return

    num_rows = len(table_data)
    num_cols = len(table_data[0]) if table_data else 0

    if num_cols == 0:
        return

    requests = []

    # 1. 플레이스홀더 삭제
    requests.append({
        'deleteContentRange': {
            'range': {
                'startIndex': position['start'],
                'endIndex': position['end'] - 1
            }
        }
    })

    # 2. 테이블 삽입
    requests.append({
        'insertTable': {
            'rows': num_rows,
            'columns': num_cols,
            'location': {'index': position['start']}
        }
    })

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()

    # 3. 문서 다시 로드하여 테이블 셀 찾기
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    # 테이블 찾기
    for element in content:
        if 'table' in element:
            table = element['table']
            start_idx = element.get('startIndex', 0)

            # 위치 확인 (대략적으로)
            if abs(start_idx - position['start']) < 50:
                # 셀에 데이터 삽입
                cell_requests = []
                table_rows = table.get('tableRows', [])

                for row_idx, row in enumerate(table_rows):
                    if row_idx >= len(table_data):
                        break
                    cells = row.get('tableCells', [])
                    for col_idx, cell in enumerate(cells):
                        if col_idx >= len(table_data[row_idx]):
                            break

                        cell_content = cell.get('content', [])
                        if cell_content:
                            cell_start = cell_content[0].get('startIndex', 0)
                            cell_text = table_data[row_idx][col_idx]
                            if cell_text:
                                cell_requests.append({
                                    'insertText': {
                                        'location': {'index': cell_start},
                                        'text': cell_text
                                    }
                                })

                if cell_requests:
                    # 역순으로 삽입 (인덱스 꼬임 방지)
                    cell_requests.reverse()
                    docs_service.documents().batchUpdate(
                        documentId=doc_id,
                        body={'requests': cell_requests}
                    ).execute()

                return


def find_anchor_position(docs_service, doc_id, anchor_text):
    """앵커 텍스트 위치 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'paragraph' not in element:
            continue
        para = element['paragraph']
        text = ''
        for elem in para.get('elements', []):
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')

        if anchor_text in text:
            return element['endIndex']

    return None


def insert_image(docs_service, doc_id, position, image_url, width=468, height=300):
    """이미지 삽입"""
    requests = [
        {
            'insertText': {
                'location': {'index': position},
                'text': '\n'
            }
        },
        {
            'insertInlineImage': {
                'location': {'index': position + 1},
                'uri': image_url,
                'objectSize': {
                    'width': {'magnitude': width, 'unit': 'PT'},
                    'height': {'magnitude': height, 'unit': 'PT'}
                }
            }
        }
    ]

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()


def main():
    print("=" * 60)
    print("Google Docs 콘텐츠 전략 문서 재생성")
    print("Issue #7: 이미지 중복 + 테이블 미렌더링 해결")
    print("=" * 60)

    # 인증
    print("\n[1/5] Google API 인증...")
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # 마크다운 읽기
    print("\n[2/5] 마크다운 파일 읽기...")
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()
    print(f"  원본: {len(md_content):,} 문자")

    # 마크다운 변환 (테이블 분리)
    print("\n[3/5] 마크다운 변환 (테이블 분리)...")
    text_content, tables = convert_md_to_content(md_content)
    print(f"  텍스트: {len(text_content):,} 문자")
    print(f"  테이블: {len(tables)}개")

    # 문서 재생성
    print("\n[4/5] 문서 재생성...")

    # 4-1. 기존 내용 삭제
    print("  기존 내용 삭제 중...")
    clear_document(docs_service, DOC_ID)

    # 4-2. 텍스트 삽입
    print("  텍스트 삽입 중...")
    insert_text(docs_service, DOC_ID, text_content)

    # 4-3. 테이블 삽입 (역순으로)
    print(f"  테이블 {len(tables)}개 삽입 중...")
    positions = find_placeholder_positions(docs_service, DOC_ID, len(tables))

    # 역순으로 처리 (인덱스 꼬임 방지)
    for i in range(len(tables) - 1, -1, -1):
        if i in positions:
            try:
                insert_table_at_position(docs_service, DOC_ID, positions[i], tables[i])
                print(f"    테이블 {i+1}/{len(tables)} 삽입 완료")
            except Exception as e:
                print(f"    테이블 {i+1} 삽입 실패: {e}")

    # 이미지 삽입
    print(f"\n[5/5] 이미지 {len(IMAGE_MAPPINGS)}개 삽입...")

    # 이미지 업로드
    image_urls = {}
    for mapping in IMAGE_MAPPINGS:
        file_path = os.path.join(IMAGE_DIR, mapping['filename'])
        if os.path.exists(file_path):
            url = upload_image_to_drive(drive_service, file_path, DRIVE_FOLDER_ID)
            image_urls[mapping['filename']] = url
            print(f"  업로드: {mapping['filename']}")

    # 이미지 삽입 (역순)
    inserted = 0
    for mapping in reversed(IMAGE_MAPPINGS):
        filename = mapping['filename']
        anchor = mapping['anchor']

        if filename not in image_urls:
            continue

        position = find_anchor_position(docs_service, DOC_ID, anchor)
        if position:
            try:
                insert_image(docs_service, DOC_ID, position, image_urls[filename])
                inserted += 1
                print(f"  삽입: {filename}")
            except Exception as e:
                print(f"  실패: {filename} - {e}")

    print()
    print("=" * 60)
    print(f"완료!")
    print(f"  테이블: {len(tables)}개 변환")
    print(f"  이미지: {inserted}/18개 삽입")
    print(f"  문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
