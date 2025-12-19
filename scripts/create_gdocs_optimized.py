"""
Google Docs 최적화 문서 생성 - 단계별 접근
1단계: 텍스트 삽입
2단계: 헤딩 스타일 적용
3단계: 볼드/이탤릭 서식 적용
"""

import os
import re
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


def get_optimized_content():
    """Google Docs에 최적화된 콘텐츠 (ASCII 박스 테이블 제거, 깔끔한 텍스트)"""

    return '''WSOPTV 콘텐츠 전략

Version 4.0.0 | Google Docs 최적화 버전


포커의 50년 역사, 하나의 플랫폼

18TB+ 아카이브  •  1973년부터 현재까지  •  세계 유일의 WSOP 공식 OTT


────────────────────────────────────────

Executive Summary

WSOPTV는 세계 최고 권위의 포커 대회 WSOP(World Series of Poker)의 50년 역사를 담은 유일한 공식 스트리밍 플랫폼입니다.

1970년 Benny Binion이 7명의 전설적 플레이어를 모아 시작한 WSOP는, 오늘날 매년 10,000명 이상이 참가하는 포커의 올림픽으로 성장했습니다.


핵심 지표

아카이브 규모: 18TB+ (50년 역사)
연간 콘텐츠: 80+ 브레이슬릿 이벤트
메인 이벤트 참가자: 10,000명+ (2024)
최대 우승 상금: $12.1M (2023)


────────────────────────────────────────

1. 왜 WSOP인가: 포커의 최고봉


1.1 브레이슬릿의 무게

"WSOP 브레이슬릿은 포커의 올림픽 금메달이다."

1976년 Benny Binion이 도입한 WSOP 금 브레이슬릿은 단순한 상이 아닙니다. 이것은 포커 플레이어가 평생을 바쳐 추구하는 궁극의 증명입니다.

포커 커뮤니티에서 플레이어의 위상은 명확하게 구분됩니다—브레이슬릿 보유자와 미보유자.


역대 브레이슬릿 레전드

Phil Hellmuth — 17개 브레이슬릿
"Poker Brat" - 5개 decade 우승, 역대 최다

Phil Ivey — 11개 브레이슬릿
"Tiger Woods of Poker" - 14년간 10개 달성 (역대 최빠름)

Doyle Brunson — 10개 브레이슬릿
포커의 대부, 메인 이벤트 2연속 우승

Johnny Chan — 10개 브레이슬릿
영화 Rounders의 실제 주인공

Daniel Negreanu — 7개 브레이슬릿
"Kid Poker" - WSOP 올타임 머니 리더 ($23.6M)


1.2 Moneymaker Effect: 포커 산업의 혁명

2003년, 테네시주의 평범한 회계사 Chris Moneymaker가 포커 역사를 바꿨습니다.


Moneymaker의 여정

$86 온라인 예선 → 예선 통과 → $10,000 메인 이벤트 시드 획득 → 839명 중 생존 → 파이널 테이블 진출 → $2,500,000 우승!


포커 붐 촉발 효과

• 2003년: 839명 → 2006년: 8,773명 → 2024년: 10,117명 (12배 성장!)
• 온라인 포커 플랫폼 폭발적 성장
• ESPN 홀카드 카메라 도입으로 시청 경험 혁신
• 일반인의 "나도 할 수 있다" 인식 확산

"평범한 이름이 전설이 된 유일무이한 사례. Moneymaker는 역대 가장 영향력 있는 포커 플레이어다."


────────────────────────────────────────

2. 콘텐츠 왕국: 무엇이 있는가


2.1 콘텐츠 구성 비율

WSOPTV 콘텐츠의 80%는 WSOP Las Vegas에서 생산됩니다. 매년 5월부터 7월까지, 50일간 벌어지는 포커의 축제가 우리의 핵심 자산입니다.


전체 콘텐츠 구성

WSOP Las Vegas — 80%
Main Event, Bracelet Events, Best Hands

기타 대회 — 10%
Paradise, Europe, Super Circuit

오리지널 콘텐츠 — 10%
Game of Gold, Documentary


2.2 WSOP Las Vegas 상세

매년 5-7월, 라스베이거스에서 80개 이상의 브레이슬릿 이벤트가 펼쳐집니다.


Main Event (35%)

$10,000 No-Limit Hold'em Championship—포커의 꿈이 현실이 되는 무대.

• 참가자: 8,000~10,000명
• 기간: 10일+
• 구조: Day 1 (3개 플라이트) → Day 2-5 (필드 압축) → Final Table (9명)
• 우승 상금: $10M+ (2024 기준)


Bracelet Events (30%)

80개 이상의 독립 챔피언십. 각 이벤트는 해당 분야의 세계 최강자를 가립니다.

No-Limit Hold'em: $1,500 / $3,000 / $5,000 NLH
Pot-Limit Omaha: $1,500 PLO, $10K PLO Championship
Mixed Games: $50K Poker Players Championship, HORSE
Special Events: Ladies, Seniors, Tag Team


Best Hands 큐레이션 (15%)

포커의 가장 순수한 순간들만 정제한 하이라이트 컬렉션:

• All-in Showdowns: 올인 후 런아웃의 극적인 드라마
• Bluff Catches: 용기 있는 콜로 상대의 블러프를 잡아내는 순간
• Hero Calls/Folds: 역사에 남을 명장면
• Monster Pots: $500K 이상의 거액 팟


2.3 기타 대회 (10%)

WSOP Paradise — 12월, 바하마
$25K Buy-in 리조트 환경

WSOP Europe — 4월, 유럽
유럽 메이저

Super Circuit — 연중, 전세계
Cyprus, Canada 등


2.4 오리지널 콘텐츠 (10%)

Game of Gold — 포커 리얼리티 쇼
Player Story — 레전드 플레이어 다큐멘터리


────────────────────────────────────────

3. 차별화 전략: YouTube vs WSOPTV


3.1 투트랙 전략

"YouTube는 미끼, WSOPTV는 풀코스."

WSOPTV의 핵심 전략은 투트랙 콘텐츠 배포입니다. YouTube에서 짧은 클립과 생방송으로 포커 입문자를 유입하고, 깊이 있는 경험을 원하는 시청자를 WSOPTV로 전환합니다.


YouTube (무료) → WSOPTV (구독)

YouTube 제공:
• 생방송: 토너먼트 실시간 스트리밍
• 쇼츠/클립: 30초~5분의 극적인 순간
• 기능: 무료 시청, 구독 유도용 콘텐츠

WSOPTV 독점:
• 풀 에피소드: 전체 라운드 완전 영상
• Hand Skip: 핵심 핸드만 편집된 버전
• Best Hands: 50년 역사에서 선별한 명경기
• 4K Remaster: 클래식 영상의 화질 복원


3.2 기능 비교표

생방송: YouTube ✓ / WSOPTV ✓ — 동일 제공
쇼츠/클립: YouTube ✓ / WSOPTV - — YouTube 전용
풀 에피소드: YouTube - / WSOPTV ✓ — WSOPTV 독점
Hand Skip: YouTube - / WSOPTV ✓ — WSOPTV 혁신
Best Hands: YouTube - / WSOPTV ✓ — WSOPTV 독점
4K Remaster: YouTube - / WSOPTV ✓ — WSOPTV 독점


3.3 WSOPTV 독점 기능 상세


기능 1: Hand Skip (시간 효율화)

포커 시청의 혁명. 지루한 폴드와 스몰팟을 건너뛰고, 핵심 핸드만 연속으로 시청합니다.

일반 영상: 3시간 / 모든 핸드 / 선택적 시청
Hand Skip: 45분 / 액션 핸드만 / 논스톱 액션

Hand Skip 우위:
• 바쁜 포커 팬: 3시간 → 45분으로 단시간 몰아보기
• 교육용: 핵심 전략만 집중
• 리플레이: 명경기의 모든 극적 순간 재경험


기능 2: Best Hands 컬렉션 (큐레이션)

50년 WSOP 역사에서 엄선한 가장 극적인 순간들

선정 기준:
• Pot Size (거액 팟): 25%
• Drama (극적 상황): 25%
• Skill Display (기술력): 20%
• Player Fame (플레이어 인지도): 15%
• Outcome (예상 외 결과): 15%

Best Hands 카테고리:
• All-in Showdowns — 올인 후 런아웃의 극적 드라마
• Bluff Catches — 용기 있는 콜로 블러프 적중
• Hero Calls/Folds — 역사에 남을 명장면
• Monster Pots — $500K 이상의 거액 판돈
• Comeback Stories — 절망적 상황에서의 역전


기능 3: 4K Remaster (아카이브 복원)

1973~2010년 클래식 영상을 AI 업스케일링으로 복원합니다.

원본: SD (480p) / 저화질 / 감퇴된 색감 / 아카이브 느낌
4K Remaster: 4K (2160p) / 선명함 / 복원된 색감 / 현대적 시청 경험

4K Remaster 라이브러리:
• CLASSIC (1973-2002): Doyle Brunson의 첫 우승
• BOOM (2003-2010): Chris Moneymaker 2003 우승


────────────────────────────────────────

4. 콘텐츠 캘린더


4.1 연간 시즌 구조

WSOPTV의 콘텐츠 흐름은 5월~7월의 WSOP Las Vegas 시즌을 중심으로 설계됩니다.


4.2 분기별 콘텐츠 흐름

Q1 (1~3월): 비시즌 + Super Circuit Cyprus — 10%
Q2 (4월): WSOP Europe — 5%
Q2-Q3 (5~7월): ★ WSOP Las Vegas ★ — 80% (피크 시즌!)
Q3 (8~9월): 비시즌 — 2%
Q4 (10~12월): Super Circuit Canada + Paradise — 3%


4.3 피크 시즌 상세 (5월~7월)

이 3개월이 연간 콘텐츠의 80%를 차지합니다.

Week 1-2: Main Event Day 1A-1C
→ 풀 에피소드 3개, Hand Skip

Week 2-3: Main Event Day 2-3
→ 풀 에피소드 2개, 분석 콘텐츠

Week 3-4: Main Event Day 4-5
→ 풀 에피소드 2개, Best Hands 업데이트

Week 4-6: Bracelet Events 병행
→ 이벤트별 파이널 테이블

Week 6-8: Bracelet Events 완주
→ $50K PPC, HORSE, 스페셜 이벤트

Week 8-9: 시즌 피날레
→ 연간 Best Hands 집계

Week 9-10: 아카이브 배치
→ 4K Remaster, 클래식 재편성


피크 시즌 콘텐츠 배출량:
• 주당 평균: 15~20개 에피소드
• 총 콘텐츠: 약 150~160개 풀 에피소드
• Hand Skip 버전: 각 에피소드당 별도 제작


4.4 글로벌 확장 로드맵 (2026~)


2026년: 아시아 진출

마카오 — WSOP Asia — Q2-Q3
필리핀 — WSOP Philippines — Q4


2027년: 신흥 시장 진출

브라질 — WSOP Brazil — Q2
인도 — WSOP India — Q2
호주 — WSOP Australia — Q4


2028년 이후: 365일 글로벌 콘텐츠

1~3월: 아시아 (Philippines, Macau)
4~5월: 유럽 (WSOP Europe)
5~7월: 북미 (WSOP Las Vegas)
8~9월: 남미 (WSOP Brazil)
10~12월: 태평양 (Australia, Paradise)


────────────────────────────────────────

5. 서비스 진화 로드맵


5.1 4단계 진화

Phase 1 — MVP
전체 18TB+ 아카이브 OTT 서비스 런칭
이어보기 기능으로 지속적인 시청 경험 제공

Phase 2 — 개인화
시청 이력 기반 프로필별 추천
플레이어/이벤트/시대별 카테고리 추천

Phase 3 — 차별화
Hand Skip: 3시간 에피소드를 45분 액션 하이라이트로
Best Hands: 50년 역사에서 선별한 극적 순간 컬렉션

Phase 4 — 프리미엄
4K Remaster: CLASSIC/BOOM 시대 AI 업스케일링
독점 다큐멘터리: 레전드 플레이어 스토리, 포커 역사


5.2 Feature Matrix

전체 볼륨 OTT: P1 ✓ → P2 ✓ → P3 ✓ → P4 ✓
이어보기: P1 ✓ → P2 ✓ → P3 ✓ → P4 ✓
프로필 추천: P1 - → P2 ✓ → P3 ✓ → P4 ✓
카테고리 추천: P1 - → P2 ✓ → P3 ✓ → P4 ✓
Hand Skip: P1 - → P2 - → P3 ✓ → P4 ✓
Best Hands: P1 - → P2 - → P3 ✓ → P4 ✓
4K Remaster: P1 - → P2 - → P3 - → P4 ✓
독점 다큐: P1 - → P2 - → P3 - → P4 ✓


────────────────────────────────────────

6. 아카이브 시대 구분

50년의 포커 역사는 명확한 네 개의 시대로 나뉩니다.


6.1 시대별 개요

CLASSIC (1973-2002)
특징: 포커 초창기, SD 화질 (VHS)
가치: 희귀 영상, 포커 DNA, 전설의 탄생

BOOM (2003-2010)
특징: Moneymaker 이후 황금기, 초기 디지털
가치: 산업 혁명, 전환점 기록, 포커 황금기

HD (2011-2025)
특징: 현대 포커 시대, HD/4K 프로덕션
가치: 고화질 풀 에피소드, GTO 시대 포커 진화

WSOPTV (2026~)
특징: 플랫폼 시대, 네이티브 OTT
가치: 독점 오리지널 콘텐츠, WSOP 완전 디지털화


6.2 CLASSIC (1973-2002): 전설의 시작

WSOP가 탄생한 시대. 7명의 플레이어로 시작한 작은 게임이 포커 산업의 기초를 마련했습니다.

• 기술: 아날로그 영상 및 VHS 저장
• 콘텐츠: 초창기 카우보이 포커의 희귀한 영상
• 가치: 포커 역사의 기원, Benny Binion의 유산
• 주요 플레이어: Benny Binion, Doyle Brunson, Johnny Chan


6.3 BOOM (2003-2010): 포커의 대변혁

Chris Moneymaker의 2003년 우승이 촉발한 포커 산업의 황금기.

• 기술: 초기 디지털 녹화, ESPN 홀카드 카메라 도입
• 콘텐츠: 온라인 포커 붐 시대의 기록
• 가치: 포커가 메인스트림 오락이 된 증거
• 주요 이벤트: 2003 Moneymaker 우승, 2006 참가자 8,773명 (최고점)


6.4 HD (2011-2025): 현대 포커 시대

고화질 제작 표준과 프로페셔널 포커 생태계의 확립.

• 기술: HD/4K 네이티브 제작
• 콘텐츠: 풀 에피소드 고화질 보관
• 가치: GTO 이론, AI 시대 포커의 진화
• 주요 플레이어: Daniel Negreanu, Phil Ivey, Phil Hellmuth


6.5 WSOPTV (2026~): 플랫폼 시대

WSOPTV 전용 오리지널 콘텐츠 시대의 개막.

• 기술: 네이티브 OTT 플랫폼, 4K Remaster
• 콘텐츠: 독점 다큐멘터리, 추가 제작
• 가치: WSOP의 완전한 디지털화


────────────────────────────────────────

부록: 기술 참조


A. 에피소드 메타데이터

title (string): WSOP 2024 Main Event Day 5
event (string): Main Event / $1,500 NLH
era (string): CLASSIC / BOOM / HD / WSOPTV
featured_players (array): [Daniel Negreanu, Phil Ivey]
air_date (date): 2024-05-15
duration (integer): 180 (분)
buy_in (integer): 10000


B. 검색 자동완성 제안

"dan" → Daniel Negreanu, Daniel Negreanu Best Hands
"phil" → Phil Hellmuth, Phil Ivey, Phil Ivey Highlights
"main 2024" → WSOP 2024 Main Event, Main Event Final Table
"bracelet" → Bracelet Events, $50K PPC, HORSE Championship
"omaha" → Pot-Limit Omaha, $1,500 PLO, $10K PLO Championship


C. 플레이어 프로파일

Phil Hellmuth — "Poker Brat"
브레이슬릿: 17개 (역대 최다)
WSOP 수익: $28M+
특징: 극적 감정 표현, 브레이슬릿 경쟁의 정의

Phil Ivey — "Tiger Woods of Poker"
브레이슬릿: 11개
WSOP 수익: $30M+
특징: 모든 포커 스타일 정복, 완벽주의자

Daniel Negreanu — "Kid Poker"
브레이슬릿: 7개
WSOP 수익: $23.6M (올타임 머니 리더)
특징: 이론과 실전의 결합, 포커의 지적 진화 상징

Alan Keating — "Cash Game Legend"
브레이슬릿: 1개
WSOP 수익: $2.5M+
특징: 하이스테이크 캐시게임 레전드, 엔터테이너


────────────────────────────────────────


WSOPTV는 이 모든 시대를 아우르는 유일한 통합 아카이브입니다.
50년의 포커 역사를 연속적으로 경험할 수 있는 최초의 플랫폼입니다.
'''


def main():
    print("=" * 60)
    print("Google Docs 최적화 문서 생성")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 1. 문서 내용 비우기
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

    # 2. 최적화된 콘텐츠 가져오기
    content_text = get_optimized_content()
    print(f"콘텐츠 길이: {len(content_text)} 문자")

    # 3. 콘텐츠 삽입
    docs_service.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': [{'insertText': {'location': {'index': 1}, 'text': content_text}}]}
    ).execute()
    print("콘텐츠 삽입 완료")

    # 4. 헤딩 스타일 적용
    apply_heading_styles(docs_service, DOC_ID)

    print("\n" + "=" * 60)
    print("완료!")
    print(f"문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


def apply_heading_styles(docs_service, doc_id):
    """헤딩 스타일 적용"""
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

        style = None

        # TITLE
        if text == 'WSOPTV 콘텐츠 전략':
            style = 'TITLE'

        # SUBTITLE
        elif text == '포커의 50년 역사, 하나의 플랫폼':
            style = 'SUBTITLE'

        # HEADING_1: 주요 섹션
        elif text in ['Executive Summary', '부록: 기술 참조']:
            style = 'HEADING_1'
        elif re.match(r'^[1-6]\.\s+[가-힣\w]', text) and not re.match(r'^[1-6]\.[1-9]', text):
            style = 'HEADING_1'

        # HEADING_2: 하위 섹션
        elif re.match(r'^[1-6]\.[1-9]\s+', text):
            style = 'HEADING_2'
        elif text.startswith('A.') or text.startswith('B.') or text.startswith('C.'):
            style = 'HEADING_2'
        elif text in ['2026년: 아시아 진출', '2027년: 신흥 시장 진출', '2028년 이후: 365일 글로벌 콘텐츠']:
            style = 'HEADING_2'

        # HEADING_3: 소제목
        elif text in ['핵심 지표', '역대 브레이슬릿 레전드', 'Moneymaker의 여정', '포커 붐 촉발 효과',
                     '전체 콘텐츠 구성', 'Main Event (35%)', 'Bracelet Events (30%)', 'Best Hands 큐레이션 (15%)',
                     'YouTube (무료) → WSOPTV (구독)',
                     '기능 1: Hand Skip (시간 효율화)', '기능 2: Best Hands 컬렉션 (큐레이션)',
                     '기능 3: 4K Remaster (아카이브 복원)', '피크 시즌 콘텐츠 배출량:']:
            style = 'HEADING_3'

        if style:
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start_index, 'endIndex': end_index},
                    'paragraphStyle': {'namedStyleType': style},
                    'fields': 'namedStyleType'
                }
            })

    if requests:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        print(f"헤딩 스타일 적용: {len(requests)}개")


if __name__ == "__main__":
    main()
