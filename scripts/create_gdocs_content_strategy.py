"""
Google Docs에 WSOPTV 콘텐츠 전략 문서 생성
OAuth 2.0 인증 사용 (파일 업로드/생성 필요)
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# OAuth 설정
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

# 절대 경로 사용
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'

# WSOPTV 공유 폴더 ID (새 폴더 구조)
# 루트: https://drive.google.com/drive/folders/19Sbq1_K-fJOEN2LnMEaMTE9fYjAEFoou
WSOPTV_FOLDER_ID = '1NqPboT9HsAfF2XPI9Xfot-nc0wcVA2uR'  # content-strategy 서브폴더


def get_credentials():
    """OAuth 2.0 인증 처리"""
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


def create_google_doc(title: str, folder_id: str = None):
    """Google Doc 생성"""
    creds = get_credentials()

    # Docs API 서비스 생성
    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # 문서 생성
    document = docs_service.documents().create(body={'title': title}).execute()
    doc_id = document.get('documentId')
    print(f"문서 생성 완료: {title}")
    print(f"문서 ID: {doc_id}")

    # 폴더로 이동
    if folder_id:
        # 현재 부모 가져오기
        file = drive_service.files().get(fileId=doc_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))

        # 새 폴더로 이동
        drive_service.files().update(
            fileId=doc_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        print(f"폴더로 이동 완료: {folder_id}")

    return doc_id, docs_service


def add_content_to_doc(doc_id: str, docs_service):
    """문서에 콘텐츠 추가"""

    # Google Docs API 요청 배열
    requests = []

    # 인덱스 추적 (끝에서부터 역순으로 삽입하므로 1부터 시작)
    index = 1

    # === 제목 ===
    requests.append({
        'insertText': {
            'location': {'index': index},
            'text': 'WSOPTV 콘텐츠 전략\n'
        }
    })
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + 18},
            'paragraphStyle': {'namedStyleType': 'TITLE'},
            'fields': 'namedStyleType'
        }
    })
    index += 19

    # === 버전 정보 ===
    version_text = 'Version: 4.0.0 | Google Docs 최적화 버전\n\n'
    requests.append({
        'insertText': {
            'location': {'index': index},
            'text': version_text
        }
    })
    index += len(version_text)

    # === 슬로건 ===
    slogan = '포커의 50년 역사, 하나의 플랫폼\n'
    requests.append({
        'insertText': {
            'location': {'index': index},
            'text': slogan
        }
    })
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(slogan)},
            'paragraphStyle': {
                'namedStyleType': 'HEADING_1',
                'alignment': 'CENTER'
            },
            'fields': 'namedStyleType,alignment'
        }
    })
    index += len(slogan)

    # === 핵심 수치 ===
    key_metrics = '18TB+ 아카이브 • 1973년부터 현재까지 • 세계 유일의 WSOP 공식 OTT\n\n'
    requests.append({
        'insertText': {
            'location': {'index': index},
            'text': key_metrics
        }
    })
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(key_metrics)},
            'paragraphStyle': {'alignment': 'CENTER'},
            'fields': 'alignment'
        }
    })
    requests.append({
        'updateTextStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(key_metrics) - 2},
            'textStyle': {'bold': True},
            'fields': 'bold'
        }
    })
    index += len(key_metrics)

    # === 구분선 ===
    divider = '━' * 50 + '\n\n'
    requests.append({
        'insertText': {
            'location': {'index': index},
            'text': divider
        }
    })
    index += len(divider)

    # === Executive Summary ===
    exec_heading = 'Executive Summary\n'
    requests.append({
        'insertText': {
            'location': {'index': index},
            'text': exec_heading
        }
    })
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(exec_heading)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }
    })
    index += len(exec_heading)

    exec_content = '''WSOPTV는 세계 최고 권위의 포커 대회 WSOP(World Series of Poker)의 50년 역사를 담은 유일한 공식 스트리밍 플랫폼입니다.

1970년 Benny Binion이 7명의 전설적 플레이어를 모아 시작한 WSOP는, 오늘날 매년 10,000명 이상이 참가하는 포커의 올림픽으로 성장했습니다.

'''
    requests.append({
        'insertText': {
            'location': {'index': index},
            'text': exec_content
        }
    })
    index += len(exec_content)

    # === 핵심 지표 테이블 제목 ===
    table_title = '핵심 지표\n\n'
    requests.append({
        'insertText': {
            'location': {'index': index},
            'text': table_title
        }
    })
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(table_title) - 1},
            'paragraphStyle': {'namedStyleType': 'HEADING_3'},
            'fields': 'namedStyleType'
        }
    })
    index += len(table_title)

    # === 핵심 지표 테이블 ===
    requests.append({
        'insertTable': {
            'location': {'index': index},
            'rows': 5,
            'columns': 2
        }
    })

    # 테이블 데이터
    table_data = [
        ['지표', '수치'],
        ['아카이브 규모', '18TB+ (50년 역사)'],
        ['연간 콘텐츠', '80+ 브레이슬릿 이벤트'],
        ['메인 이벤트 참가자', '10,000명+ (2024)'],
        ['최대 우승 상금', '$12.1M (2023)']
    ]

    # 실행 (테이블 삽입 후 인덱스 업데이트 필요)
    result = docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()
    print("기본 콘텐츠 삽입 완료")

    # 테이블 셀 채우기 (별도 요청)
    # 문서 다시 가져와서 테이블 위치 확인
    doc = docs_service.documents().get(documentId=doc_id).execute()

    # 테이블 찾기
    table_requests = []
    for element in doc.get('body', {}).get('content', []):
        if 'table' in element:
            table = element['table']
            table_start = element['startIndex']

            for row_idx, row in enumerate(table.get('tableRows', [])):
                for col_idx, cell in enumerate(row.get('tableCells', [])):
                    cell_start = cell['startIndex']
                    if row_idx < len(table_data) and col_idx < len(table_data[row_idx]):
                        text = table_data[row_idx][col_idx]
                        table_requests.append({
                            'insertText': {
                                'location': {'index': cell_start + 1},
                                'text': text
                            }
                        })
                        # 헤더 행 볼드 처리
                        if row_idx == 0:
                            table_requests.append({
                                'updateTextStyle': {
                                    'range': {
                                        'startIndex': cell_start + 1,
                                        'endIndex': cell_start + 1 + len(text)
                                    },
                                    'textStyle': {'bold': True},
                                    'fields': 'bold'
                                }
                            })
            break

    if table_requests:
        # 역순으로 실행 (인덱스 꼬임 방지)
        table_requests.reverse()
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': table_requests}
        ).execute()
        print("테이블 데이터 삽입 완료")

    # === 나머지 섹션 추가 ===
    add_remaining_sections(doc_id, docs_service)

    return doc_id


def add_remaining_sections(doc_id: str, docs_service):
    """나머지 섹션들 추가"""

    # 문서 끝 인덱스 가져오기
    doc = docs_service.documents().get(documentId=doc_id).execute()
    end_index = doc['body']['content'][-1]['endIndex'] - 1

    sections_text = '''

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 왜 WSOP인가: 포커의 최고봉

1.1 브레이슬릿의 무게

"WSOP 브레이슬릿은 포커의 올림픽 금메달이다."

1976년 Benny Binion이 도입한 WSOP 금 브레이슬릿은 단순한 상이 아닙니다. 이것은 포커 플레이어가 평생을 바쳐 추구하는 궁극의 증명입니다.

포커 커뮤니티에서 플레이어의 위상은 명확하게 구분됩니다—브레이슬릿 보유자와 미보유자.

역대 브레이슬릿 레전드:
• Phil Hellmuth - 17개 브레이슬릿 (역대 최다), "Poker Brat"
• Phil Ivey - 11개 브레이슬릿, "Tiger Woods of Poker"
• Doyle Brunson - 10개 브레이슬릿, 포커의 대부
• Johnny Chan - 10개 브레이슬릿, 영화 Rounders의 실제 주인공
• Daniel Negreanu - 7개 브레이슬릿, WSOP 올타임 머니 리더 ($23.6M)


1.2 Moneymaker Effect: 포커 산업의 혁명

2003년, 테네시주의 평범한 회계사 Chris Moneymaker가 포커 역사를 바꿨습니다.

Moneymaker의 여정:
$86 온라인 예선 → 예선 통과 → $10,000 메인 이벤트 시드 획득 → 839명 중 생존 → 파이널 테이블 진출 → $2,500,000 우승

포커 붐 촉발 효과:
• WSOP 참가자: 839명(2003) → 10,117명(2024) — 12배 성장
• 온라인 포커 플랫폼 폭발적 성장
• ESPN 홀카드 카메라 도입으로 시청 경험 혁신
• 일반인의 "나도 할 수 있다" 인식 확산

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. 콘텐츠 왕국: 무엇이 있는가

2.1 콘텐츠 구성 비율

WSOPTV 콘텐츠의 80%는 WSOP Las Vegas에서 생산됩니다. 매년 5월부터 7월까지, 50일간 벌어지는 포커의 축제가 우리의 핵심 자산입니다.

전체 콘텐츠 구성:
• WSOP Las Vegas: 80% (Main Event, Bracelet Events, Best Hands)
• 기타 대회: 10% (Paradise, Europe, Super Circuit)
• 오리지널 콘텐츠: 10% (Game of Gold, Documentary)


2.2 WSOP Las Vegas 상세

매년 5-7월, 라스베이거스에서 80개 이상의 브레이슬릿 이벤트가 펼쳐집니다.

Main Event (35%)
$10,000 No-Limit Hold'em Championship—포커의 꿈이 현실이 되는 무대.
• 참가자: 8,000~10,000명
• 기간: 10일+
• 우승 상금: $10M+ (2024 기준)

Bracelet Events (30%)
• No-Limit Hold'em: $1,500 NLH, $3,000 NLH, $5,000 NLH
• Pot-Limit Omaha: $1,500 PLO, $10K PLO Championship
• Mixed Games: $50K Poker Players Championship, HORSE
• Special Events: Ladies, Seniors, Tag Team

Best Hands 큐레이션 (15%)
• All-in Showdowns: 올인 후 런아웃의 극적인 드라마
• Bluff Catches: 용기 있는 콜로 상대의 블러프를 잡아내는 순간
• Hero Calls/Folds: 역사에 남을 명장면
• Monster Pots: $500K 이상의 거액 팟

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. 차별화 전략: YouTube vs WSOPTV

투트랙 전략
"YouTube는 미끼, WSOPTV는 풀코스."

YouTube (무료):
• 생방송: 토너먼트 실시간 스트리밍
• 쇼츠/클립: 30초~5분의 극적인 순간
• 기능: 무료 시청, 구독 유도용 콘텐츠

WSOPTV (구독):
• 풀 에피소드: 전체 라운드 완전 영상
• Hand Skip: 핵심 핸드만 편집된 버전
• Best Hands: 50년 역사에서 선별한 명경기
• 4K Remaster: 클래식 영상의 화질 복원


WSOPTV 독점 기능:

1. Hand Skip (시간 효율화)
   일반 영상 3시간 → Hand Skip 45분
   바쁜 포커 팬을 위한 액션 핸드만 연속 시청

2. Best Hands 컬렉션 (큐레이션)
   선정 기준: Pot Size 25%, Drama 25%, Skill Display 20%, Player Fame 15%, Outcome 15%

3. 4K Remaster (아카이브 복원)
   1973~2010년 클래식 영상을 AI 업스케일링으로 복원
   SD (480p) → 4K (2160p)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. 콘텐츠 캘린더

연간 시즌 구조:
• Q1 (1~3월): 비시즌 + Super Circuit Cyprus (10%)
• Q2 (4월): WSOP Europe (5%)
• Q2-Q3 (5~7월): WSOP Las Vegas (80%) ★ 피크 시즌
• Q3 (8~9월): 비시즌 (2%)
• Q4 (10~12월): Super Circuit Canada + WSOP Paradise (3%)

피크 시즌 콘텐츠 배출량:
• 주당 평균: 15~20개 에피소드
• 총 콘텐츠: 약 150~160개 풀 에피소드
• Hand Skip 버전: 각 에피소드당 별도 제작


글로벌 확장 로드맵 (2026~):

2026년 - 아시아 진출:
• WSOP Asia (마카오): Q2-Q3
• WSOP Philippines (필리핀): Q4

2027년 - 신흥 시장 진출:
• WSOP Brazil (브라질): Q2
• WSOP India (인도): Q2
• WSOP Australia (호주): Q4

2028년 이후 - 365일 글로벌 콘텐츠

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. 서비스 진화 로드맵

4단계 진화:

Phase 1 - MVP:
• 전체 18TB+ 아카이브 OTT 서비스 런칭
• 이어보기 기능으로 지속적인 시청 경험 제공

Phase 2 - 개인화:
• 시청 이력 기반 프로필별 추천
• 플레이어/이벤트/시대별 카테고리 추천

Phase 3 - 차별화:
• Hand Skip: 3시간 에피소드를 45분 액션 하이라이트로
• Best Hands: 50년 역사에서 선별한 극적 순간 컬렉션

Phase 4 - 프리미엄:
• 4K Remaster: CLASSIC/BOOM 시대 AI 업스케일링
• 독점 다큐멘터리: 레전드 플레이어 스토리, 포커 역사

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. 아카이브 시대 구분

50년의 포커 역사는 명확한 네 개의 시대로 나뉩니다.

CLASSIC (1973-2002): 전설의 시작
• 포커 초창기, SD 화질 (VHS)
• 콘텐츠 가치: 희귀 영상, 포커 DNA, 전설의 탄생
• 주요 플레이어: Benny Binion, Doyle Brunson, Johnny Chan

BOOM (2003-2010): 포커의 대변혁
• Moneymaker Effect, 초기 디지털
• 콘텐츠 가치: 산업 혁명, 전환점 기록, 포커 황금기
• 주요 이벤트: 2003 Moneymaker 우승, 2006 참가자 8,773명

HD (2011-2025): 현대 포커 시대
• HD/4K 프로덕션, 현대 포커 시대
• 콘텐츠 가치: 고화질 풀 에피소드, GTO 시대 포커 진화
• 주요 플레이어: Daniel Negreanu, Phil Ivey, Phil Hellmuth

WSOPTV (2026~): 플랫폼 시대
• 네이티브 OTT, 4K Remaster
• 콘텐츠 가치: 독점 오리지널 콘텐츠, WSOP 완전 디지털화

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WSOPTV는 이 모든 시대를 아우르는 유일한 통합 아카이브입니다.
50년의 포커 역사를 연속적으로 경험할 수 있는 최초의 플랫폼입니다.
'''

    requests = [
        {
            'insertText': {
                'location': {'index': end_index},
                'text': sections_text
            }
        }
    ]

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()
    print("나머지 섹션 삽입 완료")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("WSOPTV 콘텐츠 전략 - Google Docs 생성")
    print("=" * 60)

    # 문서 생성
    doc_id, docs_service = create_google_doc(
        title="WSOPTV 콘텐츠 전략 v4.0",
        folder_id=WSOPTV_FOLDER_ID
    )

    # 콘텐츠 추가
    add_content_to_doc(doc_id, docs_service)

    # 결과 출력
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print("\n" + "=" * 60)
    print("생성 완료!")
    print(f"문서 URL: {doc_url}")
    print("=" * 60)

    return doc_url


if __name__ == "__main__":
    main()
