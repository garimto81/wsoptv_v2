"""Update Google Docs with full UX document content."""
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
TOKEN_PATH = Path(r"D:\AI\claude01\json\token.json")
WIREFRAME_DIR = Path(r"D:\AI\claude01\wsoptv_v2\docs\wireframes\v2")
IMAGE_IDS_PATH = WIREFRAME_DIR / "image_ids.json"
GOOGLE_DOC_ID = "1tghlhpQiWttpB-0CP5c1DiL5BJa4ttWj-2R77xaoVI8"


def load_image_ids():
    """Load image IDs from JSON file."""
    if IMAGE_IDS_PATH.exists():
        with open(IMAGE_IDS_PATH) as f:
            return json.load(f)
    return {}


def get_credentials():
    """Load credentials from token.json."""
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)

    return Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )


def clear_document(docs_service, doc_id):
    """Clear all content from the document except the first character."""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])

    if len(content) <= 1:
        return

    end_index = 1
    for element in content:
        if "endIndex" in element:
            end_index = element["endIndex"]

    if end_index > 2:
        requests = [
            {
                "deleteContentRange": {
                    "range": {
                        "startIndex": 1,
                        "endIndex": end_index - 1,
                    }
                }
            }
        ]
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        print("  Document cleared")


class DocumentBuilder:
    """Helper class to build Google Docs content."""

    def __init__(self, image_ids: dict):
        self.requests = []
        self.current_index = 1
        self.image_ids = image_ids

    def add_text(self, text, heading=None, bold=False, italic=False, color=None):
        """Add text with optional styling."""
        self.requests.append({
            "insertText": {
                "location": {"index": self.current_index},
                "text": text,
            }
        })
        text_end = self.current_index + len(text)

        if heading:
            self.requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": self.current_index, "endIndex": text_end},
                    "paragraphStyle": {"namedStyleType": heading},
                    "fields": "namedStyleType",
                }
            })

        # Apply text styling
        text_style = {}
        fields = []

        if bold:
            text_style["bold"] = True
            fields.append("bold")
        if italic:
            text_style["italic"] = True
            fields.append("italic")
        if color:
            text_style["foregroundColor"] = {
                "color": {"rgbColor": color}
            }
            fields.append("foregroundColor")

        if text_style and len(text) > 1:
            self.requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": self.current_index, "endIndex": text_end - 1},
                    "textStyle": text_style,
                    "fields": ",".join(fields),
                }
            })

        self.current_index = text_end

    def add_image(self, image_key, width_pt=500):
        """Add image with center alignment."""
        image_id = self.image_ids.get(image_key)
        if not image_id:
            self.add_text(f"\n[Image: {image_key} - ID not found]\n")
            return

        uri = f"https://drive.google.com/uc?id={image_id}"

        # Insert image
        self.requests.append({
            "insertInlineImage": {
                "location": {"index": self.current_index},
                "uri": uri,
                "objectSize": {
                    "width": {"magnitude": width_pt, "unit": "PT"}
                },
            }
        })
        image_index = self.current_index
        self.current_index += 1

        # Center align the image paragraph
        self.requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": image_index, "endIndex": self.current_index},
                "paragraphStyle": {"alignment": "CENTER"},
                "fields": "alignment",
            }
        })

    def add_table_text(self, rows: list):
        """Add simple table as formatted text."""
        for row in rows:
            if isinstance(row, tuple) and len(row) >= 2:
                self.add_text(f"  {row[0]}: ", bold=True)
                self.add_text(f"{row[1]}\n")
            else:
                self.add_text(f"  {row}\n")

    def add_divider(self):
        """Add horizontal divider."""
        self.add_text("\n" + "─" * 60 + "\n\n")

    def get_requests(self):
        return self.requests


def build_full_document(image_ids: dict):
    """Build the complete UX document structure."""
    builder = DocumentBuilder(image_ids)

    # Title
    builder.add_text("WSOPTV - 사용자 경험 설계\n", heading="TITLE")
    builder.add_text("Version 1.5.1\n\n")
    builder.add_divider()

    # ========== Section 1: User Journey ==========
    builder.add_text("1. 사용자 여정 (User Journey)\n", heading="HEADING_1")

    builder.add_text("\n1.1 신규 사용자 여정\n", heading="HEADING_2")
    builder.add_text("\n진입 경로 1: YouTube (신규 유저층 확보)\n\n", bold=True)
    builder.add_image("mermaid-youtube-entry.png", width_pt=480)
    builder.add_text("\n\n진입 경로 2: WSOPTV 직접 접속\n\n", bold=True)
    builder.add_image("mermaid-direct-entry.png", width_pt=420)
    builder.add_text("\n\n")
    builder.add_text("투트랙 전략: ", bold=True)
    builder.add_text("YouTube는 신규 유저층이 많아 무료 콘텐츠(쇼츠, 하이라이트)로 유입을 유도합니다. WSOPTV는 구독자 전용 풀 에피소드 서비스입니다.\n\n")

    builder.add_text("\n1.2 기존 사용자 여정\n", heading="HEADING_2")
    builder.add_image("mermaid-existing-user.png", width_pt=450)
    builder.add_text("\n\n에피소드 내 기능:\n")
    builder.add_text("  • Hand Skip: 액션 구간만 빠르게 시청\n")
    builder.add_text("  • Best Hands: 에피소드별 하이라이트 점프\n\n")

    builder.add_divider()

    # ========== Section 2: Homepage Structure ==========
    builder.add_text("2. 홈페이지 구조\n", heading="HEADING_1")

    builder.add_text("\n2.0 디자인 의도 및 목적\n", heading="HEADING_2")
    builder.add_text("핵심 목표: ", bold=True)
    builder.add_text("포커 VOD 시청에 최적화된 몰입형 경험 제공\n\n")
    builder.add_text("디자인 결정:\n")
    builder.add_text("  • 다크 테마 - 장시간 시청 시 눈의 피로 감소\n")
    builder.add_text("  • Netflix 스타일 레이아웃 - 검증된 VOD 플랫폼 UX 패턴\n")
    builder.add_text("  • 가로 스크롤 카드 - 많은 콘텐츠를 공간 효율적으로 탐색\n")
    builder.add_text("  • Continue Watching 상단 배치 - 재방문 사용자의 즉시 시청 재개\n")
    builder.add_text("  • 시리즈 그룹핑 - WSOP/HCL 등 시리즈별 정주행 유도\n\n")

    builder.add_text("\n2.1 전체 화면 구성\n", heading="HEADING_2")
    builder.add_text("\nNetflix 스타일의 다크 테마 기반으로 설계된 WSOPTV 홈페이지 전체 구조입니다.\n\n")
    builder.add_image("00-full-page.png", width_pt=550)
    builder.add_text("\n\n페이지 구성 요소:\n")
    builder.add_text("  A. Header - 상단 고정 네비게이션\n")
    builder.add_text("  B. Hero Banner - 메인 추천 콘텐츠\n")
    builder.add_text("  C. Continue Watching - 이어보기 섹션\n")
    builder.add_text("  D. Recently Added - 최근 추가 콘텐츠\n")
    builder.add_text("  E. Series Section - 시리즈별 콘텐츠 그룹\n")
    builder.add_text("  F. Footer - 하단 정보 영역\n\n")

    # 2.2.1 Header
    builder.add_text("\n2.2.1 Header - 상단 고정 네비게이션\n", heading="HEADING_3")
    builder.add_image("01-header.png", width_pt=500)
    builder.add_text("\n\n핵심 스펙:\n")
    builder.add_text("  • 로고: 120×40px, #e50914 배경 → 클릭 시 홈 이동\n")
    builder.add_text("  • 네비게이션: gap 24px, 활성 흰색 + 언더라인\n")
    builder.add_text("  • 검색/프로필 아이콘: 36×36px\n")
    builder.add_text("  • 동작: position: fixed, z-index: 1000, 높이 64px\n\n")

    # 2.2.2 Hero Banner
    builder.add_text("\n2.2.2 Hero Banner - 메인 추천 콘텐츠\n", heading="HEADING_3")
    builder.add_image("02-hero-banner.png", width_pt=500)
    builder.add_text("\n\n핵심 스펙:\n")
    builder.add_text("  • 배지: NEW (#e50914), 4K (#ffc107)\n")
    builder.add_text("  • 제목: 36px, font-weight: 700, 최대 2줄\n")
    builder.add_text("  • 썸네일: 16:9, WebP, Lazy Load\n")
    builder.add_text("  • 인디케이터: 최대 5개, 5초 자동 전환\n\n")

    # 2.2.3 Continue Watching
    builder.add_text("\n2.2.3 Continue Watching - 이어보기 섹션\n", heading="HEADING_3")
    builder.add_image("03-continue-watching.png", width_pt=500)
    builder.add_text("\n\n핵심 스펙:\n")
    builder.add_text("  • 카드 그리드: 4열, gap: 12px\n")
    builder.add_text("  • 진행률 바: 높이 4px, #e50914\n")
    builder.add_text("  • 동작: 10초마다 위치 저장, 95% 시청 시 제거\n\n")

    # 2.2.4 Recently Added
    builder.add_text("\n2.2.4 Recently Added - 최근 추가 콘텐츠\n", heading="HEADING_3")
    builder.add_image("04-recently-added.png", width_pt=500)
    builder.add_text("\n\n핵심 스펙:\n")
    builder.add_text("  • 카드 그리드: 5열, gap: 10px\n")
    builder.add_text("  • 배지: NEW (7일 이내), 4K/HD/CC\n")
    builder.add_text("  • 호버: scale(1.05), box-shadow, 0.2s\n\n")

    # 2.2.5 Series Section
    builder.add_text("\n2.2.5 Series Section - 시리즈별 콘텐츠 그룹\n", heading="HEADING_3")
    builder.add_image("05-series-section.png", width_pt=500)
    builder.add_text("\n\n핵심 스펙:\n")
    builder.add_text("  • 레이아웃: 포스터 (2:3) + 에피소드 목록\n")
    builder.add_text("  • 에피소드: 최대 4개, 더보기 표시\n")
    builder.add_text("  • 재생시간: \"H:MM:SS\" 형식\n\n")

    # 2.2.6 Footer
    builder.add_text("\n2.2.6 Footer - 하단 정보 영역\n", heading="HEADING_3")
    builder.add_image("06-footer.png", width_pt=500)
    builder.add_text("\n\n핵심 스펙:\n")
    builder.add_text("  • 링크 그리드: 4열 (About, Support, Legal, Account)\n")
    builder.add_text("  • 소셜 링크: 36×36px, gap: 16px\n")
    builder.add_text("  • 반응형: Desktop 4열 > Tablet 2열 > Mobile 1열\n\n")

    builder.add_divider()

    # ========== Section 3: Content Cards ==========
    builder.add_text("3. 콘텐츠 카드 디자인\n", heading="HEADING_1")
    builder.add_image("08-content-cards.png", width_pt=500)

    builder.add_text("\n\n3.0 디자인 의도 및 목적\n", heading="HEADING_2")
    builder.add_text("핵심 목표: ", bold=True)
    builder.add_text("콘텐츠 정보를 빠르게 파악하고 시청 결정을 돕는 카드 시스템\n\n")
    builder.add_text("디자인 결정:\n")
    builder.add_text("  • 16:9 썸네일 - 영상 콘텐츠 표준 비율\n")
    builder.add_text("  • 진행률 바 - 이어보기 위치 즉시 파악\n")
    builder.add_text("  • 메타 정보 표시 - 핸드 수/액션 시간으로 콘텐츠 밀도 예측\n")
    builder.add_text("  • 배지 시스템 - NEW/4K/HD 등 콘텐츠 특성 즉시 인지\n\n")

    builder.add_text("\n3.1 에피소드 카드\n", heading="HEADING_2")
    builder.add_text("기본 콘텐츠 단위로, 하나의 완전한 에피소드를 표현합니다.\n")
    builder.add_text("  • 썸네일: 16:9, WebP, Lazy Load\n")
    builder.add_text("  • 재생시간: 우하단, 반투명 배경 (H:MM:SS)\n")
    builder.add_text("  • 시리즈명: 상단, 작은 텍스트\n")
    builder.add_text("  • 메타 정보: 하단, 회색 텍스트 (47 Hands / 52m Action)\n\n")

    builder.add_text("\n3.2 Best Hand 카드\n", heading="HEADING_2")
    builder.add_text("에피소드 내 하이라이트 핸드를 표현합니다.\n")
    builder.add_text("  • 액션 배지: 좌상단, #e50914 (All-in, Bluff, Bad Beat)\n")
    builder.add_text("  • 타임스탬프: 배지 옆 (▶ 2:34)\n")
    builder.add_text("  • 핸드 제목: 중앙 (AA vs KK)\n")
    builder.add_text("  • 팟 사이즈: 우하단, 금색 ($2.3M Pot)\n\n")

    builder.add_text("\n3.3 이어보기 카드\n", heading="HEADING_2")
    builder.add_text("사용자가 시청 중인 콘텐츠를 표현합니다.\n")
    builder.add_text("  • 재생 버튼: 중앙 오버레이 (▶ Resume)\n")
    builder.add_text("  • 진행률 바: 하단, 4px, #e50914\n")
    builder.add_text("  • 남은 시간: 빨간색 텍스트 (45:23 remaining)\n\n")

    builder.add_text("\n3.4 콘텐츠 상태 배지\n", heading="HEADING_2")
    builder.add_text("  • NEW (#e50914 빨강) - 7일 이내 추가\n")
    builder.add_text("  • 4K (#ffc107 금색) - 4K 리마스터 콘텐츠\n")
    builder.add_text("  • HD (#666 회색) - 1080p 콘텐츠\n")
    builder.add_text("  • CC (#fff 흰색 테두리) - 자막 지원\n\n")

    builder.add_divider()

    # ========== Section 4: Subscription UX ==========
    builder.add_text("4. 구독 전환 UX\n", heading="HEADING_1")
    builder.add_image("09-subscription.png", width_pt=500)

    builder.add_text("\n\n4.0 디자인 의도 및 목적\n", heading="HEADING_2")
    builder.add_text("핵심 목표: ", bold=True)
    builder.add_text("비구독자를 자연스럽게 구독자로 전환\n\n")
    builder.add_text("디자인 결정:\n")
    builder.add_text("  • 소프트 Paywall - 콘텐츠 일부 노출로 관심 유발 후 구독 유도\n")
    builder.add_text("  • 혜택 중심 메시지 - 가격보다 가치를 먼저 전달\n")
    builder.add_text("  • 연간 플랜 강조 - LTV 극대화, 이탈률 감소\n")
    builder.add_text("  • 원클릭 결제 - Apple Pay/Google Pay로 전환 장벽 최소화\n\n")

    builder.add_text("\n4.1 Paywall 화면\n", heading="HEADING_2")
    builder.add_text("비구독자가 유료 콘텐츠 클릭 시 표시됩니다.\n\n")
    builder.add_text("레이아웃:\n")
    builder.add_text("  • 배경: 클릭한 콘텐츠 썸네일 (블러 처리)\n")
    builder.add_text("  • 아이콘: 자물쇠\n")
    builder.add_text("  • 메시지: \"이 콘텐츠는 Premium 구독자 전용입니다\"\n")
    builder.add_text("  • CTA: \"Premium 시작하기\" 버튼\n")
    builder.add_text("  • 가격: $9.99/월 또는 $99/년\n\n")
    builder.add_text("Premium 혜택:\n")
    builder.add_text("  • 전체 아카이브: 18TB+ WSOP/HCL/GGPoker 콘텐츠\n")
    builder.add_text("  • Hand Skip: 액션 구간만 빠르게 시청\n")
    builder.add_text("  • Best Hands: 에피소드별 하이라이트 점프\n")
    builder.add_text("  • 이어보기 동기화: 모든 기기에서 시청 위치 유지\n")
    builder.add_text("  • 광고 없음: 끊김 없는 시청 경험\n\n")

    builder.add_text("\n4.2 구독 페이지\n", heading="HEADING_2")
    builder.add_text("플랜 비교:\n")
    builder.add_text("  • Monthly: $9.99/월\n")
    builder.add_text("  • Yearly (추천): $99/년 ($8.25/월) - 17% 절약, BEST VALUE 배지\n\n")
    builder.add_text("결제 수단:\n")
    builder.add_text("  • Credit Card (기본)\n")
    builder.add_text("  • Apple Pay (iOS 우선 표시)\n")
    builder.add_text("  • Google Pay (Android 우선 표시)\n\n")

    builder.add_divider()

    # ========== Section 5: Browse & Search ==========
    builder.add_text("5. Browse & Search 페이지\n", heading="HEADING_1")
    builder.add_image("12-browse.png", width_pt=500)

    builder.add_text("\n\n5.0 디자인 의도 및 목적\n", heading="HEADING_2")
    builder.add_text("핵심 목표: ", bold=True)
    builder.add_text("콘텐츠 탐색과 검색을 하나의 통합된 경험으로 제공\n\n")
    builder.add_text("디자인 결정:\n")
    builder.add_text("  • 통합 페이지 - 검색과 브라우징을 분리하지 않고 컨텍스트 유지\n")
    builder.add_text("  • 상태 기반 UI - 검색 활성화 여부에 따라 최적화된 레이아웃\n")
    builder.add_text("  • 필터 사이드바 - 시리즈/연도/언어별 빠른 필터링\n")
    builder.add_text("  • 실시간 검색 - 타이핑 중 자동완성으로 탐색 시간 단축\n\n")

    builder.add_text("\n5.1 기본 상태 (Grid View)\n", heading="HEADING_2")
    builder.add_text("검색어 없이 페이지 접근 시 기본 레이아웃입니다.\n")
    builder.add_text("  • 검색 바: 상단 고정\n")
    builder.add_text("  • 필터 사이드바: 좌측 (시리즈/연도/언어 필터)\n")
    builder.add_text("  • 콘텐츠 그리드: 4열 카드 그리드\n")
    builder.add_text("  • 정렬 옵션: 최신순, 인기순, 제목순\n\n")
    builder.add_text("필터 카테고리:\n")
    builder.add_text("  • 시리즈: WSOP, HCL, GGPoker, PAD, MPP 등\n")
    builder.add_text("  • 연도: 2024, 2023, 2022...\n")
    builder.add_text("  • 언어: 영어, 한국어 자막\n")
    builder.add_text("  • 품질: 4K, HD\n\n")

    builder.add_text("\n5.2 검색 활성 상태 (List View)\n", heading="HEADING_2")
    builder.add_text("검색어 입력 시 리스트 뷰로 전환됩니다.\n")
    builder.add_text("  • 자동완성: 최대 5개 추천 결과\n")
    builder.add_text("  • 검색 결과 수: \"'검색어' 검색 결과: N개\"\n")
    builder.add_text("  • 결과 목록: 리스트 형식, 상세 정보 표시\n\n")

    builder.add_divider()

    # ========== Section 6: Player Page ==========
    builder.add_text("6. 플레이어 페이지\n", heading="HEADING_1")
    builder.add_image("13-player.png", width_pt=500)

    builder.add_text("\n\n6.0 디자인 의도 및 목적\n", heading="HEADING_2")
    builder.add_text("핵심 목표: ", bold=True)
    builder.add_text("포커 VOD에 최적화된 시청 경험 제공\n\n")
    builder.add_text("디자인 결정:\n")
    builder.add_text("  • Hand Skip - 폴드/탱킹 구간 자동 스킵으로 액션만 시청\n")
    builder.add_text("  • Best Hands 패널 - 에피소드 내 하이라이트 빠른 접근\n")
    builder.add_text("  • 핸드 마커 - 프로그레스 바에 핸드 시작점 시각화\n")
    builder.add_text("  • 키보드 중심 - N키로 다음 핸드, B키로 Best Hands\n\n")

    builder.add_text("\n6.1 플레이어 컨트롤\n", heading="HEADING_2")
    builder.add_text("기본 컨트롤:\n")
    builder.add_text("  • 재생/일시정지: 중앙 대형 버튼\n")
    builder.add_text("  • 프로그레스 바: 드래그로 탐색, 핸드 마커 표시\n")
    builder.add_text("  • 볼륨: 슬라이더 + 음소거 버튼\n")
    builder.add_text("  • 전체화면: 우측 버튼\n\n")
    builder.add_text("포커 전용 컨트롤:\n")
    builder.add_text("  • Hand Skip (ON/OFF): 다음 핸드까지 남은 시간 표시\n")
    builder.add_text("  • Best Hands (ON/OFF): 하이라이트 개수 표시\n\n")

    builder.add_text("\n6.2 Best Hands 패널\n", heading="HEADING_2")
    builder.add_text("  • 핸드 카드: 썸네일 + 액션 배지 + 타임스탬프\n")
    builder.add_text("  • 플레이어 정보: 대결 구도 (vs)\n")
    builder.add_text("  • 팟 사이즈: 금색 강조\n")
    builder.add_text("  • 클릭 동작: 해당 시점으로 점프\n\n")
    builder.add_text("키보드 단축키:\n")
    builder.add_text("  • Space: 재생/일시정지\n")
    builder.add_text("  • N: 다음 핸드로 스킵\n")
    builder.add_text("  • B: Best Hands 패널 토글\n")
    builder.add_text("  • F: 전체화면\n")
    builder.add_text("  • M: 음소거\n\n")

    builder.add_divider()

    # ========== Section 7: Account Page ==========
    builder.add_text("7. 계정 페이지\n", heading="HEADING_1")
    builder.add_image("14-account.png", width_pt=500)

    builder.add_text("\n\n7.0 디자인 의도 및 목적\n", heading="HEADING_2")
    builder.add_text("핵심 목표: ", bold=True)
    builder.add_text("계정 관리 기능을 직관적인 탭 구조로 제공\n\n")
    builder.add_text("디자인 결정:\n")
    builder.add_text("  • 사이드바 네비게이션 - 섹션별 빠른 접근\n")
    builder.add_text("  • 프로필 우선 - 가장 자주 사용하는 정보 상단 배치\n")
    builder.add_text("  • 구독 상태 강조 - 현재 플랜과 갱신일 명확히 표시\n")
    builder.add_text("  • 시청 기록 통합 - 이어보기와 시청 완료 구분\n\n")

    builder.add_text("\n7.1 사이드바 메뉴\n", heading="HEADING_2")
    builder.add_text("  • 프로필 - 사용자 정보 관리\n")
    builder.add_text("  • 구독 관리 - 플랜, 결제 정보\n")
    builder.add_text("  • 시청 기록 - 이어보기, 시청 완료 목록\n")
    builder.add_text("  • 설정 - 재생, 자막, 알림 설정\n\n")

    builder.add_text("\n7.2 각 섹션 상세\n", heading="HEADING_2")
    builder.add_text("프로필:\n")
    builder.add_text("  • 프로필 이미지, 이름, 이메일, 비밀번호 변경\n\n")
    builder.add_text("구독 관리:\n")
    builder.add_text("  • 현재 플랜 (Premium/Free), 다음 결제일, 결제 수단\n\n")
    builder.add_text("시청 기록:\n")
    builder.add_text("  • 이어보기 탭: 진행 중인 콘텐츠\n")
    builder.add_text("  • 시청 완료 탭: 완료된 콘텐츠\n\n")
    builder.add_text("설정:\n")
    builder.add_text("  • 재생: 자동 재생, 품질, Hand Skip 기본값\n")
    builder.add_text("  • 자막: 언어, 크기, 스타일\n")
    builder.add_text("  • 알림: 새 콘텐츠, 이메일 수신\n\n")

    builder.add_divider()

    # ========== Section 8: Auth Page ==========
    builder.add_text("8. 인증 페이지\n", heading="HEADING_1")
    builder.add_image("15-auth.png", width_pt=500)

    builder.add_text("\n\n8.0 디자인 의도 및 목적\n", heading="HEADING_2")
    builder.add_text("핵심 목표: ", bold=True)
    builder.add_text("빠르고 안전한 인증 경험 제공\n\n")
    builder.add_text("디자인 결정:\n")
    builder.add_text("  • 소셜 로그인 우선 - 가입 장벽 최소화\n")
    builder.add_text("  • 인라인 유효성 검사 - 실시간 입력 피드백\n")
    builder.add_text("  • 비밀번호 강도 표시 - 보안 의식 향상\n")
    builder.add_text("  • 단계별 비밀번호 재설정 - 명확한 진행 상태\n\n")

    builder.add_text("\n8.1 로그인\n", heading="HEADING_2")
    builder.add_text("  • 소셜 로그인: Apple, Google 버튼\n")
    builder.add_text("  • 구분선: \"또는 이메일로 로그인\"\n")
    builder.add_text("  • 이메일/비밀번호 입력 (유효성 검사)\n")
    builder.add_text("  • 로그인 유지 체크박스\n")
    builder.add_text("  • 비밀번호 찾기, 회원가입 링크\n\n")

    builder.add_text("\n8.2 회원가입\n", heading="HEADING_2")
    builder.add_text("  • 기본 정보: 이름, 이메일\n")
    builder.add_text("  • 보안: 비밀번호 (강도 표시), 비밀번호 확인\n")
    builder.add_text("  • 동의: 서비스 약관, 개인정보 처리방침\n\n")
    builder.add_text("비밀번호 요구사항:\n")
    builder.add_text("  • 최소 8자\n")
    builder.add_text("  • 대문자, 소문자, 숫자 포함\n")
    builder.add_text("  • 강도 표시 (약함/보통/강함)\n\n")

    builder.add_text("\n8.3 비밀번호 재설정\n", heading="HEADING_2")
    builder.add_text("3단계 프로세스:\n")
    builder.add_text("  1. 이메일 입력 - 가입된 이메일 확인\n")
    builder.add_text("  2. 인증 코드 - 이메일로 전송된 6자리 코드 입력\n")
    builder.add_text("  3. 새 비밀번호 - 새 비밀번호 설정\n\n")

    builder.add_divider()

    # ========== Section 9: Navigation Map ==========
    builder.add_text("9. 네비게이션 맵\n", heading="HEADING_1")
    builder.add_image("07-navigation.png", width_pt=500)

    builder.add_text("\n\n9.0 사이트 구조\n", heading="HEADING_2")
    builder.add_text("주요 페이지:\n")
    builder.add_text("  • Home (/) - Public\n")
    builder.add_text("  • Browse (/browse) - Public\n")
    builder.add_text("  • Search (/browse?q=) - Public\n")
    builder.add_text("  • Watch (/watch/:id) - Auth Required\n")
    builder.add_text("  • Account (/account) - Auth Required\n")
    builder.add_text("  • Login (/login) - Public\n")
    builder.add_text("  • Register (/register) - Public\n")
    builder.add_text("  • Admin (/admin) - Admin Only\n\n")

    builder.add_text("\n9.1 글로벌 네비게이션\n", heading="HEADING_2")
    builder.add_text("Desktop 헤더:\n")
    builder.add_text("  [Logo] [Home] [Browse] [Search] [검색아이콘] [프로필]\n\n")
    builder.add_text("Mobile 바텀 탭:\n")
    builder.add_text("  [Home] [Browse] [Search] [Account]\n\n")
    builder.add_text("프로필 드롭다운:\n")
    builder.add_text("  • 프로필 → /account\n")
    builder.add_text("  • 구독 관리 → /account/subscription\n")
    builder.add_text("  • 시청 기록 → /account/history\n")
    builder.add_text("  • 설정 → /account/settings\n")
    builder.add_text("  • 로그아웃\n\n")

    builder.add_text("\n9.2 사용자 흐름\n", heading="HEADING_2")
    builder.add_text("신규 사용자:\n")
    builder.add_text("  Landing → Browse → Content Click → Paywall → Register → Subscribe → Watch\n\n")
    builder.add_text("기존 사용자:\n")
    builder.add_text("  Home → Continue Watching Click → Watch (Resume) → Next Episode\n\n")
    builder.add_text("검색 흐름:\n")
    builder.add_text("  Any Page → Search Icon → Search Input → Results → Content Click → Watch\n\n")

    builder.add_text("\n9.3 접근 제어\n", heading="HEADING_2")
    builder.add_text("  • Home, Browse: 모든 사용자\n")
    builder.add_text("  • Watch (Preview): 30초 미리보기\n")
    builder.add_text("  • Watch (Full): Premium 구독자만\n")
    builder.add_text("  • Account: 로그인 필요\n")
    builder.add_text("  • Admin: 관리자만\n\n")

    builder.add_divider()
    builder.add_text("\n— End of Document —\n")

    return builder.get_requests()


def main():
    """Main function."""
    print("Loading credentials...")
    creds = get_credentials()

    print("Loading image IDs...")
    image_ids = load_image_ids()
    print(f"  Found {len(image_ids)} image IDs")

    print("\nBuilding Docs service...")
    docs_service = build("docs", "v1", credentials=creds)

    print("\nClearing existing document...")
    clear_document(docs_service, GOOGLE_DOC_ID)

    print("Building full document structure (9 sections)...")
    requests = build_full_document(image_ids)

    print(f"Applying {len(requests)} updates to document...")

    # Batch requests in chunks to avoid API limits
    chunk_size = 100
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i:i + chunk_size]
        docs_service.documents().batchUpdate(
            documentId=GOOGLE_DOC_ID, body={"requests": chunk}
        ).execute()
        print(f"  Applied requests {i+1} to {min(i + chunk_size, len(requests))}")

    print(f"\nDocument updated successfully!")
    print(f"View at: https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit")


if __name__ == "__main__":
    main()
