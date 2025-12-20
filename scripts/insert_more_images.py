"""
추가 이미지 삽입 - 콘텐츠 구성, 콘텐츠 상세 차트
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '1431Dz71jRV78o6-bwgR6sVM573bnGKf9-9Ozyo6hKpg'
# content-strategy 서브폴더
FOLDER_ID = '1NqPboT9HsAfF2XPI9Xfot-nc0wcVA2uR'

IMAGE_DIR = r'D:\AI\claude01\wsoptv_v2\docs\wireframes\v2'

# 이미 업로드된 이미지 ID
UPLOADED_IMAGES = {
    'cs-content-composition.png': '18v27YH8LzaKiI_4F6_FXD_YkWizVlngH',
    'cs-content-detail.png': '1_SS4ynLnDQ3n1uXbYF07weO8jDt8z4tT',
    'cs-content-pie.png': '1P1c9JptKIgPWMCOcZeMnYBTj-8eeKNw3',
    'cs-bracelet-structure.png': '1kPt_yN2YrrVTxdqRezrR1OgKBNET5nhK',
    'cs-main-event.png': '1jQDyY0_m9CpzuvIWFYgmbL-z23-falBE',
}


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


def find_section_index(docs_service, doc_id, section_text):
    """특정 섹션 텍스트 뒤의 인덱스 찾기"""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])

    for element in content:
        if 'paragraph' not in element:
            continue

        paragraph = element['paragraph']
        elements = paragraph.get('elements', [])
        text = ''
        for elem in elements:
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')

        if section_text in text.strip():
            return element['endIndex']

    return None


def insert_image_at_index(docs_service, doc_id, index, image_id, width=468, height=280):
    """특정 인덱스에 이미지 삽입"""
    url = f"https://drive.google.com/uc?export=view&id={image_id}"

    try:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{
                'insertInlineImage': {
                    'location': {'index': index},
                    'uri': url,
                    'objectSize': {
                        'width': {'magnitude': width, 'unit': 'PT'},
                        'height': {'magnitude': height, 'unit': 'PT'}
                    }
                }
            }]}
        ).execute()
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    print("=" * 60)
    print("추가 이미지 삽입")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 삽입할 이미지와 위치
    images_to_insert = [
        {
            'section': '콘텐츠 구성',
            'image': 'cs-content-composition.png',
            'description': '콘텐츠 구성 파이 차트'
        },
        {
            'section': '콘텐츠 상세',
            'image': 'cs-content-detail.png',
            'description': '콘텐츠 상세 차트'
        },
    ]

    # 역순으로 처리 (인덱스 꼬임 방지)
    images_to_insert.reverse()

    for item in images_to_insert:
        print(f"\n{item['description']} 삽입 중...")

        # 섹션 위치 찾기
        index = find_section_index(docs_service, DOC_ID, item['section'])

        if index is None:
            print(f"  섹션 '{item['section']}' 찾을 수 없음")
            continue

        print(f"  섹션 위치: {index}")

        # 이미지 ID 가져오기
        image_id = UPLOADED_IMAGES.get(item['image'])
        if not image_id:
            print(f"  이미지 ID 없음: {item['image']}")
            continue

        # 줄바꿈 삽입
        docs_service.documents().batchUpdate(
            documentId=DOC_ID,
            body={'requests': [{
                'insertText': {
                    'location': {'index': index},
                    'text': '\n\n'
                }
            }]}
        ).execute()

        # 이미지 삽입
        success = insert_image_at_index(docs_service, DOC_ID, index + 1, image_id)

        if success:
            print(f"  성공!")
        else:
            print(f"  실패")

    print(f"\n완료! 문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")


if __name__ == "__main__":
    main()
