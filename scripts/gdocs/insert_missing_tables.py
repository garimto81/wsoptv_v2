"""
누락된 테이블 3개 삽입 (Rate Limit으로 실패한 테이블들)

원본 마크다운의 처음 3개 테이블:
1. 채널별 역할 테이블
2. 콘텐츠 배분 원칙 테이블
3. 방송 형식 테이블
"""

import os
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents']
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '150uymfx3hYZaXF6yzmU6WghAXMt6RXocMCZth0R0z8k'

# 누락된 테이블 데이터 (원본 마크다운에서 추출)
MISSING_TABLES = [
    {
        'anchor': '1.1 채널별 역할',
        'data': [
            ['채널', '역할', '목표'],
            ['YouTube', '유입 게이트웨이', '포커 관심층 확보, WSOPTV 인지도'],
            ['WSOPTV', '수익 엔진', '구독 전환, 리텐션']
        ]
    },
    {
        'anchor': '1.2 콘텐츠 배분 원칙',
        'data': [
            ['콘텐츠 유형', 'YouTube', 'WSOPTV', '배분 의도'],
            ['풀 에피소드', 'X', 'O', '유료 전환 핵심 콘텐츠'],
            ['쇼츠 (60초)', 'O', 'X', '바이럴, 신규 유입'],
            ['하이라이트 (5-10분)', 'O', 'X', '관심 유발'],
            ['Best Hands 클립', '일부 (티저)', '전체', '맛보기 → 전환 유도'],
            ['생방송', 'O', 'O', '동시 송출'],
            ['4K Remaster', '프로모션만', '전체', '프리미엄 독점']
        ]
    },
    {
        'anchor': '1.3 방송 형식',
        'data': [
            ['형식', '설명', '길이', '대상'],
            ['생방송', '실시간 중계, 다중 테이블 커버리지', '4-10시간', '코어 팬, 현장감'],
            ['에피소드', '생방송을 편집한 하이라이트 버전', '1시간', '캐주얼 시청, 신규 유입']
        ]
    }
]


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


def find_anchor_position(docs_service, doc_id, anchor_text):
    """앵커 텍스트 위치 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'paragraph' not in element:
            continue
        para = element['paragraph']
        text = ''
        for elem in para.get('elements', []):
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')

        if anchor_text in text:
            return element['endIndex']

    return None


def insert_table_after_position(docs_service, doc_id, position, table_data):
    """특정 위치 뒤에 테이블 삽입"""
    num_rows = len(table_data)
    num_cols = len(table_data[0]) if table_data else 0

    # 테이블 삽입
    try:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{
                'insertTable': {
                    'rows': num_rows,
                    'columns': num_cols,
                    'location': {'index': position}
                }
            }]}
        ).execute()
    except Exception as e:
        print(f"  테이블 삽입 실패: {e}")
        return False

    time.sleep(1)

    # 문서 다시 로드하여 테이블 셀에 내용 삽입
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'table' not in element:
            continue

        # 위치 확인
        if abs(element['startIndex'] - position) < 20:
            table = element['table']
            cell_requests = []

            for row_idx, row in enumerate(table.get('tableRows', [])):
                if row_idx >= len(table_data):
                    break
                for col_idx, cell in enumerate(row.get('tableCells', [])):
                    if col_idx >= len(table_data[row_idx]):
                        break

                    cell_content = cell.get('content', [])
                    if cell_content:
                        cell_start = cell_content[0].get('startIndex', 0)
                        cell_text = table_data[row_idx][col_idx]
                        if cell_text:
                            cell_requests.append({
                                'insertText': {
                                    'location': {'index': cell_start},
                                    'text': cell_text
                                }
                            })

            if cell_requests:
                cell_requests.reverse()
                try:
                    docs_service.documents().batchUpdate(
                        documentId=doc_id,
                        body={'requests': cell_requests}
                    ).execute()
                except Exception as e:
                    print(f"  셀 내용 삽입 실패: {e}")
                    return False

            return True

    return False


def main():
    print("=" * 50)
    print("누락된 테이블 3개 삽입")
    print("=" * 50)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    for i, table_info in enumerate(MISSING_TABLES):
        anchor = table_info['anchor']
        data = table_info['data']

        print(f"\n[{i+1}/3] '{anchor}' 테이블 삽입 중...")

        position = find_anchor_position(docs_service, DOC_ID, anchor)
        if not position:
            print(f"  [FAIL] 앵커 위치를 찾을 수 없음: {anchor}")
            continue

        if insert_table_after_position(docs_service, DOC_ID, position, data):
            print(f"  [OK] 테이블 삽입 완료 ({len(data)}행 x {len(data[0])}열)")
        else:
            print(f"  [FAIL] 테이블 삽입 실패")

        time.sleep(3)  # Rate Limit 방지

    print("\n완료!")
    print(f"문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")


if __name__ == "__main__":
    main()
