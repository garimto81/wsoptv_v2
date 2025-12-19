"""Upload PRD document to Google Docs."""
import json
import re
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
TOKEN_PATH = Path(r"D:\AI\claude01\json\token.json")
PRD_PATH = Path(r"D:\AI\claude01\wsoptv_v2\tasks\prds\0011-prd-qr-vip-registration.md")

# Google Doc ID for PRD 0011 (create new if None)
GOOGLE_DOC_ID = None  # Will create new document


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


def parse_markdown_to_requests(markdown_content: str) -> list:
    """Parse markdown and convert to Google Docs API requests."""
    requests = []
    current_index = 1

    lines = markdown_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip HTML table tags (we'll handle tables differently)
        if line.strip().startswith('<table') or line.strip().startswith('</table'):
            i += 1
            continue
        if line.strip().startswith('<tr') or line.strip().startswith('</tr'):
            i += 1
            continue
        if line.strip().startswith('<td') or line.strip().startswith('</td'):
            i += 1
            continue

        # Heading 1: # Title
        if line.startswith('# ') and not line.startswith('##'):
            text = line[2:] + '\n'
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": text,
                }
            })
            text_end = current_index + len(text)
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": current_index, "endIndex": text_end},
                    "paragraphStyle": {"namedStyleType": "HEADING_1"},
                    "fields": "namedStyleType",
                }
            })
            current_index = text_end

        # Heading 2: ## Title
        elif line.startswith('## '):
            text = line[3:] + '\n'
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": text,
                }
            })
            text_end = current_index + len(text)
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": current_index, "endIndex": text_end},
                    "paragraphStyle": {"namedStyleType": "HEADING_2"},
                    "fields": "namedStyleType",
                }
            })
            current_index = text_end

        # Heading 3: ### Title
        elif line.startswith('### '):
            text = line[4:] + '\n'
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": text,
                }
            })
            text_end = current_index + len(text)
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": current_index, "endIndex": text_end},
                    "paragraphStyle": {"namedStyleType": "HEADING_3"},
                    "fields": "namedStyleType",
                }
            })
            current_index = text_end

        # Heading 4: #### Title
        elif line.startswith('#### '):
            text = line[5:] + '\n'
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": text,
                }
            })
            text_end = current_index + len(text)
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": current_index, "endIndex": text_end},
                    "paragraphStyle": {"namedStyleType": "HEADING_4"},
                    "fields": "namedStyleType",
                }
            })
            current_index = text_end

        # Code block
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1

            if code_lines:
                code_text = '\n'.join(code_lines) + '\n\n'
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": code_text,
                    }
                })
                text_end = current_index + len(code_text)
                # Apply monospace font
                requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": current_index, "endIndex": text_end - 1},
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Consolas"},
                            "fontSize": {"magnitude": 9, "unit": "PT"},
                        },
                        "fields": "weightedFontFamily,fontSize",
                    }
                })
                current_index = text_end

        # Horizontal rule
        elif line.strip() == '---':
            text = '\n' + '─' * 50 + '\n\n'
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": text,
                }
            })
            current_index += len(text)

        # Table row (markdown table)
        elif line.startswith('|'):
            # Skip separator lines
            if re.match(r'^\|[\s\-:|]+\|$', line):
                i += 1
                continue

            # Parse table row
            cells = [c.strip() for c in line.split('|')[1:-1]]
            row_text = '  |  '.join(cells) + '\n'
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": row_text,
                }
            })
            current_index += len(row_text)

        # Regular text or list items
        elif line.strip():
            text = line + '\n'
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": text,
                }
            })
            current_index += len(text)

        # Empty line
        else:
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": '\n',
                }
            })
            current_index += 1

        i += 1

    return requests


def create_new_document(docs_service, title: str) -> str:
    """Create a new Google Doc and return its ID."""
    doc = docs_service.documents().create(body={"title": title}).execute()
    return doc.get("documentId")


def main():
    """Main function."""
    print("Loading credentials...")
    creds = get_credentials()

    print("Loading PRD content...")
    with open(PRD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    print("\nBuilding Docs service...")
    docs_service = build("docs", "v1", credentials=creds)

    doc_id = GOOGLE_DOC_ID

    if not doc_id:
        print("Creating new Google Doc...")
        doc_id = create_new_document(docs_service, "PRD 0011: QR 코드 VIP 등록 시스템")
        print(f"  Created document ID: {doc_id}")
    else:
        print("Clearing existing document...")
        clear_document(docs_service, doc_id)

    print("Parsing markdown...")
    requests = parse_markdown_to_requests(content)

    print(f"Applying {len(requests)} updates to document...")

    # Batch requests in chunks to avoid API limits
    chunk_size = 100
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i:i + chunk_size]
        try:
            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": chunk}
            ).execute()
            print(f"  Applied requests {i+1} to {min(i + chunk_size, len(requests))}")
        except Exception as e:
            print(f"  Error at chunk {i}: {e}")
            # Continue with next chunk

    print(f"\nDocument updated successfully!")
    print(f"View at: https://docs.google.com/document/d/{doc_id}/edit")


if __name__ == "__main__":
    main()
