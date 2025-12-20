"""
콘텐츠 전략 문서 (03-content-strategy-gdocs.md) Google Docs 이미지 삽입 스크립트
18개의 Mermaid 다이어그램 PNG 이미지를 Google Docs에 삽입합니다.
"""

import os
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

# 콘텐츠 전략 Google Docs ID
DOC_ID = '150uymfx3hYZaXF6yzmU6WghAXMt6RXocMCZth0R0z8k'

# 이미지 저장 폴더 (Google Drive - content-strategy 서브폴더)
# 루트: https://drive.google.com/drive/folders/19Sbq1_K-fJOEN2LnMEaMTE9fYjAEFoou
FOLDER_ID = '1NqPboT9HsAfF2XPI9Xfot-nc0wcVA2uR'

# 이미지 디렉토리
IMAGE_DIR = r'D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\images'

# 이미지-섹션 매핑 (삽입할 위치의 앵커 텍스트)
# 앵커 텍스트 뒤에 이미지가 삽입됩니다
IMAGE_MAPPINGS = [
    {
        'filename': '01-mindmap-core-metrics.png',
        'anchor': '최대 우승 상금',  # 핵심 지표 테이블 뒤
        'section': 'Executive Summary',
        'width': 468,
        'height': 350
    },
    {
        'filename': '02-xychart-bracelet-legends.png',
        'anchor': '역대 브레이슬릿 레전드',
        'section': '1.1 브레이슬릿의 무게',
        'width': 468,
        'height': 280
    },
    {
        'filename': '03-journey-moneymaker.png',
        'anchor': 'Moneymaker의 여정',
        'section': '1.2 Moneymaker Effect',
        'width': 468,
        'height': 300
    },
    {
        'filename': '04-xychart-participants.png',
        'anchor': '12배 성장',
        'section': '1.2 Moneymaker Effect - 참가자',
        'width': 468,
        'height': 280
    },
    {
        'filename': '05-pie-content-composition.png',
        'anchor': '전체 콘텐츠 구성',
        'section': '2.1 콘텐츠 구성 비율',
        'width': 400,
        'height': 300
    },
    {
        'filename': '06-pie-wsop-lv-content.png',
        'anchor': 'WSOP Las Vegas 콘텐츠 내역',
        'section': '2.2 WSOP Las Vegas 상세',
        'width': 400,
        'height': 300
    },
    {
        'filename': '07-flowchart-main-event.png',
        'anchor': '토너먼트 구조',
        'section': '2.2 Main Event (35%)',
        'width': 468,
        'height': 200
    },
    {
        'filename': '08-flowchart-bracelet-events.png',
        'anchor': '80개 이상의 독립 챔피언십',
        'section': '2.2 Bracelet Events (30%)',
        'width': 468,
        'height': 350
    },
    {
        'filename': '09-flowchart-best-hands.png',
        'anchor': 'Best Hands 큐레이션',
        'section': '2.2 Best Hands 큐레이션',
        'width': 468,
        'height': 200
    },
    {
        'filename': '10-flowchart-other-events.png',
        'anchor': '2.3 기타 대회',
        'section': '2.3 기타 대회',
        'width': 468,
        'height': 250
    },
    {
        'filename': '11-flowchart-youtube-vs-wsoptv.png',
        'anchor': '콘텐츠 전환 흐름',
        'section': '3.1 투트랙 전략',
        'width': 468,
        'height': 280
    },
    {
        'filename': '12-flowchart-exclusive-features.png',
        'anchor': '3.3 WSOPTV 독점 기능 상세',
        'section': '3.3 WSOPTV 독점 기능 상세',
        'width': 468,
        'height': 250
    },
    {
        'filename': '13-pie-best-hands-criteria.png',
        'anchor': '선정 기준 가중치',
        'section': '3.3 Best Hands 컬렉션',
        'width': 400,
        'height': 300
    },
    {
        'filename': '14-gantt-annual-calendar.png',
        'anchor': '연간 콘텐츠 캘린더',
        'section': '4.1 연간 시즌 구조',
        'width': 468,
        'height': 280
    },
    {
        'filename': '15-timeline-global-expansion.png',
        'anchor': '4.4 글로벌 확장 로드맵 (2026~)',
        'section': '4.4 글로벌 확장 로드맵',
        'width': 468,
        'height': 200
    },
    {
        'filename': '16-timeline-service-evolution.png',
        'anchor': '5.1 4단계 진화',
        'section': '5.1 4단계 진화',
        'width': 468,
        'height': 250
    },
    {
        'filename': '17-quadrant-feature-phases.png',
        'anchor': '5.2 Feature Matrix',
        'section': '5.2 Feature Matrix',
        'width': 400,
        'height': 350
    },
    {
        'filename': '18-timeline-archive-eras.png',
        'anchor': '6.1 시대 타임라인',
        'section': '6.1 시대 타임라인',
        'width': 468,
        'height': 250
    }
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


def upload_to_drive(drive_service, file_path, folder_id):
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
        drive_service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"  기존 파일 업데이트: {file_name}")
    else:
        # 새 파일 업로드
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='image/png')
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        file_id = file['id']
        print(f"  새 파일 업로드: {file_name}")

    # 공개 권한 설정
    try:
        drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
    except:
        pass  # 이미 공개 상태

    return f"https://drive.google.com/uc?export=view&id={file_id}"


def get_document_content(docs_service, doc_id):
    """문서 내용 가져오기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    return doc


def find_text_position(doc, search_text):
    """문서에서 특정 텍스트의 위치 찾기"""
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'paragraph' not in element:
            continue

        paragraph = element['paragraph']
        elements = paragraph.get('elements', [])

        text = ''
        for elem in elements:
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')

        if search_text in text:
            return {
                'start': element['startIndex'],
                'end': element['endIndex'],
                'text': text.strip()
            }

    return None


def insert_image_at_position(docs_service, doc_id, position, image_url, width, height):
    """특정 위치에 이미지 삽입"""
    requests = [
        # 1. 플레이스홀더 텍스트 삭제
        {
            'deleteContentRange': {
                'range': {
                    'startIndex': position['start'],
                    'endIndex': position['end'] - 1
                }
            }
        },
        # 2. 이미지 삽입
        {
            'insertInlineImage': {
                'location': {'index': position['start']},
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


def insert_image_at_end_of_section(docs_service, doc_id, section_text, image_url, width, height):
    """섹션 끝에 이미지 삽입 (플레이스홀더가 없는 경우)"""
    doc = get_document_content(docs_service, doc_id)
    position = find_text_position(doc, section_text)

    if position:
        # 섹션 다음 줄에 이미지 삽입
        insert_index = position['end']

        requests = [
            # 새 줄 추가
            {
                'insertText': {
                    'location': {'index': insert_index},
                    'text': '\n'
                }
            },
            # 이미지 삽입
            {
                'insertInlineImage': {
                    'location': {'index': insert_index + 1},
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
        return True
    return False


def main():
    """메인 실행"""
    print("=" * 60)
    print("콘텐츠 전략 문서 이미지 삽입")
    print("=" * 60)
    print(f"문서 ID: {DOC_ID}")
    print(f"이미지 수: {len(IMAGE_MAPPINGS)}개")
    print()

    # 인증
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # 이미지 업로드 및 URL 획득
    print("Phase 1: 이미지 업로드 중...")
    image_urls = {}

    for mapping in IMAGE_MAPPINGS:
        file_path = os.path.join(IMAGE_DIR, mapping['filename'])
        if os.path.exists(file_path):
            url = upload_to_drive(drive_service, file_path, FOLDER_ID)
            image_urls[mapping['filename']] = url
        else:
            print(f"  파일 없음: {file_path}")

    print(f"\n업로드 완료: {len(image_urls)}개")

    # 문서에 이미지 삽입
    print("\nPhase 2: 문서에 이미지 삽입 중...")

    # 플레이스홀더 찾아서 역순으로 처리 (인덱스 꼬임 방지)
    doc = get_document_content(docs_service, DOC_ID)

    successful = 0
    failed = 0

    # 역순으로 처리 (인덱스 꼬임 방지)
    for mapping in reversed(IMAGE_MAPPINGS):
        filename = mapping['filename']
        anchor = mapping['anchor']  # anchor 필드 사용
        section = mapping['section']
        width = mapping['width']
        height = mapping['height']

        if filename not in image_urls:
            print(f"  SKIP: {filename} (URL 없음)")
            failed += 1
            continue

        url = image_urls[filename]

        # 앵커 텍스트 위치 찾기
        position = find_text_position(doc, anchor)

        if position:
            try:
                # 앵커 텍스트 뒤에 이미지 삽입
                insert_image_at_end_of_section(docs_service, DOC_ID, anchor, url, width, height)
                print(f"  OK: {filename} → {section}")
                successful += 1
                # 문서 다시 로드 (인덱스 변경됨)
                doc = get_document_content(docs_service, DOC_ID)
            except Exception as e:
                print(f"  FAIL: {filename} - {e}")
                failed += 1
        else:
            print(f"  SKIP: {filename} (앵커 없음: {anchor})")
            failed += 1

    print()
    print("=" * 60)
    print(f"완료: 성공 {successful}개, 실패 {failed}개")
    print(f"문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
