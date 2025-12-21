"""
Google Docs 서식 상세 분석 - 수동 조정 필요 항목 체크
"""

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


def analyze_document_details(docs_service, doc_id):
    """문서 상세 분석"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    issues = []
    warnings = []

    # 문서 구조 수집
    headings = []
    tables_info = []
    images_info = []
    empty_paragraphs = 0
    consecutive_empty = 0
    max_consecutive_empty = 0

    prev_was_empty = False

    for idx, element in enumerate(content):
        if 'paragraph' in element:
            para = element['paragraph']
            style = para.get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')

            # 텍스트 추출
            text = ''
            has_image = False
            for elem in para.get('elements', []):
                if 'textRun' in elem:
                    text += elem['textRun'].get('content', '')
                if 'inlineObjectElement' in elem:
                    has_image = True
                    obj_id = elem['inlineObjectElement'].get('inlineObjectId', '')
                    images_info.append({
                        'index': element['startIndex'],
                        'object_id': obj_id
                    })

            text = text.strip()

            # 헤딩 수집
            if style.startswith('HEADING_'):
                headings.append({
                    'level': style,
                    'text': text[:50] + ('...' if len(text) > 50 else ''),
                    'index': element['startIndex']
                })

            # 빈 문단 체크
            if not text and not has_image:
                empty_paragraphs += 1
                if prev_was_empty:
                    consecutive_empty += 1
                    max_consecutive_empty = max(max_consecutive_empty, consecutive_empty)
                else:
                    consecutive_empty = 1
                prev_was_empty = True
            else:
                prev_was_empty = False
                consecutive_empty = 0

            # 마크다운 잔여물 체크
            if '**' in text:
                issues.append(f"마크다운 볼드 잔여: '{text[:40]}...'")
            if text.startswith('- ') or text.startswith('* '):
                warnings.append(f"리스트 마커 미변환: '{text[:40]}'")
            if '`' in text:
                warnings.append(f"인라인 코드 잔여: '{text[:40]}'")

        elif 'table' in element:
            table = element['table']
            rows = len(table.get('tableRows', []))
            cols = len(table.get('tableRows', [{}])[0].get('tableCells', [])) if rows > 0 else 0
            tables_info.append({
                'index': element['startIndex'],
                'rows': rows,
                'cols': cols
            })

    # 이미지 상세 정보
    inline_objects = doc.get('inlineObjects', {})
    for img in images_info:
        obj_id = img['object_id']
        if obj_id in inline_objects:
            obj = inline_objects[obj_id]
            props = obj.get('inlineObjectProperties', {}).get('embeddedObject', {})
            img['width'] = props.get('size', {}).get('width', {}).get('magnitude', 0)
            img['height'] = props.get('size', {}).get('height', {}).get('magnitude', 0)
            img['uri'] = props.get('imageProperties', {}).get('sourceUri', '')[:50]

    return {
        'headings': headings,
        'tables': tables_info,
        'images': images_info,
        'empty_paragraphs': empty_paragraphs,
        'max_consecutive_empty': max_consecutive_empty,
        'issues': issues,
        'warnings': warnings
    }


def main():
    print("=" * 70)
    print("Google Docs 서식 상세 분석")
    print("=" * 70)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    result = analyze_document_details(docs_service, DOC_ID)

    # 1. 헤딩 구조
    print("\n[1] 헤딩 구조 (목차)")
    print("-" * 50)
    for h in result['headings']:
        indent = "  " * (int(h['level'][-1]) - 1)
        print(f"{indent}{h['level']}: {h['text']}")

    # 2. 테이블 정보
    print(f"\n[2] 테이블 ({len(result['tables'])}개)")
    print("-" * 50)
    for i, t in enumerate(result['tables'][:10]):
        print(f"  Table {i+1}: {t['rows']}행 x {t['cols']}열")
    if len(result['tables']) > 10:
        print(f"  ... 외 {len(result['tables']) - 10}개")

    # 3. 이미지 정보
    print(f"\n[3] 이미지 ({len(result['images'])}개)")
    print("-" * 50)
    for i, img in enumerate(result['images']):
        w = img.get('width', 0)
        h = img.get('height', 0)
        print(f"  Image {i+1}: {w:.0f}pt x {h:.0f}pt")

    # 4. 빈 문단
    print(f"\n[4] 빈 문단")
    print("-" * 50)
    print(f"  총 빈 문단: {result['empty_paragraphs']}개")
    print(f"  최대 연속 빈 문단: {result['max_consecutive_empty']}개")

    # 5. 이슈 및 경고
    print(f"\n[5] 발견된 이슈")
    print("-" * 50)
    if result['issues']:
        for issue in result['issues']:
            print(f"  [ERROR] {issue}")
    else:
        print("  이슈 없음")

    if result['warnings']:
        print()
        for warn in result['warnings']:
            print(f"  [WARN] {warn}")

    # 6. 수동 조정 권장 사항
    print("\n" + "=" * 70)
    print("[수동 조정 권장 사항]")
    print("=" * 70)

    recommendations = []

    # 이미지 크기 체크
    for i, img in enumerate(result['images']):
        w = img.get('width', 0)
        if w < 300:
            recommendations.append(f"Image {i+1}: 크기 확대 권장 (현재 {w:.0f}pt → 400pt)")
        elif w > 500:
            recommendations.append(f"Image {i+1}: 크기 축소 권장 (현재 {w:.0f}pt → 400pt)")

    # 연속 빈 문단
    if result['max_consecutive_empty'] > 2:
        recommendations.append(f"연속 빈 줄 정리: 최대 {result['max_consecutive_empty']}개 → 1개로 축소")

    # 테이블 헤더 스타일
    recommendations.append("테이블 첫 행에 배경색/볼드 적용 권장")

    # 인용문 스타일
    recommendations.append("인용문(>) 블록에 들여쓰기 또는 배경색 적용 권장")

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("  수동 조정 불필요!")

    print()
    print(f"문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 70)


if __name__ == "__main__":
    main()
