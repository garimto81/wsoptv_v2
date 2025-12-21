"""
Google Docs 페이지 방향 수정 - A4 세로(Portrait) 설정
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents']
CREDENTIALS_FILE = r'D:\AI\claude01\json\desktop_credentials.json'
TOKEN_FILE = r'D:\AI\claude01\json\token.json'
DOC_ID = '150uymfx3hYZaXF6yzmU6WghAXMt6RXocMCZth0R0z8k'

# A4 세로 (Portrait): 210mm x 297mm
# 1mm = 2.83465pt
A4_WIDTH_PT = 595.276   # 210mm
A4_HEIGHT_PT = 841.890  # 297mm


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
    print("=" * 60)
    print("Google Docs 페이지 방향 수정")
    print("=" * 60)

    creds = get_credentials()
    docs_service = build('docs', 'v1', credentials=creds)

    # 현재 설정 확인
    doc = docs_service.documents().get(documentId=DOC_ID).execute()
    style = doc.get('documentStyle', {})
    page_size = style.get('pageSize', {})

    current_width = page_size.get('width', {}).get('magnitude', 0)
    current_height = page_size.get('height', {}).get('magnitude', 0)

    print(f"\n[현재 설정]")
    print(f"  Width: {current_width:.1f}pt")
    print(f"  Height: {current_height:.1f}pt")
    print(f"  방향: {'세로(Portrait)' if current_width < current_height else '가로(Landscape)'}")

    # A4 세로로 강제 설정
    print(f"\n[A4 세로 설정 적용]")
    print(f"  Target Width: {A4_WIDTH_PT:.1f}pt (210mm)")
    print(f"  Target Height: {A4_HEIGHT_PT:.1f}pt (297mm)")

    requests = [{
        'updateDocumentStyle': {
            'documentStyle': {
                'pageSize': {
                    'width': {'magnitude': A4_WIDTH_PT, 'unit': 'PT'},
                    'height': {'magnitude': A4_HEIGHT_PT, 'unit': 'PT'}
                },
                'marginTop': {'magnitude': 72, 'unit': 'PT'},
                'marginBottom': {'magnitude': 72, 'unit': 'PT'},
                'marginLeft': {'magnitude': 72, 'unit': 'PT'},
                'marginRight': {'magnitude': 72, 'unit': 'PT'}
            },
            'fields': 'pageSize,marginTop,marginBottom,marginLeft,marginRight'
        }
    }]

    docs_service.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': requests}
    ).execute()

    # 확인
    doc = docs_service.documents().get(documentId=DOC_ID).execute()
    style = doc.get('documentStyle', {})
    page_size = style.get('pageSize', {})

    new_width = page_size.get('width', {}).get('magnitude', 0)
    new_height = page_size.get('height', {}).get('magnitude', 0)

    print(f"\n[적용 후]")
    print(f"  Width: {new_width:.1f}pt")
    print(f"  Height: {new_height:.1f}pt")
    print(f"  방향: {'세로(Portrait)' if new_width < new_height else '가로(Landscape)'}")

    print(f"\n문서 URL: https://docs.google.com/document/d/{DOC_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
