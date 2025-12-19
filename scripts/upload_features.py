"""Upload 01-features.md document to Google Docs with Mermaid diagram."""
import json
import re
import time
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Paths
TOKEN_PATH = Path(r"D:\AI\claude01\json\token.json")
WIREFRAME_DIR = Path(r"D:\AI\claude01\wsoptv_v2\docs\wireframes\v2")
PRD_PATH = Path(r"D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\01-features.md")

# Features diagram files
FEATURES_DIAGRAM_FILES = [
    "features-mindmap.png",  # Best Hands Categories mindmap
]

# Mermaid block to image mapping (order in document)
MERMAID_TO_IMAGE = {
    0: "features-mindmap.png",  # 2.3 Best Hands Categories
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


def upload_to_drive(drive_service, file_path, folder_id=None):
    """Upload a file to Google Drive."""
    file_name = file_path.name

    file_metadata = {"name": file_name}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(str(file_path), mimetype="image/png")

    # Check if file already exists
    query = f"name='{file_name}' and trashed=false"
    if folder_id:
        query += f" and '{folder_id}' in parents"

    results = drive_service.files().list(q=query, fields="files(id)").execute()
    existing_files = results.get("files", [])

    if existing_files:
        # Update existing file
        file_id = existing_files[0]["id"]
        drive_service.files().update(
            fileId=file_id,
            media_body=media,
        ).execute()
        print(f"  Updated: {file_name} (ID: {file_id})")
    else:
        # Create new file
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()
        file_id = file.get("id")
        # Make file publicly accessible
        drive_service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()
        print(f"  Created: {file_name} (ID: {file_id})")

    return file_id


def create_new_document(docs_service, title: str) -> str:
    """Create a new Google Doc and return its ID."""
    doc = docs_service.documents().create(body={"title": title}).execute()
    return doc.get("documentId")


class DocumentBuilder:
    """Helper class to build Google Docs content."""

    def __init__(self, image_ids: dict):
        self.requests = []
        self.current_index = 1
        self.image_ids = image_ids
        self.pending_tables = []  # (marker_text, table_data) pairs

    def add_text(self, text, heading=None, bold=False, monospace=False):
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

        if bold and len(text) > 1:
            self.requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": self.current_index, "endIndex": text_end - 1},
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            })

        if monospace and len(text) > 1:
            self.requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": self.current_index, "endIndex": text_end - 1},
                    "textStyle": {
                        "weightedFontFamily": {"fontFamily": "Courier New"},
                        "fontSize": {"magnitude": 9, "unit": "PT"}
                    },
                    "fields": "weightedFontFamily,fontSize",
                }
            })

        self.current_index = text_end

    def add_image(self, image_key, width_pt=400):
        """Add image with center alignment."""
        image_id = self.image_ids.get(image_key)
        if not image_id:
            self.add_text(f"\n[Image: {image_key} - ID not found]\n")
            return

        uri = f"https://drive.google.com/uc?id={image_id}"

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

    def add_table_marker(self, table_data: list):
        """Add a marker for table insertion later."""
        marker = f"[TABLE_MARKER_{len(self.pending_tables)}]"
        self.pending_tables.append((marker, table_data))
        self.add_text(marker + "\n")

    def add_divider(self):
        """Add horizontal divider."""
        self.add_text("\n" + "-" * 60 + "\n\n")

    def get_requests(self):
        return self.requests


def parse_markdown_table(lines: list, start_idx: int) -> tuple:
    """Parse a markdown table and return (table_data, end_index)."""
    table_data = []
    i = start_idx

    while i < len(lines) and lines[i].startswith('|'):
        line = lines[i]
        # Skip separator lines
        if re.match(r'^\|[\s\-:|]+\|$', line):
            i += 1
            continue

        cells = [c.strip() for c in line.split('|')[1:-1]]
        table_data.append(cells)
        i += 1

    return table_data, i


def parse_markdown_with_images(content: str, image_ids: dict) -> tuple:
    """Parse markdown and convert to Google Docs API requests with image support.
    Returns (requests, pending_tables).
    """
    builder = DocumentBuilder(image_ids)
    lines = content.split('\n')
    i = 0
    mermaid_block_index = 0
    in_code_block = False
    code_block_lines = []
    code_block_type = None

    while i < len(lines):
        line = lines[i]

        # Handle code blocks (including mermaid)
        if line.strip().startswith('```'):
            if not in_code_block:
                # Starting a code block
                in_code_block = True
                code_block_type = line.strip()[3:].strip()  # Get language type
                code_block_lines = []
                i += 1
                continue
            else:
                # Ending a code block
                in_code_block = False

                # Handle mermaid blocks specially
                if code_block_type == 'mermaid':
                    image_file = MERMAID_TO_IMAGE.get(mermaid_block_index)
                    if image_file and image_file in image_ids:
                        builder.add_text("\n")
                        builder.add_image(image_file, width_pt=450)
                        builder.add_text("\n")
                    mermaid_block_index += 1
                else:
                    # Regular code block - render as monospace
                    if code_block_lines:
                        builder.add_text('\n')
                        for code_line in code_block_lines:
                            builder.add_text(code_line + '\n', monospace=True)
                        builder.add_text('\n')

                code_block_lines = []
                code_block_type = None
                i += 1
                continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Heading 1: # Title
        if line.startswith('# ') and not line.startswith('##'):
            builder.add_text(line[2:] + '\n', heading="HEADING_1")

        # Heading 2: ## Title
        elif line.startswith('## '):
            builder.add_text(line[3:] + '\n', heading="HEADING_2")

        # Heading 3: ### Title
        elif line.startswith('### '):
            builder.add_text(line[4:] + '\n', heading="HEADING_3")

        # Heading 4: #### Title
        elif line.startswith('#### '):
            builder.add_text(line[5:] + '\n', heading="HEADING_4")

        # Horizontal rule
        elif line.strip() == '---':
            builder.add_divider()

        # Table - collect all rows and add marker
        elif line.startswith('|'):
            table_data, end_idx = parse_markdown_table(lines, i)
            if table_data:
                builder.add_table_marker(table_data)
            i = end_idx
            continue

        # Blockquote
        elif line.startswith('> '):
            builder.add_text("    " + line[2:] + '\n')

        # Regular text or list items
        elif line.strip():
            builder.add_text(line + '\n')

        # Empty line
        else:
            builder.add_text('\n')

        i += 1

    return builder.get_requests(), builder.pending_tables


def insert_tables(docs_service, doc_id: str, pending_tables: list):
    """Replace table markers with actual Google Docs tables."""
    # Process tables in reverse order to maintain correct indices
    table_count = 0
    for marker, table_data in reversed(pending_tables):
        # Rate limiting: pause every 5 tables to avoid quota exceeded
        if table_count > 0 and table_count % 5 == 0:
            print("    (waiting 10s for API quota...)")
            time.sleep(10)
        table_count += 1
        if not table_data:
            continue

        rows = len(table_data)
        cols = len(table_data[0]) if table_data else 0

        if rows == 0 or cols == 0:
            continue

        # Find marker location
        doc = docs_service.documents().get(documentId=doc_id).execute()
        content = doc.get("body", {}).get("content", [])

        marker_start = None
        marker_end = None

        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for elem in paragraph.get("elements", []):
                    if "textRun" in elem:
                        text = elem["textRun"].get("content", "")
                        if marker in text:
                            marker_start = elem["startIndex"]
                            marker_end = elem["endIndex"]
                            break

        if marker_start is None:
            print(f"  Warning: Marker {marker} not found")
            continue

        # Delete marker text
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{
                "deleteContentRange": {
                    "range": {
                        "startIndex": marker_start,
                        "endIndex": marker_end,
                    }
                }
            }]}
        ).execute()

        # Insert table at marker location
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{
                "insertTable": {
                    "location": {"index": marker_start},
                    "rows": rows,
                    "columns": cols,
                }
            }]}
        ).execute()

        # Get updated document to find cell indices
        doc = docs_service.documents().get(documentId=doc_id).execute()
        content = doc.get("body", {}).get("content", [])

        # Find the table we just inserted
        table_element = None
        for element in content:
            if "table" in element:
                if element["startIndex"] >= marker_start - 5:
                    table_element = element
                    break

        if not table_element:
            print(f"  Warning: Could not find inserted table")
            continue

        # Fill table cells with content
        table = table_element["table"]
        requests = []

        for row_idx, row_data in enumerate(table_data):
            table_row = table["tableRows"][row_idx]
            for col_idx, cell_text in enumerate(row_data):
                if col_idx >= len(table_row["tableCells"]):
                    continue

                cell = table_row["tableCells"][col_idx]
                cell_start = cell["content"][0]["startIndex"]

                # Insert text
                requests.append({
                    "insertText": {
                        "location": {"index": cell_start},
                        "text": cell_text,
                    }
                })

                # Bold header row (first row)
                if row_idx == 0:
                    requests.append({
                        "updateTextStyle": {
                            "range": {
                                "startIndex": cell_start,
                                "endIndex": cell_start + len(cell_text)
                            },
                            "textStyle": {"bold": True},
                            "fields": "bold",
                        }
                    })

        # Apply all cell content in one batch (process in reverse order)
        if requests:
            # Sort requests by index in reverse order
            requests.sort(key=lambda r: r.get("insertText", r.get("updateTextStyle", {})).get("location", r.get("range", {})).get("index", r.get("startIndex", 0)), reverse=True)

            # Split into smaller batches
            for j in range(0, len(requests), 50):
                batch = requests[j:j+50]
                try:
                    docs_service.documents().batchUpdate(
                        documentId=doc_id, body={"requests": batch}
                    ).execute()
                except Exception as e:
                    print(f"  Error filling table: {e}")

        print(f"  Inserted table: {rows}x{cols}")


def main():
    """Main function."""
    print("Loading credentials...")
    creds = get_credentials()

    print("Building Drive service...")
    drive_service = build("drive", "v3", credentials=creds)

    print("\nUploading Features diagram images to Google Drive...")
    image_ids = {}

    for file_name in FEATURES_DIAGRAM_FILES:
        file_path = WIREFRAME_DIR / file_name
        if file_path.exists():
            image_id = upload_to_drive(drive_service, file_path)
            image_ids[file_name] = image_id
        else:
            print(f"  Skipped (not found): {file_name}")

    print(f"\n--- Uploaded {len(image_ids)} images ---")

    print("\nLoading PRD content...")
    with open(PRD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    print("\nBuilding Docs service...")
    docs_service = build("docs", "v1", credentials=creds)

    print("Creating new Google Doc...")
    doc_id = create_new_document(docs_service, "WSOPTV - 핵심 기능 명세 (01-features)")
    print(f"  Created document ID: {doc_id}")

    print("Parsing markdown with images...")
    requests, pending_tables = parse_markdown_with_images(content, image_ids)

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

    # Insert tables
    if pending_tables:
        print(f"\nInserting {len(pending_tables)} tables...")
        insert_tables(docs_service, doc_id, pending_tables)

    print(f"\nDocument created successfully!")
    print(f"View at: https://docs.google.com/document/d/{doc_id}/edit")
    print(f"\nStatistics:")
    print(f"  - Tables inserted: {len(pending_tables)}")
    print(f"  - Images inserted: {len([k for k in image_ids.keys() if k in MERMAID_TO_IMAGE.values()])}")


if __name__ == "__main__":
    main()
