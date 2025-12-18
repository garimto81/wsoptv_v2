"""
WSOPTV UX 문서를 Google Docs로 생성하는 스크립트
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 서비스 계정 키 경로
SERVICE_ACCOUNT_FILE = r'D:\AI\claude01\json\service_account_key.json'

# 필요한 권한
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

# 공유할 폴더 ID (WSOPTV PRD 폴더)
FOLDER_ID = '1zPpTxEM5bPZ62g4bXIAzp8QHXB1T0xgb'


def get_credentials():
    """서비스 계정 인증"""
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )


def create_document(title: str) -> str:
    """새 Google Docs 문서 생성 (Drive API 사용)"""
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    # Drive API로 Google Docs 문서 생성
    file_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [FOLDER_ID]
    }

    doc = drive_service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    return doc.get('id')


def add_content(doc_id: str, requests: list):
    """문서에 콘텐츠 추가"""
    creds = get_credentials()
    service = build('docs', 'v1', credentials=creds)

    service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()


def build_document_requests() -> list:
    """문서 콘텐츠 요청 빌드"""
    requests = []
    index = 1

    def add_text(text: str, bold: bool = False, font_size: int = 11,
                 heading: str = None, color: dict = None):
        nonlocal index

        # 텍스트 삽입
        requests.append({
            'insertText': {
                'location': {'index': index},
                'text': text
            }
        })

        text_len = len(text)
        end_index = index + text_len

        # 스타일 적용
        style = {}
        if bold:
            style['bold'] = True
        if font_size != 11:
            style['fontSize'] = {'magnitude': font_size, 'unit': 'PT'}
        if color:
            style['foregroundColor'] = {'color': {'rgbColor': color}}

        if style:
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': index, 'endIndex': end_index},
                    'textStyle': style,
                    'fields': ','.join(style.keys())
                }
            })

        # 헤딩 스타일 적용
        if heading:
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': index, 'endIndex': end_index},
                    'paragraphStyle': {'namedStyleType': heading},
                    'fields': 'namedStyleType'
                }
            })

        index = end_index

    def add_newline(count: int = 1):
        add_text('\n' * count)

    def add_heading1(text: str):
        add_text(text, heading='HEADING_1')
        add_newline()

    def add_heading2(text: str):
        add_text(text, heading='HEADING_2')
        add_newline()

    def add_heading3(text: str):
        add_text(text, heading='HEADING_3')
        add_newline()

    def add_paragraph(text: str):
        add_text(text)
        add_newline()

    def add_bold_text(text: str):
        add_text(text, bold=True)

    def add_divider():
        add_text('━' * 60)
        add_newline(2)

    # ===== 문서 시작 =====

    add_heading1('WSOPTV - 사용자 경험 설계')
    add_paragraph('Version 1.5.0')
    add_newline()
    add_divider()

    # 섹션 1: 사용자 여정
    add_heading2('1. 사용자 여정 (User Journey)')
    add_newline()

    add_heading3('1.1 신규 사용자 여정')
    add_newline()

    add_bold_text('진입 경로 1: YouTube (신규 유저층 확보)')
    add_newline(2)
    add_paragraph('    YouTube 접속  →  쇼츠/하이라이트  →  풀 영상 관심?  →  WSOPTV 이동  →  구독')
    add_newline()

    add_bold_text('진입 경로 2: WSOPTV 직접 접속')
    add_newline(2)
    add_paragraph('    랜딩페이지 접속  →  콘텐츠 미리보기  →  회원가입  →  구독')
    add_newline()

    add_text('💡 ', color={'red': 0.9, 'green': 0.6, 'blue': 0})
    add_bold_text('투트랙 전략')
    add_newline()
    add_paragraph('YouTube는 신규 유저층이 많아 무료 콘텐츠(쇼츠, 하이라이트)로 유입을 유도합니다.')
    add_paragraph('WSOPTV는 구독자 전용 풀 에피소드 서비스입니다.')
    add_newline()

    add_heading3('1.2 기존 사용자 여정')
    add_newline()
    add_paragraph('    앱/웹 접속  →  로그인  →  홈 화면')
    add_paragraph('                              ↓')
    add_paragraph('                         시청 선택')
    add_paragraph('                        ↙        ↘')
    add_paragraph('              이어보기              새 콘텐츠')
    add_paragraph('                 ↓                    ↓')
    add_paragraph('         중단 지점부터 재생      브라우징  →  에피소드 선택  →  시청 시작')
    add_newline()

    add_text('💡 ', color={'red': 0.9, 'green': 0.6, 'blue': 0})
    add_bold_text('Best Hands')
    add_text(': 별도 페이지가 아닌, 에피소드 시청 중 해당 에피소드의 Best Hands로 점프하는 기능입니다.')
    add_newline(2)

    add_divider()

    # 섹션 2: 홈페이지 구조
    add_heading2('2. 홈페이지 구조')
    add_newline()

    add_heading3('2.0 디자인 의도 및 목적')
    add_newline()

    add_bold_text('핵심 목표: ')
    add_text('포커 VOD 시청에 최적화된 몰입형 경험 제공')
    add_newline(2)

    add_bold_text('디자인 결정 및 의도:')
    add_newline(2)

    design_decisions = [
        ('다크 테마', '장시간 시청 시 눈의 피로 감소, 영상 콘텐츠 집중도 향상'),
        ('Netflix 스타일 레이아웃', '검증된 VOD 플랫폼 UX 패턴으로 학습 비용 최소화'),
        ('가로 스크롤 카드', '많은 콘텐츠를 공간 효율적으로 탐색, 모바일 제스처 친화적'),
        ('Continue Watching 상단 배치', '재방문 사용자의 즉시 시청 재개 유도 (리텐션 핵심)'),
        ('시리즈 그룹핑', 'WSOP/HCL 등 시리즈별 정주행 유도, 시청 시간 증가'),
    ]

    for title, desc in design_decisions:
        add_text('• ')
        add_bold_text(title)
        add_newline()
        add_text(f'  {desc}')
        add_newline(2)

    add_heading3('2.1 전체 화면 구성')
    add_newline()
    add_paragraph('Netflix 스타일의 다크 테마 기반으로 설계된 WSOPTV 홈페이지 전체 구조입니다.')
    add_newline()

    add_text('📎 ', color={'red': 0.2, 'green': 0.5, 'blue': 0.9})
    add_bold_text('[이미지 삽입: 00-full-page.png]')
    add_newline(2)

    add_bold_text('페이지 구성 요소:')
    add_newline(2)

    components = [
        ('A. Header', '상단 고정 네비게이션'),
        ('B. Hero Banner', '메인 추천 콘텐츠'),
        ('C. Continue Watching', '이어보기 섹션'),
        ('D. Recently Added', '최근 추가 콘텐츠'),
        ('E. Series Section', '시리즈별 콘텐츠 그룹'),
        ('F. Footer', '하단 정보 영역'),
    ]

    for comp, desc in components:
        add_text('    ')
        add_bold_text(comp)
        add_text(f' ─── {desc}')
        add_newline()

    add_newline()
    add_divider()

    # 섹션 3: 콘텐츠 카드 디자인
    add_heading2('3. 콘텐츠 카드 디자인')
    add_newline()

    add_text('📎 ', color={'red': 0.2, 'green': 0.5, 'blue': 0.9})
    add_bold_text('[이미지 삽입: 08-content-cards.png]')
    add_newline(2)

    add_heading3('3.0 디자인 의도 및 목적')
    add_newline()

    add_bold_text('핵심 목표: ')
    add_text('콘텐츠 정보를 빠르게 파악하고 시청 결정을 돕는 카드 시스템')
    add_newline(2)

    card_decisions = [
        ('16:9 썸네일', '영상 콘텐츠 표준 비율, 실제 장면 미리보기 제공'),
        ('진행률 바', '이어보기 위치 즉시 파악, 재시청 동기 부여'),
        ('메타 정보 표시', '핸드 수/액션 시간으로 콘텐츠 밀도 예측'),
        ('배지 시스템', 'NEW/4K/HD 등 콘텐츠 특성 즉시 인지'),
        ('호버 확대', '관심 콘텐츠 강조, 클릭 유도'),
    ]

    for title, desc in card_decisions:
        add_text('• ')
        add_bold_text(title)
        add_text(f' → {desc}')
        add_newline()

    add_newline()

    add_heading3('3.4 콘텐츠 상태 배지')
    add_newline()

    badges = [
        ('NEW', '빨강 #e50914', '7일 이내 추가'),
        ('4K', '금색 #ffc107', '4K 리마스터 콘텐츠'),
        ('HD', '회색 #666', '1080p 콘텐츠'),
        ('CC', '흰색 테두리', '자막 지원'),
    ]

    for badge, color_desc, condition in badges:
        add_text('• ')
        add_bold_text(badge)
        add_text(f' ({color_desc}) - {condition}')
        add_newline()

    add_newline()
    add_divider()

    # 섹션 4: 구독 전환 UX
    add_heading2('4. 구독 전환 UX')
    add_newline()

    add_text('📎 ', color={'red': 0.2, 'green': 0.5, 'blue': 0.9})
    add_bold_text('[이미지 삽입: 09-subscription.png]')
    add_newline(2)

    add_heading3('4.0 디자인 의도 및 목적')
    add_newline()

    add_bold_text('핵심 목표: ')
    add_text('비구독자를 자연스럽게 구독자로 전환')
    add_newline(2)

    sub_decisions = [
        ('소프트 Paywall', '콘텐츠 일부 노출로 관심 유발 후 구독 유도'),
        ('혜택 중심 메시지', '가격보다 가치를 먼저 전달'),
        ('연간 플랜 강조', 'LTV 극대화, 이탈률 감소'),
        ('원클릭 결제', 'Apple Pay/Google Pay로 전환 장벽 최소화'),
        ('미리보기 제공', '30초 미리보기로 콘텐츠 품질 확인 기회'),
    ]

    for title, desc in sub_decisions:
        add_text('• ')
        add_bold_text(title)
        add_text(f' → {desc}')
        add_newline()

    add_newline()

    add_bold_text('전환 퍼널:')
    add_newline(2)
    add_paragraph('    1. 인지 ──── 홈 브라우징 ──────── 잠금 콘텐츠 발견')
    add_paragraph('         ↓')
    add_paragraph('    2. 관심 ──── 잠금 콘텐츠 클릭 ──── 30초 미리보기 시청')
    add_paragraph('         ↓')
    add_paragraph('    3. 결정 ──── 미리보기 종료 ─────── Paywall 모달 표시')
    add_paragraph('         ↓')
    add_paragraph('    4. 전환 ──── CTA 클릭 ─────────── 구독 페이지 이동')
    add_newline()

    add_divider()

    # 섹션 5: Browse & Search
    add_heading2('5. Browse & Search 페이지')
    add_newline()

    add_text('📎 ', color={'red': 0.2, 'green': 0.5, 'blue': 0.9})
    add_bold_text('[이미지 삽입: 12-browse.png]')
    add_newline(2)

    add_heading3('5.0 디자인 의도 및 목적')
    add_newline()

    add_bold_text('핵심 목표: ')
    add_text('콘텐츠 탐색과 검색을 하나의 통합된 경험으로 제공')
    add_newline(2)

    browse_decisions = [
        ('통합 페이지', '검색과 브라우징을 분리하지 않고 컨텍스트 유지'),
        ('상태 기반 UI', '검색 활성화 여부에 따라 최적화된 레이아웃 표시'),
        ('필터 사이드바', '시리즈/연도/언어별 빠른 필터링'),
        ('실시간 검색', '타이핑 중 자동완성으로 탐색 시간 단축'),
    ]

    for title, desc in browse_decisions:
        add_text('• ')
        add_bold_text(title)
        add_text(f' → {desc}')
        add_newline()

    add_newline()
    add_divider()

    # 섹션 6: 플레이어 페이지
    add_heading2('6. 플레이어 페이지')
    add_newline()

    add_text('📎 ', color={'red': 0.2, 'green': 0.5, 'blue': 0.9})
    add_bold_text('[이미지 삽입: 13-player.png]')
    add_newline(2)

    add_heading3('6.0 디자인 의도 및 목적')
    add_newline()

    add_bold_text('핵심 목표: ')
    add_text('포커 VOD에 최적화된 시청 경험 제공')
    add_newline(2)

    player_decisions = [
        ('Hand Skip', '폴드/탱킹 구간 자동 스킵으로 액션만 시청'),
        ('Best Hands 패널', '에피소드 내 하이라이트 빠른 접근'),
        ('핸드 마커', '프로그레스 바에 핸드 시작점 시각화'),
        ('키보드 중심', 'N키로 다음 핸드, B키로 Best Hands'),
    ]

    for title, desc in player_decisions:
        add_text('• ')
        add_bold_text(title)
        add_text(f' → {desc}')
        add_newline()

    add_newline()

    add_heading3('6.2 키보드 단축키')
    add_newline()

    shortcuts = [
        ('Space', '재생/일시정지'),
        ('N', '다음 핸드로 스킵'),
        ('B', 'Best Hands 패널 토글'),
        ('F', '전체화면'),
        ('M', '음소거'),
    ]

    for key, action in shortcuts:
        add_text('• ')
        add_bold_text(key)
        add_text(f' - {action}')
        add_newline()

    add_newline()
    add_divider()

    # 섹션 7: 계정 페이지
    add_heading2('7. 계정 페이지')
    add_newline()

    add_text('📎 ', color={'red': 0.2, 'green': 0.5, 'blue': 0.9})
    add_bold_text('[이미지 삽입: 14-account.png]')
    add_newline(2)

    add_heading3('7.1 사이드바 메뉴')
    add_newline()

    menus = [
        ('👤 프로필', '사용자 정보 관리'),
        ('💳 구독 관리', '플랜, 결제 정보'),
        ('📺 시청 기록', '이어보기, 시청 완료'),
        ('⚙️ 설정', '재생, 자막, 알림'),
    ]

    for menu, desc in menus:
        add_text('• ')
        add_bold_text(menu)
        add_text(f' - {desc}')
        add_newline()

    add_newline()
    add_divider()

    # 섹션 8: 인증 페이지
    add_heading2('8. 인증 페이지')
    add_newline()

    add_text('📎 ', color={'red': 0.2, 'green': 0.5, 'blue': 0.9})
    add_bold_text('[이미지 삽입: 15-auth.png]')
    add_newline(2)

    add_heading3('8.0 디자인 의도 및 목적')
    add_newline()

    add_bold_text('핵심 목표: ')
    add_text('빠르고 안전한 인증 경험 제공')
    add_newline(2)

    auth_decisions = [
        ('소셜 로그인 우선', '가입 장벽 최소화'),
        ('인라인 유효성 검사', '실시간 입력 피드백'),
        ('비밀번호 강도 표시', '보안 의식 향상'),
        ('단계별 비밀번호 재설정', '명확한 진행 상태'),
    ]

    for title, desc in auth_decisions:
        add_text('• ')
        add_bold_text(title)
        add_text(f' → {desc}')
        add_newline()

    add_newline()

    add_heading3('8.3 비밀번호 재설정')
    add_newline()
    add_paragraph('3단계 프로세스로 진행됩니다.')
    add_newline()
    add_paragraph('    ① 이메일 입력 ──→ ② 인증 코드 ──→ ③ 새 비밀번호')
    add_paragraph('       가입된 이메일     6자리 코드      비밀번호 설정')
    add_paragraph('          확인            입력')
    add_newline()

    add_divider()

    # 섹션 9: 네비게이션 맵
    add_heading2('9. 네비게이션 맵')
    add_newline()

    add_text('📎 ', color={'red': 0.2, 'green': 0.5, 'blue': 0.9})
    add_bold_text('[이미지 삽입: 07-navigation.png]')
    add_newline(2)

    add_heading3('9.0 사이트 구조')
    add_newline()

    add_bold_text('주요 페이지:')
    add_newline(2)

    pages = [
        ('Home', '/', 'Public'),
        ('Browse', '/browse', 'Public'),
        ('Search', '/browse?q=', 'Public'),
        ('Watch', '/watch/:id', 'Auth Required'),
        ('Account', '/account', 'Auth Required'),
        ('Login', '/login', 'Public'),
        ('Register', '/register', 'Public'),
        ('Admin', '/admin', 'Admin Only'),
    ]

    for page, path, access in pages:
        add_text('• ')
        add_bold_text(page)
        add_text(f'  {path}  ({access})')
        add_newline()

    add_newline()

    add_heading3('9.2 사용자 흐름')
    add_newline()

    add_bold_text('신규 사용자 흐름:')
    add_newline()
    add_paragraph('Landing → Browse → Content Click → Paywall → Register → Subscribe → Watch')
    add_newline()

    add_bold_text('기존 사용자 흐름:')
    add_newline()
    add_paragraph('Home → Continue Watching Click → Watch (Resume) → Next Episode')
    add_newline()

    add_bold_text('검색 흐름:')
    add_newline()
    add_paragraph('Any Page → Search Icon → Search Input → Results → Content Click → Watch')
    add_newline()

    add_divider()

    add_bold_text('문서 끝')
    add_newline()
    add_paragraph('다음: 03-content-strategy.md')

    return requests


def main():
    print("WSOPTV UX Google Docs 문서 생성 시작...")

    # 문서 생성
    doc_id = create_document('WSOPTV - 사용자 경험 설계 v1.5.0')
    print(f"문서 생성 완료: {doc_id}")

    # 콘텐츠 추가
    requests = build_document_requests()
    add_content(doc_id, requests)
    print("콘텐츠 추가 완료")

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"\n문서 URL: {doc_url}")

    return doc_url


if __name__ == '__main__':
    main()
