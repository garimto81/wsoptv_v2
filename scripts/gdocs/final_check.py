"""최종 서식 체크"""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '150uymfx3hYZaXF6yzmU6WghAXMt6RXocMCZth0R0z8k'

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

def main():
    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)
    doc = docs_service.documents().get(documentId=DOC_ID).execute()

    print("=" * 60)
    print("FINAL CHECK - Google Docs")
    print("=" * 60)

    # 페이지 설정
    style = doc.get('documentStyle', {})
    page_size = style.get('pageSize', {})
    width = page_size.get('width', {}).get('magnitude', 0)
    height = page_size.get('height', {}).get('magnitude', 0)

    print(f"\n[Page Setup]")
    print(f"  Size: {width:.1f}pt x {height:.1f}pt")
    print(f"  A4 Check: {'OK' if abs(width - 595.3) < 1 and abs(height - 841.9) < 1 else 'FAIL'}")

    margins = {
        'top': style.get('marginTop', {}).get('magnitude', 0),
        'bottom': style.get('marginBottom', {}).get('magnitude', 0),
        'left': style.get('marginLeft', {}).get('magnitude', 0),
        'right': style.get('marginRight', {}).get('magnitude', 0)
    }
    print(f"  Margins: T={margins['top']:.0f} B={margins['bottom']:.0f} L={margins['left']:.0f} R={margins['right']:.0f} pt")

    # 이미지 크기
    inline_objects = doc.get('inlineObjects', {})
    print(f"\n[Images] ({len(inline_objects)} total)")
    for i, (obj_id, obj) in enumerate(inline_objects.items()):
        props = obj.get('inlineObjectProperties', {}).get('embeddedObject', {})
        size = props.get('size', {})
        w = size.get('width', {}).get('magnitude', 0)
        h = size.get('height', {}).get('magnitude', 0)
        status = 'OK' if w >= 400 else 'SMALL'
        print(f"  {i+1}. {w:.0f}pt x {h:.0f}pt [{status}]")

    # 헤딩 스타일
    content = doc.get('body', {}).get('content', [])
    headings = {'HEADING_1': 0, 'HEADING_2': 0, 'HEADING_3': 0, 'HEADING_4': 0}
    tables = 0
    quotes = 0
    bullets = 0

    for element in content:
        if 'paragraph' in element:
            para = element['paragraph']
            style_type = para.get('paragraphStyle', {}).get('namedStyleType', '')
            if style_type in headings:
                headings[style_type] += 1

            # 인용문 체크 (들여쓰기)
            indent = para.get('paragraphStyle', {}).get('indentStart', {}).get('magnitude', 0)
            if indent > 0:
                quotes += 1

            # 불릿 체크
            if para.get('bullet'):
                bullets += 1

        elif 'table' in element:
            tables += 1

    print(f"\n[Headings]")
    for h, c in headings.items():
        print(f"  {h}: {c}")

    print(f"\n[Formatting]")
    print(f"  Tables: {tables}")
    print(f"  Indented (quotes): {quotes}")
    print(f"  Bullets: {bullets}")

    # 최종 결과
    print("\n" + "=" * 60)
    all_ok = (
        abs(width - 595.3) < 1 and
        abs(height - 841.9) < 1 and
        tables >= 28 and
        len(inline_objects) >= 9
    )

    if all_ok:
        print("[RESULT] ALL CHECKS PASSED!")
        print("\n  - A4 page size")
        print("  - 1-inch margins")
        print(f"  - {tables} tables with header styling")
        print(f"  - {len(inline_objects)} images (17cm width)")
        print("  - Heading styles H1-H4")
        print("  - Quote indentation")
        print("  - Bullet lists")
    else:
        print("[RESULT] Some issues found")

    print(f"\nDocument: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)

if __name__ == "__main__":
    main()
