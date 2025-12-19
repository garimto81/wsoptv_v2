"""Upload Content Strategy document to Google Docs.

Converts 03-content-strategy-gdocs.md to Google Docs format.
"""
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
TOKEN_PATH = Path(r"D:\AI\claude01\json\token.json")
WIREFRAME_DIR = Path(r"D:\AI\claude01\wsoptv_v2\docs\wireframes\v2")
IMAGE_IDS_PATH = WIREFRAME_DIR / "image_ids.json"

# Create a NEW Google Doc for Content Strategy
# This will be set after creating the document
GOOGLE_DOC_ID = None


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

    def add_divider(self):
        """Add horizontal divider."""
        self.add_text("\n" + "─" * 60 + "\n\n")

    def get_requests(self):
        return self.requests


def build_content_strategy_document(image_ids: dict):
    """Build the Content Strategy document structure."""
    builder = DocumentBuilder(image_ids)

    # ========== Title ==========
    builder.add_text("WSOPTV 콘텐츠 전략\n", heading="TITLE")
    builder.add_text("Version 4.0.0 | Google Docs 최적화 버전\n\n")
    builder.add_divider()

    # ========== Executive Summary ==========
    builder.add_text("포커의 50년 역사, 하나의 플랫폼\n", heading="HEADING_1")
    builder.add_text("\n18TB+ 아카이브 • 1973년부터 현재까지 • 세계 유일의 WSOP 공식 OTT\n\n")

    builder.add_text("Executive Summary\n", heading="HEADING_2")
    builder.add_text("\nWSOPTV는 세계 최고 권위의 포커 대회 ")
    builder.add_text("WSOP(World Series of Poker)", bold=True)
    builder.add_text("의 50년 역사를 담은 ")
    builder.add_text("유일한 공식 스트리밍 플랫폼", bold=True)
    builder.add_text("입니다.\n\n")

    builder.add_text("1970년 Benny Binion이 7명의 전설적 플레이어를 모아 시작한 WSOP는, 오늘날 매년 10,000명 이상이 참가하는 ")
    builder.add_text("포커의 올림픽", bold=True)
    builder.add_text("으로 성장했습니다.\n\n")

    builder.add_text("핵심 지표\n", heading="HEADING_3")
    builder.add_text("• 아카이브 규모: 18TB+ (50년 역사)\n")
    builder.add_text("• 연간 콘텐츠: 80+ 브레이슬릿\n")
    builder.add_text("• 메인 이벤트 참가자: 10,000명+ (2024)\n")
    builder.add_text("• 최대 우승 상금: $12.1M (2023)\n\n")

    builder.add_divider()

    # ========== Section 1: 왜 WSOP인가 ==========
    builder.add_text("1. 왜 WSOP인가: 포커의 최고봉\n", heading="HEADING_1")

    builder.add_text("\n1.1 브레이슬릿의 무게\n", heading="HEADING_2")
    builder.add_text("\n\"WSOP 브레이슬릿은 포커의 올림픽 금메달이다.\"\n\n", italic=True)
    builder.add_text("1976년 Benny Binion이 도입한 ")
    builder.add_text("WSOP 금 브레이슬릿", bold=True)
    builder.add_text("은 단순한 상이 아닙니다. 이것은 포커 플레이어가 평생을 바쳐 추구하는 ")
    builder.add_text("궁극의 증명", bold=True)
    builder.add_text("입니다.\n\n")

    builder.add_text("포커 커뮤니티에서 플레이어의 위상은 명확하게 구분됩니다—")
    builder.add_text("브레이슬릿 보유자와 미보유자", bold=True)
    builder.add_text(".\n\n")

    builder.add_text("역대 브레이슬릿 레전드\n", heading="HEADING_3")
    builder.add_text("• Phil Hellmuth (17개) - \"Poker Brat\", 5개 decade 우승\n")
    builder.add_text("• Phil Ivey (11개) - \"Tiger Woods of Poker\", 최빠름 달성\n")
    builder.add_text("• Doyle Brunson (10개) - 포커의 대부, 메인 2연속 우승\n")
    builder.add_text("• Johnny Chan (10개) - 영화 Rounders의 실제 주인공\n")
    builder.add_text("• Daniel Negreanu (7개) - \"Kid Poker\", 올타임 머니 리더\n\n")

    builder.add_text("\n1.2 Moneymaker Effect: 포커 산업의 혁명\n", heading="HEADING_2")
    builder.add_text("\n2003년, 테네시주의 평범한 회계사 ")
    builder.add_text("Chris Moneymaker", bold=True)
    builder.add_text("가 포커 역사를 바꿨습니다.\n\n")

    builder.add_text("Moneymaker의 여정\n", heading="HEADING_3")
    builder.add_text("$86 온라인 예선 → 예선 통과 → $10,000 메인 이벤트 시드 획득\n")
    builder.add_text("→ 839명 중 생존 → 파이널 테이블 진출 → ")
    builder.add_text("$2,500,000 우승!\n\n", bold=True)

    builder.add_text("포커 붐 촉발 효과\n", heading="HEADING_3")
    builder.add_text("• 2003년: 839명 → 2006년: 8,773명 → 2024년: 10,117명\n")
    builder.add_text("• ")
    builder.add_text("12배 성장", bold=True)
    builder.add_text(" - 온라인 포커 플랫폼 폭발적 성장\n")
    builder.add_text("• ESPN 홀카드 카메라 도입으로 시청 경험 혁신\n")
    builder.add_text("• 일반인의 \"나도 할 수 있다\" 인식 확산\n\n")

    builder.add_text("\"평범한 이름이 전설이 된 유일무이한 사례. Moneymaker는 역대 가장 영향력 있는 포커 플레이어다.\"\n\n", italic=True)

    builder.add_divider()

    # ========== Section 2: 콘텐츠 왕국 ==========
    builder.add_text("2. 콘텐츠 왕국: 무엇이 있는가\n", heading="HEADING_1")

    builder.add_text("\n2.1 콘텐츠 구성 비율\n", heading="HEADING_2")
    builder.add_text("\nWSOPTV 콘텐츠의 ")
    builder.add_text("80%는 WSOP Las Vegas", bold=True)
    builder.add_text("에서 생산됩니다. 매년 5월부터 7월까지, 50일간 벌어지는 포커의 축제가 우리의 핵심 자산입니다.\n\n")

    # Content pie chart image
    builder.add_image("cs-content-pie.png", width_pt=400)
    builder.add_text("\n\n전체 콘텐츠 구성\n", heading="HEADING_3")
    builder.add_text("• WSOP Las Vegas (80%) - Main Event, Bracelet, Best\n")
    builder.add_text("• 기타 대회 (10%) - Paradise, Europe, Circuit\n")
    builder.add_text("• 오리지널 (10%) - Game of Gold, Documentary\n\n")

    builder.add_text("\n2.2 WSOP Las Vegas 상세\n", heading="HEADING_2")
    builder.add_text("\n매년 5-7월, 라스베이거스에서 ")
    builder.add_text("80개 이상의 브레이슬릿 이벤트", bold=True)
    builder.add_text("가 펼쳐집니다.\n\n")

    # Main Event structure image
    builder.add_image("cs-main-event.png", width_pt=450)
    builder.add_text("\n\n")

    builder.add_text("Main Event (35%)\n", heading="HEADING_3")
    builder.add_text("$10,000 No-Limit Hold'em Championship—포커의 꿈이 현실이 되는 무대.\n")
    builder.add_text("• 참가자: 8,000~10,000명\n")
    builder.add_text("• 기간: 10일+\n")
    builder.add_text("• 우승 상금: $10M+ (2024 기준)\n\n")

    builder.add_text("Bracelet Events (30%)\n", heading="HEADING_3")
    builder.add_text("80개 이상의 독립 챔피언십. 각 이벤트는 해당 분야의 세계 최강자를 가립니다.\n")
    builder.add_text("• No-Limit Hold'em: $1,500 NLH, $3,000 NLH, $5,000 NLH\n")
    builder.add_text("• Pot-Limit Omaha: $1,500 PLO, $10K PLO Championship\n")
    builder.add_text("• Mixed Games: $50K PPC, HORSE\n")
    builder.add_text("• Special Events: Ladies, Seniors, Tag Team\n\n")

    builder.add_text("Best Hands 큐레이션 (15%)\n", heading="HEADING_3")
    builder.add_text("포커의 가장 순수한 순간들만 정제한 하이라이트 컬렉션.\n")
    builder.add_text("• All-in Showdowns: 올인 후 런아웃의 극적인 드라마\n")
    builder.add_text("• Bluff Catches: 용기 있는 콜로 상대의 블러프를 잡아내는 순간\n")
    builder.add_text("• Hero Calls/Folds: 역사에 남을 명장면\n")
    builder.add_text("• Monster Pots: $500K 이상의 거액 팟\n\n")

    builder.add_text("\n2.3 기타 대회 (10%)\n", heading="HEADING_2")
    # Other events image
    builder.add_image("cs-other-events.png", width_pt=400)
    builder.add_text("\n\n")
    builder.add_text("• WSOP Paradise (12월) - 바하마, $25K Buy-in\n")
    builder.add_text("• WSOP Europe (4월) - 유럽 메이저\n")
    builder.add_text("• Super Circuit (연중) - Cyprus, Canada 등\n\n")

    builder.add_text("\n2.4 오리지널 콘텐츠 (10%)\n", heading="HEADING_2")
    builder.add_text("• Game of Gold - 포커 리얼리티 쇼\n")
    builder.add_text("• Player Story - 레전드 플레이어 다큐멘터리\n\n")

    builder.add_divider()

    # ========== Section 3: 차별화 전략 ==========
    builder.add_text("3. 차별화 전략: YouTube vs WSOPTV\n", heading="HEADING_1")

    builder.add_text("\n3.1 투트랙 전략\n", heading="HEADING_2")
    builder.add_text("\n\"YouTube는 미끼, WSOPTV는 풀코스.\"\n\n", italic=True)
    builder.add_text("WSOPTV의 핵심 전략은 ")
    builder.add_text("투트랙 콘텐츠 배포", bold=True)
    builder.add_text("입니다.\n\n")

    # YouTube vs WSOPTV comparison image
    builder.add_image("cs-youtube-wsoptv.png", width_pt=450)
    builder.add_text("\n\n")

    builder.add_text("\n3.2 기능 비교표\n", heading="HEADING_2")
    builder.add_text("\n")
    builder.add_text("YouTube (무료)\n", bold=True)
    builder.add_text("• 생방송 ✓\n")
    builder.add_text("• 쇼츠/클립 ✓\n")
    builder.add_text("• 풀 에피소드 ✗\n")
    builder.add_text("• Hand Skip ✗\n")
    builder.add_text("• Best Hands ✗\n")
    builder.add_text("• 4K Remaster ✗\n\n")

    builder.add_text("WSOPTV (구독)\n", bold=True)
    builder.add_text("• 생방송 ✓\n")
    builder.add_text("• 풀 에피소드 ✓ (독점)\n")
    builder.add_text("• Hand Skip ✓ (혁신)\n")
    builder.add_text("• Best Hands ✓ (독점)\n")
    builder.add_text("• 4K Remaster ✓ (독점)\n\n")

    builder.add_text("\n3.3 WSOPTV 독점 기능 상세\n", heading="HEADING_2")

    builder.add_text("\n기능 1: Hand Skip (시간 효율화)\n", heading="HEADING_3")
    builder.add_text("문제: 포커는 흥미로운 핸드와 평범한 핸드가 섞여 있음\n\n")
    builder.add_text("• 일반 영상: 3시간, 모든 핸드, 선택적 시청\n")
    builder.add_text("• Hand Skip: 45분, 액션 핸드만, 논스톱 액션\n\n")
    builder.add_text("Hand Skip 우위:\n")
    builder.add_text("• 바쁜 포커 팬: 3시간 → 45분으로 단시간 몰아보기\n")
    builder.add_text("• 교육용: 핵심 전략만 집중\n")
    builder.add_text("• 리플레이: 명경기의 모든 극적 순간 재경험\n\n")

    builder.add_text("\n기능 2: Best Hands 컬렉션 (큐레이션)\n", heading="HEADING_3")
    builder.add_text("50년 WSOP 역사에서 엄선한 가장 극적인 순간들\n\n")
    builder.add_text("선정 기준 가중치:\n")
    builder.add_text("• Pot Size (거액 팟): 25%\n")
    builder.add_text("• Drama (극적 상황): 25%\n")
    builder.add_text("• Skill Display (기술력): 20%\n")
    builder.add_text("• Player Fame (플레이어 인지도): 15%\n")
    builder.add_text("• Outcome (예상 외 결과): 15%\n\n")

    builder.add_text("\n기능 3: 4K Remaster (아카이브 복원)\n", heading="HEADING_3")
    builder.add_text("대상: 1973~2010년 클래식 영상 (SD 화질)\n\n")
    builder.add_text("• 원본: SD (480p), 저화질, 색감 감퇴\n")
    builder.add_text("• 4K Remaster: 4K (2160p), 선명함, 색감 복원\n\n")

    builder.add_divider()

    # ========== Section 4: 콘텐츠 캘린더 ==========
    builder.add_text("4. 콘텐츠 캘린더\n", heading="HEADING_1")

    builder.add_text("\n4.1 연간 시즌 구조\n", heading="HEADING_2")
    builder.add_text("\nWSOPTV의 콘텐츠 흐름은 ")
    builder.add_text("5월~7월의 WSOP Las Vegas 시즌", bold=True)
    builder.add_text("을 중심으로 설계됩니다.\n\n")

    # Season calendar image
    builder.add_image("cs-season-calendar.png", width_pt=500)
    builder.add_text("\n\n")

    builder.add_text("\n4.2 분기별 콘텐츠 흐름\n", heading="HEADING_2")
    builder.add_text("• Q1 (1~3월): 비시즌 + Cyprus Circuit - 10%\n")
    builder.add_text("• Q2 (4월): WSOP Europe - 5%\n")
    builder.add_text("• Q2-Q3 (5~7월): ★ WSOP Las Vegas ★ - 80%\n")
    builder.add_text("• Q3 (8~9월): 비시즌 - 2%\n")
    builder.add_text("• Q4 (10~12월): Canada + Paradise - 3%\n\n")

    builder.add_text("\n4.3 피크 시즌 상세 (5월~7월)\n", heading="HEADING_2")
    builder.add_text("\n")
    builder.add_text("이 3개월이 연간 콘텐츠의 80%를 차지합니다.\n\n", bold=True)
    builder.add_text("• Week 1-2: Main Event Day 1A-1C → 풀 에피소드 3개, Hand Skip\n")
    builder.add_text("• Week 2-3: Main Event Day 2-3 → 풀 에피소드 2개, 분석\n")
    builder.add_text("• Week 3-4: Main Event Day 4-5 → 풀 에피소드 2개, Best Hands\n")
    builder.add_text("• Week 4-6: Bracelet Events → 이벤트별 파이널 테이블\n")
    builder.add_text("• Week 6-8: Bracelet 완주 → $50K PPC, HORSE, 스페셜\n")
    builder.add_text("• Week 8-9: 시즌 피날레 → 연간 Best Hands 집계\n")
    builder.add_text("• Week 9-10: 아카이브 배치 → 4K Remaster, 클래식 재편성\n\n")

    builder.add_text("피크 시즌 콘텐츠 배출량:\n", bold=True)
    builder.add_text("• 주당 평균: 15~20개 에피소드\n")
    builder.add_text("• 총 콘텐츠: 약 150~160개 풀 에피소드\n")
    builder.add_text("• Hand Skip 버전: 각 에피소드당 별도 제작\n\n")

    builder.add_divider()

    # ========== Section 5: 서비스 진화 로드맵 ==========
    builder.add_text("5. 서비스 진화 로드맵\n", heading="HEADING_1")

    builder.add_text("\n5.1 4단계 진화\n", heading="HEADING_2")

    # Curation roadmap image
    builder.add_image("cs-curation-roadmap.png", width_pt=500)
    builder.add_text("\n\n")

    builder.add_text("Phase 1: MVP\n", heading="HEADING_3")
    builder.add_text("• 전체 18TB+ 아카이브 OTT 서비스 런칭\n")
    builder.add_text("• 이어보기 기능으로 지속적인 시청 경험 제공\n\n")

    builder.add_text("Phase 2: 개인화\n", heading="HEADING_3")
    builder.add_text("• 시청 이력 기반 프로필별 추천\n")
    builder.add_text("• 플레이어/이벤트/시대별 카테고리 추천\n\n")

    builder.add_text("Phase 3: 차별화\n", heading="HEADING_3")
    builder.add_text("• Hand Skip: 3시간 에피소드를 45분 액션 하이라이트로\n")
    builder.add_text("• Best Hands: 50년 역사에서 선별한 극적 순간 컬렉션\n\n")

    builder.add_text("Phase 4: 프리미엄\n", heading="HEADING_3")
    builder.add_text("• 4K Remaster: CLASSIC/BOOM 시대 AI 업스케일링\n")
    builder.add_text("• 독점 다큐멘터리: 레전드 플레이어 스토리, 포커 역사\n\n")

    builder.add_divider()

    # ========== Section 6: 아카이브 시대 구분 ==========
    builder.add_text("6. 아카이브 시대 구분\n", heading="HEADING_1")
    builder.add_text("\n50년의 포커 역사는 명확한 네 개의 시대로 나뉩니다.\n\n")

    builder.add_text("CLASSIC (1973-2002): 전설의 시작\n", heading="HEADING_2")
    builder.add_text("WSOP가 탄생한 시대. 7명의 플레이어로 시작한 작은 게임이 포커 산업의 기초를 마련했습니다.\n")
    builder.add_text("• 기술: 아날로그 영상 및 VHS 저장\n")
    builder.add_text("• 콘텐츠: 초창기 카우보이 포커의 희귀한 영상\n")
    builder.add_text("• 가치: 포커 역사의 기원, Benny Binion의 유산\n")
    builder.add_text("• 주요 플레이어: Benny Binion, Doyle Brunson, Johnny Chan\n\n")

    builder.add_text("BOOM (2003-2010): 포커의 대변혁\n", heading="HEADING_2")
    builder.add_text("Chris Moneymaker의 2003년 우승이 촉발한 포커 산업의 황금기.\n")
    builder.add_text("• 기술: 초기 디지털 녹화, ESPN 홀카드 카메라 도입\n")
    builder.add_text("• 콘텐츠: 온라인 포커 붐 시대의 기록\n")
    builder.add_text("• 가치: 포커가 메인스트림 오락이 된 증거\n")
    builder.add_text("• 주요 이벤트: 2003 Moneymaker 우승, 2006 참가자 8,773명\n\n")

    builder.add_text("HD (2011-2025): 현대 포커 시대\n", heading="HEADING_2")
    builder.add_text("고화질 제작 표준과 프로페셔널 포커 생태계의 확립.\n")
    builder.add_text("• 기술: HD/4K 네이티브 제작\n")
    builder.add_text("• 콘텐츠: 풀 에피소드 고화질 보관\n")
    builder.add_text("• 가치: GTO 이론, AI 시대 포커의 진화\n")
    builder.add_text("• 주요 플레이어: Daniel Negreanu, Phil Ivey, Phil Hellmuth\n\n")

    builder.add_text("WSOPTV (2026~): 플랫폼 시대\n", heading="HEADING_2")
    builder.add_text("WSOPTV 전용 오리지널 콘텐츠 시대의 개막.\n")
    builder.add_text("• 기술: 네이티브 OTT 플랫폼, 4K Remaster\n")
    builder.add_text("• 콘텐츠: 독점 다큐멘터리, 추가 제작\n")
    builder.add_text("• 가치: WSOP의 완전한 디지털화\n\n")

    builder.add_divider()

    # ========== End ==========
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

    # Create a new Google Doc
    print("\nCreating new Google Doc...")
    doc = docs_service.documents().create(body={
        "title": "WSOPTV 콘텐츠 전략 v4.0.0"
    }).execute()
    doc_id = doc["documentId"]
    print(f"  Created document: {doc_id}")

    print("Building Content Strategy document structure (6 sections)...")
    requests = build_content_strategy_document(image_ids)

    print(f"Applying {len(requests)} updates to document...")

    # Batch requests in chunks to avoid API limits
    chunk_size = 100
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i:i + chunk_size]
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": chunk}
        ).execute()
        print(f"  Applied requests {i+1} to {min(i + chunk_size, len(requests))}")

    print(f"\nDocument created successfully!")
    print(f"View at: https://docs.google.com/document/d/{doc_id}/edit")

    return doc_id


if __name__ == "__main__":
    main()
