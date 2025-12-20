"""
경영진 발표용 Google Docs 생성
- 이미지 중심의 시각적 문서
- 핵심 메시지만 전달
- 프로페셔널 디자인
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '1431Dz71jRV78o6-bwgR6sVM573bnGKf9-9Ozyo6hKpg'
# content-strategy 서브폴더
FOLDER_ID = '1NqPboT9HsAfF2XPI9Xfot-nc0wcVA2uR'

# 이미지 파일 경로
IMAGE_DIR = r'D:\AI\claude01\wsoptv_v2\docs\wireframes\v2'
IMAGES = {
    'content_composition': 'cs-content-composition.png',
    'youtube_vs_wsoptv': 'cs-youtube-vs-wsoptv.png',
    'season_calendar': 'cs-season-calendar.png',
    'bracelet_structure': 'cs-bracelet-structure.png',
    'main_event': 'cs-main-event.png',
    'curation_roadmap': 'cs-curation-roadmap.png',
    'content_pie': 'cs-content-pie.png',
    'content_detail': 'cs-content-detail.png',
}


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


def upload_image_to_drive(drive_service, file_path, folder_id):
    """이미지를 Google Drive에 업로드하고 공유 링크 반환"""
    file_name = os.path.basename(file_path)

    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }

    media = MediaFileUpload(file_path, mimetype='image/png')

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webContentLink'
    ).execute()

    # 공개 읽기 권한 설정
    drive_service.permissions().create(
        fileId=file['id'],
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    print(f"업로드 완료: {file_name} -> {file['id']}")
    return file['id']


def get_executive_content():
    """경영진 발표용 콘텐츠"""
    return '''WSOPTV
콘텐츠 전략

Version 4.0 | Executive Summary


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



포커의 50년 역사
하나의 플랫폼으로

18TB+ 아카이브  |  1973년~현재  |  세계 유일 WSOP 공식 OTT



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



핵심 지표

아카이브 규모
18TB+
50년 역사

연간 콘텐츠
80+
브레이슬릿 이벤트

메인 이벤트 참가자
10,000+
2024 기준

최대 우승 상금
$12.1M
2023 기록



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



왜 WSOP인가?



브레이슬릿의 가치

"WSOP 브레이슬릿은 포커의 올림픽 금메달이다."

포커 커뮤니티의 위상은 브레이슬릿 보유 여부로 결정됩니다.



역대 레전드

Phil Hellmuth — 17개 (역대 최다)
Phil Ivey — 11개
Doyle Brunson — 10개
Johnny Chan — 10개
Daniel Negreanu — 7개



Moneymaker Effect

2003년, $86 온라인 예선 → $2.5M 우승

참가자 성장: 839명(2003) → 10,117명(2024)
12배 성장!



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



콘텐츠 구성

[이미지: 콘텐츠 구성 차트]



WSOP Las Vegas — 80%
Main Event, Bracelet Events, Best Hands

기타 대회 — 10%
Paradise, Europe, Circuit

오리지널 — 10%
Game of Gold, Documentary



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



콘텐츠 상세

[이미지: 콘텐츠 상세 차트]



Main Event (35%)
$10,000 No-Limit Hold'em Championship
• 참가자: 10,000명+
• 우승 상금: $10M+

Bracelet Events (30%)
80+ 독립 챔피언십
• NLH, PLO, Mixed Games
• 각 분야 세계 최강자 결정

Best Hands (15%)
50년 역사 명장면 큐레이션
• All-in Showdowns
• Monster Pots



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



YouTube vs WSOPTV

[이미지: YouTube vs WSOPTV 비교]



투트랙 전략

"YouTube는 미끼, WSOPTV는 풀코스"



YouTube (무료)
관심 유도 & 유입
• 생방송
• 쇼츠/클립

WSOPTV (구독)
깊이 있는 경험
• 풀 에피소드
• Hand Skip
• Best Hands
• 4K Remaster



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



WSOPTV 독점 기능



Hand Skip
3시간 → 45분
핵심 핸드만 시청

Best Hands
50년 역사
극적인 순간 큐레이션

4K Remaster
SD → 4K
클래식 영상 복원



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



연간 캘린더

[이미지: 시즌 캘린더]



5월~7월
WSOP Las Vegas
연간 콘텐츠 80%

피크 시즌 콘텐츠
• 주당 15~20개 에피소드
• 총 150~160개 풀 에피소드
• Hand Skip 버전 별도 제작



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



글로벌 확장 로드맵



2026
아시아 진출
• WSOP Asia (마카오)
• WSOP Philippines

2027
신흥 시장
• WSOP Brazil
• WSOP India
• WSOP Australia

2028+
365일 글로벌 콘텐츠



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



서비스 진화 로드맵

[이미지: 로드맵]



Phase 1 — MVP
전체 볼륨 OTT
이어보기

Phase 2 — 개인화
프로필 추천
카테고리 추천

Phase 3 — 차별화
Hand Skip
Best Hands

Phase 4 — 프리미엄
4K Remaster
독점 다큐



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



아카이브 시대 구분



CLASSIC (1973-2002)
포커 초창기
희귀 영상, 전설의 탄생

BOOM (2003-2010)
Moneymaker 황금기
산업 혁명, 전환점

HD (2011-2025)
현대 포커 시대
고화질 풀 에피소드

WSOPTV (2026~)
플랫폼 시대
독점 오리지널 콘텐츠



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



결론



WSOPTV는 50년 포커 역사를 담은
세계 유일의 통합 아카이브입니다.



핵심 가치

18TB+
유일무이한 아카이브

80%
WSOP Las Vegas 독점

4단계
체계적 서비스 진화

글로벌
365일 콘텐츠 확장



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



감사합니다

WSOPTV
'''


def main():
    print("=" * 60)
    print("경영진 발표용 Google Docs 생성")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # 1. 문서 비우기
    doc = docs_service.documents().get(documentId=DOC_ID).execute()
    content = doc.get('body', {}).get('content', [])
    if content:
        end_index = content[-1].get('endIndex', 1) - 1
        if end_index > 1:
            docs_service.documents().batchUpdate(
                documentId=DOC_ID,
                body={'requests': [{'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index}}}]}
            ).execute()
    print("문서 비우기 완료")

    # 2. 이미지 업로드
    print("\n이미지 업로드 중...")
    image_ids = {}
    for key, filename in IMAGES.items():
        file_path = os.path.join(IMAGE_DIR, filename)
        if os.path.exists(file_path):
            image_ids[key] = upload_image_to_drive(drive_service, file_path, FOLDER_ID)
        else:
            print(f"파일 없음: {file_path}")

    # 3. 콘텐츠 삽입
    content_text = get_executive_content()
    print(f"\n콘텐츠 길이: {len(content_text)} 문자")

    docs_service.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': [{'insertText': {'location': {'index': 1}, 'text': content_text}}]}
    ).execute()
    print("텍스트 삽입 완료")

    # 4. 스타일 적용
    apply_executive_styles(docs_service, DOC_ID)

    # 5. 이미지 삽입
    print("\n이미지 삽입 중...")
    insert_images(docs_service, DOC_ID, image_ids)

    print("\n" + "=" * 60)
    print("완료!")
    print(f"문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


def apply_executive_styles(docs_service, doc_id):
    """경영진 발표용 스타일 적용"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    requests = []

    for element in content:
        if 'paragraph' not in element:
            continue

        paragraph = element['paragraph']
        elements = paragraph.get('elements', [])
        if not elements:
            continue

        text = ''
        for elem in elements:
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')
        text = text.strip()

        if not text:
            continue

        start_index = element['startIndex']
        end_index = element['endIndex']

        # TITLE
        if text == 'WSOPTV':
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start_index, 'endIndex': end_index},
                    'paragraphStyle': {'namedStyleType': 'TITLE', 'alignment': 'CENTER'},
                    'fields': 'namedStyleType,alignment'
                }
            })

        # SUBTITLE
        elif text in ['콘텐츠 전략', '포커의 50년 역사', '하나의 플랫폼으로']:
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start_index, 'endIndex': end_index},
                    'paragraphStyle': {'namedStyleType': 'SUBTITLE', 'alignment': 'CENTER'},
                    'fields': 'namedStyleType,alignment'
                }
            })

        # HEADING_1: 주요 섹션
        elif text in ['핵심 지표', '왜 WSOP인가?', '콘텐츠 구성', '콘텐츠 상세',
                     'YouTube vs WSOPTV', 'WSOPTV 독점 기능', '연간 캘린더',
                     '글로벌 확장 로드맵', '서비스 진화 로드맵', '아카이브 시대 구분',
                     '결론', '감사합니다']:
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start_index, 'endIndex': end_index},
                    'paragraphStyle': {'namedStyleType': 'HEADING_1', 'alignment': 'CENTER'},
                    'fields': 'namedStyleType,alignment'
                }
            })

        # HEADING_2: 하위 섹션
        elif text in ['브레이슬릿의 가치', '역대 레전드', 'Moneymaker Effect',
                     '투트랙 전략', '핵심 가치', '2026', '2027', '2028+']:
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start_index, 'endIndex': end_index},
                    'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                    'fields': 'namedStyleType'
                }
            })

        # HEADING_3: 상세 항목
        elif text in ['Hand Skip', 'Best Hands', '4K Remaster',
                     'CLASSIC (1973-2002)', 'BOOM (2003-2010)', 'HD (2011-2025)', 'WSOPTV (2026~)',
                     'Phase 1 — MVP', 'Phase 2 — 개인화', 'Phase 3 — 차별화', 'Phase 4 — 프리미엄',
                     'YouTube (무료)', 'WSOPTV (구독)',
                     'WSOP Las Vegas — 80%', '기타 대회 — 10%', '오리지널 — 10%',
                     'Main Event (35%)', 'Bracelet Events (30%)', 'Best Hands (15%)',
                     '5월~7월', '피크 시즌 콘텐츠', '아시아 진출', '신흥 시장', '365일 글로벌 콘텐츠']:
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start_index, 'endIndex': end_index},
                    'paragraphStyle': {'namedStyleType': 'HEADING_3'},
                    'fields': 'namedStyleType'
                }
            })

        # 중앙 정렬 텍스트
        elif text.startswith('18TB+') or text.startswith('Version') or text.startswith('"'):
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start_index, 'endIndex': end_index},
                    'paragraphStyle': {'alignment': 'CENTER'},
                    'fields': 'alignment'
                }
            })

        # 큰 숫자 (지표)
        elif text in ['18TB+', '80+', '10,000+', '$12.1M', '3시간 → 45분', '50년 역사', 'SD → 4K',
                     '80%', '4단계', '글로벌']:
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': start_index, 'endIndex': end_index - 1},
                    'textStyle': {'bold': True, 'fontSize': {'magnitude': 18, 'unit': 'PT'}},
                    'fields': 'bold,fontSize'
                }
            })

    if requests:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        print(f"스타일 적용: {len(requests)}개")


def insert_images(docs_service, doc_id, image_ids):
    """이미지 삽입 (플레이스홀더 위치에)"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    requests = []
    image_mapping = {
        '[이미지: 콘텐츠 구성 차트]': 'content_composition',
        '[이미지: 콘텐츠 상세 차트]': 'content_detail',
        '[이미지: YouTube vs WSOPTV 비교]': 'youtube_vs_wsoptv',
        '[이미지: 시즌 캘린더]': 'season_calendar',
        '[이미지: 로드맵]': 'curation_roadmap',
    }

    for element in content:
        if 'paragraph' not in element:
            continue

        paragraph = element['paragraph']
        elements = paragraph.get('elements', [])
        if not elements:
            continue

        text = ''
        for elem in elements:
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')
        text = text.strip()

        # 플레이스홀더 찾기
        if text in image_mapping:
            image_key = image_mapping[text]
            if image_key in image_ids:
                start_index = element['startIndex']
                end_index = element['endIndex']

                # 텍스트 삭제 후 이미지 삽입
                requests.append({
                    'deleteContentRange': {
                        'range': {'startIndex': start_index, 'endIndex': end_index - 1}
                    }
                })
                requests.append({
                    'insertInlineImage': {
                        'location': {'index': start_index},
                        'uri': f'https://drive.google.com/uc?id={image_ids[image_key]}',
                        'objectSize': {
                            'width': {'magnitude': 500, 'unit': 'PT'},
                            'height': {'magnitude': 300, 'unit': 'PT'}
                        }
                    }
                })

    if requests:
        # 역순으로 실행 (인덱스 꼬임 방지)
        for i in range(0, len(requests), 2):
            try:
                batch = requests[i:i+2]
                batch.reverse()
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': batch}
                ).execute()
            except Exception as e:
                print(f"이미지 삽입 오류: {e}")
        print(f"이미지 삽입 시도: {len(requests) // 2}개")


if __name__ == "__main__":
    main()
