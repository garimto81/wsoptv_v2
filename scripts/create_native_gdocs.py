"""
Google Docs 네이티브 기능을 활용한 문서 재설계
- 네이티브 표 (insertTable)
- 네이티브 헤딩 스타일
- 볼드/이탤릭 서식
- 가로선
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents']
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '1431Dz71jRV78o6-bwgR6sVM573bnGKf9-9Ozyo6hKpg'


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


def clear_document(docs_service, doc_id):
    """문서 내용 비우기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    if content:
        end_index = content[-1].get('endIndex', 1) - 1
        if end_index > 1:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': [{'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index}}}]}
            ).execute()
    print("문서 비우기 완료")


def build_document_structure():
    """Google Docs 네이티브 구조 정의"""

    # 문서 구조 (순서대로 삽입)
    structure = []

    # ===== TITLE =====
    structure.append({
        'type': 'text',
        'content': 'WSOPTV 콘텐츠 전략\n',
        'style': 'TITLE'
    })

    structure.append({
        'type': 'text',
        'content': 'Version 4.0.0 | Google Docs Native\n\n',
        'style': 'NORMAL_TEXT'
    })

    # ===== 슬로건 =====
    structure.append({
        'type': 'text',
        'content': '포커의 50년 역사, 하나의 플랫폼\n',
        'style': 'SUBTITLE',
        'alignment': 'CENTER'
    })

    structure.append({
        'type': 'text',
        'content': '18TB+ 아카이브  •  1973년부터 현재까지  •  세계 유일의 WSOP 공식 OTT\n\n',
        'style': 'NORMAL_TEXT',
        'alignment': 'CENTER',
        'bold': True
    })

    # ===== Executive Summary =====
    structure.append({'type': 'horizontal_rule'})

    structure.append({
        'type': 'text',
        'content': 'Executive Summary\n',
        'style': 'HEADING_1'
    })

    structure.append({
        'type': 'text',
        'content': '''WSOPTV는 세계 최고 권위의 포커 대회 WSOP(World Series of Poker)의 50년 역사를 담은 유일한 공식 스트리밍 플랫폼입니다.

1970년 Benny Binion이 7명의 전설적 플레이어를 모아 시작한 WSOP는, 오늘날 매년 10,000명 이상이 참가하는 포커의 올림픽으로 성장했습니다.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '핵심 지표\n',
        'style': 'HEADING_3'
    })

    # 핵심 지표 테이블
    structure.append({
        'type': 'table',
        'rows': 5,
        'cols': 2,
        'data': [
            ['지표', '수치'],
            ['아카이브 규모', '18TB+ (50년 역사)'],
            ['연간 콘텐츠', '80+ 브레이슬릿 이벤트'],
            ['메인 이벤트 참가자', '10,000명+ (2024)'],
            ['최대 우승 상금', '$12.1M (2023)']
        ],
        'header_row': True
    })

    # ===== Section 1 =====
    structure.append({'type': 'horizontal_rule'})

    structure.append({
        'type': 'text',
        'content': '1. 왜 WSOP인가: 포커의 최고봉\n',
        'style': 'HEADING_1'
    })

    structure.append({
        'type': 'text',
        'content': '1.1 브레이슬릿의 무게\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '"WSOP 브레이슬릿은 포커의 올림픽 금메달이다."\n\n',
        'style': 'NORMAL_TEXT',
        'italic': True
    })

    structure.append({
        'type': 'text',
        'content': '''1976년 Benny Binion이 도입한 WSOP 금 브레이슬릿은 단순한 상이 아닙니다. 이것은 포커 플레이어가 평생을 바쳐 추구하는 궁극의 증명입니다.

포커 커뮤니티에서 플레이어의 위상은 명확하게 구분됩니다—브레이슬릿 보유자와 미보유자.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '역대 브레이슬릿 레전드\n',
        'style': 'HEADING_3'
    })

    # 브레이슬릿 레전드 테이블
    structure.append({
        'type': 'table',
        'rows': 6,
        'cols': 3,
        'data': [
            ['플레이어', '브레이슬릿', '특징'],
            ['Phil Hellmuth', '17', '"Poker Brat" - 5개 decade 우승, 역대 최다'],
            ['Phil Ivey', '11', '"Tiger Woods of Poker" - 14년간 10개 달성'],
            ['Doyle Brunson', '10', '포커의 대부, 메인 이벤트 2연속 우승'],
            ['Johnny Chan', '10', '영화 Rounders의 실제 주인공'],
            ['Daniel Negreanu', '7', '"Kid Poker" - WSOP 올타임 머니 리더 ($23.6M)']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n1.2 Moneymaker Effect: 포커 산업의 혁명\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '''2003년, 테네시주의 평범한 회계사 Chris Moneymaker가 포커 역사를 바꿨습니다.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': 'Moneymaker의 여정\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'text',
        'content': '''$86 온라인 예선 → 예선 통과 → $10,000 메인 이벤트 시드 획득 → 839명 중 생존 → 파이널 테이블 진출 → $2,500,000 우승

이 하나의 이야기가 포커 붐(Poker Boom)을 촉발했습니다:

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '포커 붐 촉발 효과\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'table',
        'rows': 4,
        'cols': 3,
        'data': [
            ['연도', '참가자 수', '성장률'],
            ['2003', '839명', '기준'],
            ['2006', '8,773명', '10배 성장'],
            ['2024', '10,117명', '12배 성장']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '''
• 온라인 포커 플랫폼 폭발적 성장
• ESPN 홀카드 카메라 도입으로 시청 경험 혁신
• 일반인의 "나도 할 수 있다" 인식 확산

''',
        'style': 'NORMAL_TEXT'
    })

    # ===== Section 2 =====
    structure.append({'type': 'horizontal_rule'})

    structure.append({
        'type': 'text',
        'content': '2. 콘텐츠 왕국: 무엇이 있는가\n',
        'style': 'HEADING_1'
    })

    structure.append({
        'type': 'text',
        'content': '2.1 콘텐츠 구성 비율\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '''WSOPTV 콘텐츠의 80%는 WSOP Las Vegas에서 생산됩니다. 매년 5월부터 7월까지, 50일간 벌어지는 포커의 축제가 우리의 핵심 자산입니다.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '전체 콘텐츠 구성\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'table',
        'rows': 4,
        'cols': 3,
        'data': [
            ['카테고리', '비중', '세부'],
            ['WSOP Las Vegas', '80%', 'Main Event, Bracelet Events, Best Hands'],
            ['기타 대회', '10%', 'Paradise, Europe, Super Circuit'],
            ['오리지널 콘텐츠', '10%', 'Game of Gold, Documentary']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n2.2 WSOP Las Vegas 상세\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '''매년 5-7월, 라스베이거스에서 80개 이상의 브레이슬릿 이벤트가 펼쳐집니다.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': 'WSOP Las Vegas 콘텐츠 상세\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'table',
        'rows': 6,
        'cols': 3,
        'data': [
            ['콘텐츠', '비중', '설명'],
            ['Main Event', '35%', '$10,000 No-Limit Hold\'em Championship'],
            ['Bracelet Events', '30%', '80+ 독립 챔피언십 이벤트'],
            ['Best Hands', '15%', '50년 역사 명장면 큐레이션'],
            ['Classics', '5%', '역대 명경기 아카이브'],
            ['기타', '15%', '분석, 인터뷰, 비하인드']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\nMain Event 토너먼트 구조\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'text',
        'content': '''• Day 1: 8,000~10,000명 시작 (1A, 1B, 1C 3개 플라이트)
• Day 2-5: 필드 압축 (매일 탈락)
• Final Table: 9명 → 1명 챔피언
• 기간: 총 10일 이상
• 우승 상금: $10M+ (2024 기준)

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': 'Bracelet Events 카테고리\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'table',
        'rows': 5,
        'cols': 2,
        'data': [
            ['카테고리', '대표 이벤트'],
            ['No-Limit Hold\'em', '$1,500 / $3,000 / $5,000 NLH'],
            ['Pot-Limit Omaha', '$1,500 PLO, $10K PLO Championship'],
            ['Mixed Games', '$50K Poker Players Championship, HORSE'],
            ['Special Events', 'Ladies, Seniors, Tag Team']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\nBest Hands 큐레이션\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'text',
        'content': '''포커의 가장 순수한 순간들만 정제한 하이라이트 컬렉션:

• All-in Showdowns: 올인 후 런아웃의 극적인 드라마
• Bluff Catches: 용기 있는 콜로 상대의 블러프를 잡아내는 순간
• Hero Calls/Folds: 역사에 남을 명장면
• Monster Pots: $500K 이상의 거액 팟

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '2.3 기타 대회\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 4,
        'cols': 3,
        'data': [
            ['대회', '시기', '특징'],
            ['WSOP Paradise', '12월', '바하마, $25K Buy-in 리조트 환경'],
            ['WSOP Europe', '4월', '유럽 메이저'],
            ['Super Circuit', '연중', 'Cyprus, Canada 등 지역 대회']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n2.4 오리지널 콘텐츠\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 3,
        'cols': 2,
        'data': [
            ['프로그램', '설명'],
            ['Game of Gold', '포커 리얼리티 쇼'],
            ['Player Story', '레전드 플레이어 다큐멘터리']
        ],
        'header_row': True
    })

    # ===== Section 3 =====
    structure.append({'type': 'horizontal_rule'})

    structure.append({
        'type': 'text',
        'content': '3. 차별화 전략: YouTube vs WSOPTV\n',
        'style': 'HEADING_1'
    })

    structure.append({
        'type': 'text',
        'content': '3.1 투트랙 전략\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '"YouTube는 미끼, WSOPTV는 풀코스."\n\n',
        'style': 'NORMAL_TEXT',
        'bold': True
    })

    structure.append({
        'type': 'text',
        'content': '''WSOPTV의 핵심 전략은 투트랙 콘텐츠 배포입니다. YouTube에서 짧은 클립과 생방송으로 포커 입문자를 유입하고, 깊이 있는 경험을 원하는 시청자를 WSOPTV로 전환합니다.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '콘텐츠 플랫폼 비교\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'table',
        'rows': 3,
        'cols': 3,
        'data': [
            ['플랫폼', '역할', '콘텐츠'],
            ['YouTube (무료)', '관심 유도, 유입', '생방송, 쇼츠/클립'],
            ['WSOPTV (구독)', '깊이 있는 경험', '풀 에피소드, Hand Skip, Best Hands, 4K']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n3.2 기능 비교표\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 7,
        'cols': 4,
        'data': [
            ['기능', 'YouTube (무료)', 'WSOPTV (구독)', '차별점'],
            ['생방송', '✓', '✓', '동일 제공'],
            ['쇼츠/클립', '✓', '-', 'YouTube 전용'],
            ['풀 에피소드', '-', '✓', 'WSOPTV 독점'],
            ['Hand Skip', '-', '✓', 'WSOPTV 혁신'],
            ['Best Hands', '-', '✓', 'WSOPTV 독점'],
            ['4K Remaster', '-', '✓', 'WSOPTV 독점']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n3.3 WSOPTV 독점 기능 상세\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '기능 1: Hand Skip (시간 효율화)\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'text',
        'content': '''포커 시청의 혁명. 지루한 폴드와 스몰팟을 건너뛰고, 핵심 핸드만 연속으로 시청합니다.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'table',
        'rows': 5,
        'cols': 3,
        'data': [
            ['항목', '일반 영상', 'Hand Skip'],
            ['총 길이', '3시간', '45분'],
            ['포함 내용', '모든 핸드', '액션 핸드만'],
            ['시청 경험', '선택적 시청', '논스톱 액션'],
            ['학습 효과', '낮음', '높음']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n기능 2: Best Hands 컬렉션\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'text',
        'content': '''50년 WSOP 역사에서 엄선한 가장 극적인 순간들

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': 'Best Hands 선정 기준\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'table',
        'rows': 6,
        'cols': 2,
        'data': [
            ['요소', '가중치'],
            ['Pot Size (거액 팟)', '25%'],
            ['Drama (극적 상황)', '25%'],
            ['Skill Display (기술력)', '20%'],
            ['Player Fame (플레이어 인지도)', '15%'],
            ['Outcome (예상 외 결과)', '15%']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n기능 3: 4K Remaster\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'text',
        'content': '''1973~2010년 클래식 영상을 AI 업스케일링으로 복원합니다.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'table',
        'rows': 5,
        'cols': 3,
        'data': [
            ['지표', '원본', '4K Remaster'],
            ['해상도', 'SD (480p)', '4K (2160p)'],
            ['프레임 품질', '저화질', '선명함'],
            ['색감', '감퇴', '복원'],
            ['시청 경험', '아카이브 느낌', '현대적']
        ],
        'header_row': True
    })

    # ===== Section 4 =====
    structure.append({'type': 'horizontal_rule'})

    structure.append({
        'type': 'text',
        'content': '4. 콘텐츠 캘린더\n',
        'style': 'HEADING_1'
    })

    structure.append({
        'type': 'text',
        'content': '4.1 연간 시즌 구조\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '''WSOPTV의 콘텐츠 흐름은 5월~7월의 WSOP Las Vegas 시즌을 중심으로 설계됩니다.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '4.2 분기별 콘텐츠 흐름\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 6,
        'cols': 4,
        'data': [
            ['분기', '시기', '주요 이벤트', '비중'],
            ['Q1', '1~3월', '비시즌 + Super Circuit Cyprus', '10%'],
            ['Q2', '4월', 'WSOP Europe', '5%'],
            ['Q2-Q3', '5~7월', '★ WSOP Las Vegas (피크 시즌)', '80%'],
            ['Q3', '8~9월', '비시즌', '2%'],
            ['Q4', '10~12월', 'Super Circuit Canada + Paradise', '3%']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n4.3 피크 시즌 상세 (5월~7월)\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '''이 3개월이 연간 콘텐츠의 80%를 차지합니다.

''',
        'style': 'NORMAL_TEXT',
        'bold': True
    })

    structure.append({
        'type': 'table',
        'rows': 8,
        'cols': 3,
        'data': [
            ['주차', '주요 활동', '콘텐츠 품목'],
            ['Week 1-2', 'Main Event Day 1A-1C', '풀 에피소드 3개, Hand Skip'],
            ['Week 2-3', 'Main Event Day 2-3', '풀 에피소드 2개, 분석'],
            ['Week 3-4', 'Main Event Day 4-5', '풀 에피소드 2개, Best Hands'],
            ['Week 4-6', 'Bracelet Events', '이벤트별 파이널 테이블'],
            ['Week 6-8', 'Bracelet 완주', '$50K PPC, HORSE, 스페셜'],
            ['Week 8-9', '시즌 피날레', '연간 Best Hands 집계'],
            ['Week 9-10', '아카이브 배치', '4K Remaster, 클래식 재편성']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '''
피크 시즌 콘텐츠 배출량:
• 주당 평균: 15~20개 에피소드
• 총 콘텐츠: 약 150~160개 풀 에피소드
• Hand Skip 버전: 각 에피소드당 별도 제작

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '4.4 글로벌 확장 로드맵 (2026~)\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '2026년: 아시아 진출\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'table',
        'rows': 3,
        'cols': 3,
        'data': [
            ['지역', '이벤트명', '예정'],
            ['마카오', 'WSOP Asia', 'Q2-Q3'],
            ['필리핀', 'WSOP Philippines', 'Q4']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n2027년: 신흥 시장 진출\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'table',
        'rows': 4,
        'cols': 3,
        'data': [
            ['지역', '이벤트명', '예정'],
            ['브라질', 'WSOP Brazil', 'Q2'],
            ['인도', 'WSOP India', 'Q2'],
            ['호주', 'WSOP Australia', 'Q4']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n2028년 이후: 365일 글로벌 콘텐츠\n',
        'style': 'HEADING_3'
    })

    structure.append({
        'type': 'table',
        'rows': 6,
        'cols': 3,
        'data': [
            ['시기', '지역', '주요 이벤트'],
            ['1~3월', '아시아', 'Philippines, Macau'],
            ['4~5월', '유럽', 'WSOP Europe'],
            ['5~7월', '북미', 'WSOP Las Vegas'],
            ['8~9월', '남미', 'WSOP Brazil'],
            ['10~12월', '태평양', 'Australia, Paradise']
        ],
        'header_row': True
    })

    # ===== Section 5 =====
    structure.append({'type': 'horizontal_rule'})

    structure.append({
        'type': 'text',
        'content': '5. 서비스 진화 로드맵\n',
        'style': 'HEADING_1'
    })

    structure.append({
        'type': 'text',
        'content': '5.1 4단계 진화\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 5,
        'cols': 3,
        'data': [
            ['Phase', '단계명', '주요 기능'],
            ['Phase 1', 'MVP', '전체 볼륨 OTT, 이어보기'],
            ['Phase 2', '개인화', '프로필 추천, 카테고리 추천'],
            ['Phase 3', '차별화', 'Hand Skip, Best Hands'],
            ['Phase 4', '프리미엄', '4K Remaster, 독점 다큐']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n5.2 Feature Matrix\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 9,
        'cols': 5,
        'data': [
            ['기능', 'P1 MVP', 'P2 개인화', 'P3 차별화', 'P4 프리미엄'],
            ['전체 볼륨 OTT', '✓', '✓', '✓', '✓'],
            ['이어보기', '✓', '✓', '✓', '✓'],
            ['프로필 추천', '-', '✓', '✓', '✓'],
            ['카테고리 추천', '-', '✓', '✓', '✓'],
            ['Hand Skip', '-', '-', '✓', '✓'],
            ['Best Hands', '-', '-', '✓', '✓'],
            ['4K Remaster', '-', '-', '-', '✓'],
            ['독점 다큐', '-', '-', '-', '✓']
        ],
        'header_row': True
    })

    # ===== Section 6 =====
    structure.append({'type': 'horizontal_rule'})

    structure.append({
        'type': 'text',
        'content': '6. 아카이브 시대 구분\n',
        'style': 'HEADING_1'
    })

    structure.append({
        'type': 'text',
        'content': '''50년의 포커 역사는 명확한 네 개의 시대로 나뉩니다.

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '6.1 시대별 개요\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 5,
        'cols': 4,
        'data': [
            ['시대', '연도', '특징', '콘텐츠 가치'],
            ['CLASSIC', '1973-2002', '포커 초창기, SD 화질', '희귀 영상, 전설의 탄생'],
            ['BOOM', '2003-2010', 'Moneymaker 이후 황금기', '산업 혁명, 전환점 기록'],
            ['HD', '2011-2025', '현대 포커, HD/4K 프로덕션', '고화질 풀 에피소드'],
            ['WSOPTV', '2026~', '플랫폼 시대, 네이티브 OTT', '독점 오리지널 콘텐츠']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\n6.2 CLASSIC (1973-2002): 전설의 시작\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '''WSOP가 탄생한 시대. 7명의 플레이어로 시작한 작은 게임이 포커 산업의 기초를 마련했습니다.

• 기술: 아날로그 영상 및 VHS 저장
• 콘텐츠: 초창기 카우보이 포커의 희귀한 영상
• 가치: 포커 역사의 기원, Benny Binion의 유산
• 주요 플레이어: Benny Binion, Doyle Brunson, Johnny Chan

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '6.3 BOOM (2003-2010): 포커의 대변혁\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '''Chris Moneymaker의 2003년 우승이 촉발한 포커 산업의 황금기.

• 기술: 초기 디지털 녹화, ESPN 홀카드 카메라 도입
• 콘텐츠: 온라인 포커 붐 시대의 기록
• 가치: 포커가 메인스트림 오락이 된 증거
• 주요 이벤트: 2003 Moneymaker 우승, 2006 참가자 8,773명

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '6.4 HD (2011-2025): 현대 포커 시대\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '''고화질 제작 표준과 프로페셔널 포커 생태계의 확립.

• 기술: HD/4K 네이티브 제작
• 콘텐츠: 풀 에피소드 고화질 보관
• 가치: GTO 이론, AI 시대 포커의 진화
• 주요 플레이어: Daniel Negreanu, Phil Ivey, Phil Hellmuth

''',
        'style': 'NORMAL_TEXT'
    })

    structure.append({
        'type': 'text',
        'content': '6.5 WSOPTV (2026~): 플랫폼 시대\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'text',
        'content': '''WSOPTV 전용 오리지널 콘텐츠 시대의 개막.

• 기술: 네이티브 OTT 플랫폼, 4K Remaster
• 콘텐츠: 독점 다큐멘터리, 추가 제작
• 가치: WSOP의 완전한 디지털화

''',
        'style': 'NORMAL_TEXT'
    })

    # ===== 부록 =====
    structure.append({'type': 'horizontal_rule'})

    structure.append({
        'type': 'text',
        'content': '부록: 기술 참조\n',
        'style': 'HEADING_1'
    })

    structure.append({
        'type': 'text',
        'content': 'A. 에피소드 메타데이터\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 8,
        'cols': 3,
        'data': [
            ['필드명', '타입', '설명 / 예시'],
            ['title', 'string', 'WSOP 2024 Main Event Day 5'],
            ['event', 'string', 'Main Event / $1,500 NLH'],
            ['era', 'string', 'CLASSIC / BOOM / HD / WSOPTV'],
            ['featured_players', 'array', '[Daniel Negreanu, Phil Ivey]'],
            ['air_date', 'date', '2024-05-15'],
            ['duration', 'integer', '180 (분)'],
            ['buy_in', 'integer', '10000']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\nB. 검색 자동완성 제안\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 6,
        'cols': 2,
        'data': [
            ['사용자 입력', '제안'],
            ['dan', 'Daniel Negreanu, Daniel Negreanu Best Hands'],
            ['phil', 'Phil Hellmuth, Phil Ivey, Phil Ivey Highlights'],
            ['main 2024', 'WSOP 2024 Main Event, Main Event Final Table'],
            ['bracelet', 'Bracelet Events, $50K PPC, HORSE Championship'],
            ['omaha', 'Pot-Limit Omaha, $1,500 PLO, $10K PLO Championship']
        ],
        'header_row': True
    })

    structure.append({
        'type': 'text',
        'content': '\nC. 플레이어 프로파일\n',
        'style': 'HEADING_2'
    })

    structure.append({
        'type': 'table',
        'rows': 5,
        'cols': 5,
        'data': [
            ['플레이어', '별명', '브레이슬릿', 'WSOP 수익', '특징'],
            ['Phil Hellmuth', 'Poker Brat', '17개', '$28M+', '역대 최다 브레이슬릿'],
            ['Phil Ivey', 'Tiger Woods of Poker', '11개', '$30M+', '완벽주의자, 모든 스타일 정복'],
            ['Daniel Negreanu', 'Kid Poker', '7개', '$23.6M', '올타임 머니 리더'],
            ['Alan Keating', 'Cash Game Legend', '1개', '$2.5M+', '하이스테이크 캐시게임 레전드']
        ],
        'header_row': True
    })

    # ===== 마무리 =====
    structure.append({'type': 'horizontal_rule'})

    structure.append({
        'type': 'text',
        'content': '''WSOPTV는 이 모든 시대를 아우르는 유일한 통합 아카이브입니다.
50년의 포커 역사를 연속적으로 경험할 수 있는 최초의 플랫폼입니다.
''',
        'style': 'NORMAL_TEXT',
        'bold': True,
        'alignment': 'CENTER'
    })

    return structure


def insert_structure(docs_service, doc_id, structure):
    """문서에 구조 삽입"""
    requests = []
    current_index = 1

    for item in structure:
        if item['type'] == 'text':
            # 텍스트 삽입
            text = item['content']
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': text
                }
            })

            start_idx = current_index
            end_idx = current_index + len(text)

            # 스타일 적용
            if item.get('style') and item['style'] != 'NORMAL_TEXT':
                requests.append({
                    'updateParagraphStyle': {
                        'range': {'startIndex': start_idx, 'endIndex': end_idx},
                        'paragraphStyle': {'namedStyleType': item['style']},
                        'fields': 'namedStyleType'
                    }
                })

            # 정렬 적용
            if item.get('alignment'):
                requests.append({
                    'updateParagraphStyle': {
                        'range': {'startIndex': start_idx, 'endIndex': end_idx},
                        'paragraphStyle': {'alignment': item['alignment']},
                        'fields': 'alignment'
                    }
                })

            # 볼드 적용
            if item.get('bold'):
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': start_idx, 'endIndex': end_idx - 1},
                        'textStyle': {'bold': True},
                        'fields': 'bold'
                    }
                })

            # 이탤릭 적용
            if item.get('italic'):
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': start_idx, 'endIndex': end_idx - 1},
                        'textStyle': {'italic': True},
                        'fields': 'italic'
                    }
                })

            current_index = end_idx

        elif item['type'] == 'table':
            # 테이블 삽입 전 줄바꿈
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': '\n'
                }
            })
            current_index += 1

            # 테이블 삽입
            requests.append({
                'insertTable': {
                    'location': {'index': current_index},
                    'rows': item['rows'],
                    'columns': item['cols']
                }
            })

            # 테이블 삽입 후 인덱스 업데이트 (대략적인 추정)
            # 테이블 크기: rows * cols * 2 (셀당 약 2 인덱스) + 구조 오버헤드
            table_size = item['rows'] * item['cols'] * 2 + item['rows'] + 5
            current_index += table_size

            # 줄바꿈 추가
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': '\n'
                }
            })
            current_index += 1

        elif item['type'] == 'horizontal_rule':
            # 가로선 대신 구분 텍스트
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': '\n\n'
                }
            })
            current_index += 2

    # 첫 번째 배치: 텍스트와 기본 스타일만
    text_requests = [r for r in requests if 'insertText' in r or 'updateParagraphStyle' in r or 'updateTextStyle' in r]

    if text_requests:
        try:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': text_requests}
            ).execute()
            print(f"텍스트 및 스타일 삽입 완료: {len(text_requests)}개 요청")
        except Exception as e:
            print(f"오류: {e}")
            # 오류 시 텍스트만 삽입
            text_only = [r for r in requests if 'insertText' in r]
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': text_only}
            ).execute()
            print("텍스트만 삽입 완료")


def insert_tables_after(docs_service, doc_id, structure):
    """테이블 데이터를 별도로 삽입 (문서 생성 후)"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    # 테이블 찾기
    tables = []
    for element in content:
        if 'table' in element:
            tables.append(element)

    # 구조에서 테이블 데이터 추출
    table_data_list = [item for item in structure if item['type'] == 'table']

    print(f"문서의 테이블: {len(tables)}개, 데이터: {len(table_data_list)}개")

    # 테이블 데이터 삽입 (역순으로)
    for idx, (table_element, table_data) in enumerate(zip(tables, table_data_list)):
        requests = []
        table = table_element['table']

        for row_idx, row in enumerate(table.get('tableRows', [])):
            for col_idx, cell in enumerate(row.get('tableCells', [])):
                if row_idx < len(table_data['data']) and col_idx < len(table_data['data'][row_idx]):
                    text = str(table_data['data'][row_idx][col_idx])
                    cell_start = cell['startIndex']

                    requests.append({
                        'insertText': {
                            'location': {'index': cell_start + 1},
                            'text': text
                        }
                    })

                    # 헤더 행 볼드 처리
                    if table_data.get('header_row') and row_idx == 0:
                        requests.append({
                            'updateTextStyle': {
                                'range': {
                                    'startIndex': cell_start + 1,
                                    'endIndex': cell_start + 1 + len(text)
                                },
                                'textStyle': {'bold': True},
                                'fields': 'bold'
                            }
                        })

        if requests:
            # 역순으로 실행
            requests.reverse()
            try:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
                print(f"테이블 {idx + 1} 데이터 삽입 완료")
            except Exception as e:
                print(f"테이블 {idx + 1} 오류: {e}")


def main():
    print("=" * 60)
    print("Google Docs 네이티브 최적화 문서 생성")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 1. 문서 비우기
    clear_document(docs_service, DOC_ID)

    # 2. 문서 구조 정의
    structure = build_document_structure()
    print(f"문서 구조 생성: {len(structure)}개 요소")

    # 3. 텍스트와 스타일 삽입
    insert_structure(docs_service, DOC_ID, structure)

    # 4. 테이블 데이터 삽입
    insert_tables_after(docs_service, DOC_ID, structure)

    print("\n" + "=" * 60)
    print("완료!")
    print(f"문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
