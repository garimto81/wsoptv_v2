"""Update Google Docs with wireframe structure."""
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
TOKEN_PATH = Path(r"D:\AI\claude01\json\token.json")
WIREFRAME_DIR = Path(r"D:\AI\claude01\wsoptv_v2\docs\wireframes\v2")
GOOGLE_DOC_ID = "1tghlhpQiWttpB-0CP5c1DiL5BJa4ttWj-2R77xaoVI8"

# Image IDs from Google Drive
IMAGE_IDS = {
    "full-page": "1RryYK2PRSZQg8D_n18XhjLjAzsoq2Vk_",
    "header": "1o9q_EGdUeghPQolNJ161ZEqXhz3Ml8Cb",
    "hero": "1lN3O652dyDCnVUzObxh_-YKzWVMXIdjO",
    "continue": "1jrlMTi7-vwb82mKT7TDZVrGZle-tA2Ji",
    "recent": "1nwiutlNSsLa_VqRDFQF0hLCchF9PuiuW",
    "series": "1AQpOI_VVFMo2G3HUXGzv4BKkDxbweDII",
    "footer": "13YwFBfF-iJHUM1Lio--UjTRlKCoq6L8D",
}


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

    # Find end index
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


def build_document_structure():
    """Build the requests to create the document structure."""
    requests = []
    current_index = 1

    def add_text(text, style=None, heading=None):
        nonlocal current_index
        requests.append({
            "insertText": {
                "location": {"index": current_index},
                "text": text,
            }
        })
        text_end = current_index + len(text)

        if heading:
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": current_index, "endIndex": text_end},
                    "paragraphStyle": {"namedStyleType": heading},
                    "fields": "namedStyleType",
                }
            })
        elif style:
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": current_index, "endIndex": text_end - 1},
                    "textStyle": style,
                    "fields": ",".join(style.keys()),
                }
            })

        current_index = text_end

    def add_image(image_id, width_pt=None, height_pt=None):
        nonlocal current_index
        uri = f"https://drive.google.com/uc?id={image_id}"
        obj_size = {}
        if height_pt:
            obj_size["height"] = {"magnitude": height_pt, "unit": "PT"}
        if width_pt:
            obj_size["width"] = {"magnitude": width_pt, "unit": "PT"}

        requests.append({
            "insertInlineImage": {
                "location": {"index": current_index},
                "uri": uri,
                "objectSize": obj_size if obj_size else {"width": {"magnitude": 600, "unit": "PT"}},
            }
        })
        current_index += 1  # Image takes 1 index

    # Title
    add_text("WSOPTV - 홈페이지 와이어프레임\n", heading="TITLE")

    # Section 1: Full Page
    add_text("\n1. 홈페이지 전체 와이어프레임\n", heading="HEADING_1")
    add_text("Netflix 스타일의 다크 테마 기반으로 설계된 WSOPTV 홈페이지 전체 구조입니다.\n\n")
    add_image(IMAGE_IDS["full-page"], height_pt=650)
    add_text("\n\n페이지 구성 요소:\n")
    add_text("- A. Header - 상단 고정 네비게이션\n")
    add_text("- B. Hero Banner - 메인 추천 콘텐츠\n")
    add_text("- C. Continue Watching - 이어보기 섹션\n")
    add_text("- D. Recently Added - 최근 추가 콘텐츠\n")
    add_text("- E. Series Section - 시리즈별 콘텐츠 그룹\n")
    add_text("- F. Footer - 하단 정보 영역\n")

    # Section 2: Element Analysis
    add_text("\n2. 요소별 상세 분석\n", heading="HEADING_1")

    # 2.1 Header
    add_text("\n2.1 Header - 상단 고정 네비게이션\n", heading="HEADING_2")
    add_image(IMAGE_IDS["header"])
    add_text("\n\n핵심 스펙:\n")
    add_text("- 로고: 120x40px, #e50914 배경\n")
    add_text("- 네비게이션: gap 24px, 활성 흰색 + 언더라인\n")
    add_text("- 아이콘: 36x36px (검색, 프로필)\n")
    add_text("- 동작: position: fixed, z-index: 1000, 높이 64px\n")

    # 2.2 Hero Banner
    add_text("\n2.2 Hero Banner - 메인 추천 콘텐츠\n", heading="HEADING_2")
    add_image(IMAGE_IDS["hero"])
    add_text("\n\n핵심 스펙:\n")
    add_text("- 배지: NEW (#e50914), 4K (#ffc107)\n")
    add_text("- 제목: 36px / font-weight: 700, 최대 2줄\n")
    add_text("- 썸네일: 16:9, WebP, Lazy Load\n")
    add_text("- 인디케이터: 최대 5개, 5초 자동 전환\n")

    # 2.3 Continue Watching
    add_text("\n2.3 Continue Watching - 이어보기 섹션\n", heading="HEADING_2")
    add_image(IMAGE_IDS["continue"])
    add_text("\n\n핵심 스펙:\n")
    add_text("- 카드 그리드: 4열, gap: 12px\n")
    add_text("- 진행률 바: 높이 4px, #e50914\n")
    add_text("- 동작: 10초마다 위치 저장, 95% 시청 시 제거\n")

    # 2.4 Recently Added
    add_text("\n2.4 Recently Added - 최근 추가 콘텐츠\n", heading="HEADING_2")
    add_image(IMAGE_IDS["recent"])
    add_text("\n\n핵심 스펙:\n")
    add_text("- 카드 그리드: 5열, gap: 10px\n")
    add_text("- 배지: NEW (7일 이내), 4K/HD/CC\n")
    add_text("- 호버: scale(1.05), box-shadow, 0.2s\n")

    # 2.5 Series Section
    add_text("\n2.5 Series Section - 시리즈별 콘텐츠 그룹\n", heading="HEADING_2")
    add_image(IMAGE_IDS["series"])
    add_text("\n\n핵심 스펙:\n")
    add_text("- 레이아웃: 포스터 (2:3) + 에피소드 목록\n")
    add_text("- 에피소드: 최대 4개, 더보기 표시\n")
    add_text('- 재생시간: "H:MM:SS" 형식\n')

    # 2.6 Footer
    add_text("\n2.6 Footer - 하단 정보 영역\n", heading="HEADING_2")
    add_image(IMAGE_IDS["footer"])
    add_text("\n\n핵심 스펙:\n")
    add_text("- 링크 그리드: 4열 (About, Support, Legal, Account)\n")
    add_text("- 소셜 링크: 36x36px, gap: 16px\n")
    add_text("- 반응형: Desktop 4열 > Tablet 2열 > Mobile 1열\n")

    return requests


def main():
    """Main function."""
    print("Loading credentials...")
    creds = get_credentials()

    print("Building Docs service...")
    docs_service = build("docs", "v1", credentials=creds)

    print("\nClearing existing document...")
    clear_document(docs_service, GOOGLE_DOC_ID)

    print("Building new document structure...")
    requests = build_document_structure()

    print(f"Applying {len(requests)} updates to document...")
    docs_service.documents().batchUpdate(
        documentId=GOOGLE_DOC_ID, body={"requests": requests}
    ).execute()

    print(f"\nDocument updated successfully!")
    print(f"View at: https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit")


if __name__ == "__main__":
    main()
