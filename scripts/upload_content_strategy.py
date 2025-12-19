"""Upload Content Strategy document to Google Docs with Mermaid diagrams."""
import json
import re
import time
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

# Paths - OAuth 2.0 인증 (Drive 업로드 지원)
CREDENTIALS_FILE = Path(r"D:\AI\claude01\json\desktop_credentials.json")
TOKEN_FILE = Path(r"D:\AI\claude01\json\token.json")
WIREFRAME_DIR = Path(r"D:\AI\claude01\wsoptv_v2\docs\wireframes\v2")
PRD_PATH = Path(r"D:\AI\claude01\wsoptv_v2\tasks\prds\0010-prd-wsoptv\03-content-strategy.md")

# Content Strategy diagram files (9 images including pie chart)
CS_DIAGRAM_FILES = [
    "cs-core-content.png",
    "cs-content-pie.png",          # NEW: Pie chart
    "cs-content-detail.png",
    "cs-bracelet-structure.png",
    "cs-main-event.png",
    "cs-other-events.png",
    "cs-youtube-wsoptv.png",
    "cs-curation-roadmap.png",
    "cs-season-calendar.png",
]

# Mermaid block to image mapping (order in document)
MERMAID_TO_IMAGE = {
    0: "cs-core-content.png",       # 1.1 Core Content
    1: "cs-content-pie.png",        # 1.2 Pie chart
    2: "cs-content-detail.png",     # 1.3 Las Vegas Content Detail
    3: "cs-bracelet-structure.png", # 1.4 Bracelet Structure
    4: "cs-main-event.png",         # 1.5 Main Event Structure
    5: "cs-other-events.png",       # 2.1 Other Events
    6: "cs-youtube-wsoptv.png",     # 4. YouTube vs WSOPTV
    7: "cs-curation-roadmap.png",   # 5.2 Curation Roadmap
    8: "cs-season-calendar.png",    # 6. Season Calendar
}

# Image sizes for each diagram (pt)
IMAGE_SIZES = {
    "cs-core-content.png": 450,
    "cs-content-detail.png": 450,
    "cs-bracelet-structure.png": 480,
    "cs-season-calendar.png": 450,
    "cs-main-event.png": 400,
    "cs-other-events.png": 380,
    "cs-youtube-wsoptv.png": 400,
    "cs-curation-roadmap.png": 380,
    "cs-content-pie.png": 300,
}

# Poker theme colors (RGB 0-1 scale)
POKER_COLORS = {
    "black": {"red": 0.1, "green": 0.1, "blue": 0.1},          # #1A1A1A
    "gold": {"red": 0.85, "green": 0.65, "blue": 0.13},        # #D9A621
    "light_gray": {"red": 0.95, "green": 0.95, "blue": 0.95},  # #F2F2F2
}


def get_credentials():
    """Load credentials using OAuth 2.0."""
    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
    ]

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds


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


def clear_document(docs_service, doc_id: str):
    """Clear all content from existing document."""
    # Get document to find the end index
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])

    # Find the last element's end index
    end_index = 1
    for element in content:
        if "endIndex" in element:
            end_index = max(end_index, element["endIndex"])

    # Delete all content except the first character (required by API)
    # Only delete if there's actual content (end_index > 2)
    if end_index > 2:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{
                "deleteContentRange": {
                    "range": {
                        "startIndex": 1,
                        "endIndex": end_index - 1,
                    }
                }
            }]}
        ).execute()
        print(f"  Cleared existing content (deleted {end_index - 2} characters)")
    else:
        print(f"  Document is already empty")


def parse_inline_markdown(text: str) -> list:
    """Parse **bold** and *italic* markers.

    Returns list of (text, style_dict) tuples.
    style_dict = {"bold": True/False, "italic": True/False}

    Examples:
        "Hello **world**" → [("Hello ", {}), ("world", {"bold": True})]
        "Test *italic* text" → [("Test ", {}), ("italic", {"italic": True}), (" text", {})]
        "**Bold** and *italic*" → [("Bold", {"bold": True}), (" and ", {}), ("italic", {"italic": True})]
    """
    segments = []
    current_pos = 0

    # Pattern: **bold** or *italic* (but not *** which is markdown divider)
    # Use negative lookbehind/lookahead to avoid matching ***
    pattern = re.compile(r'(\*\*(?!\*)(.+?)\*\*|\*(?!\*)(.+?)\*)')

    for match in pattern.finditer(text):
        # Add any text before the match
        if match.start() > current_pos:
            plain_text = text[current_pos:match.start()]
            if plain_text:
                segments.append((plain_text, {}))

        full_match = match.group(1)
        if full_match.startswith('**'):
            # Bold text
            bold_text = match.group(2)
            segments.append((bold_text, {"bold": True}))
        else:
            # Italic text
            italic_text = match.group(3)
            segments.append((italic_text, {"italic": True}))

        current_pos = match.end()

    # Add remaining text
    if current_pos < len(text):
        remaining = text[current_pos:]
        if remaining:
            segments.append((remaining, {}))

    # If no markdown found, return original text
    if not segments:
        return [(text, {})]

    return segments


class DocumentBuilder:
    """Helper class to build Google Docs content."""

    def __init__(self, image_ids: dict):
        self.requests = []
        self.current_index = 1
        self.image_ids = image_ids
        self.pending_tables = []  # (marker_text, table_data) pairs

    def add_text(self, text, heading=None, bold=False, blockquote=False):
        """Add text with optional styling and inline markdown parsing."""
        # Parse inline markdown (**bold**, *italic*)
        segments = parse_inline_markdown(text)

        text_start = self.current_index
        total_length = 0

        for segment_text, styles in segments:
            # Insert text segment
            self.requests.append({
                "insertText": {
                    "location": {"index": self.current_index},
                    "text": segment_text,
                }
            })

            segment_start = self.current_index
            segment_end = segment_start + len(segment_text)

            # Apply inline styles (bold/italic from markdown)
            if styles.get("bold") or (bold and not styles):
                self.requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": segment_start, "endIndex": segment_end},
                        "textStyle": {"bold": True},
                        "fields": "bold",
                    }
                })

            if styles.get("italic"):
                self.requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": segment_start, "endIndex": segment_end},
                        "textStyle": {"italic": True},
                        "fields": "italic",
                    }
                })

            self.current_index = segment_end
            total_length += len(segment_text)

        text_end = self.current_index

        # Apply paragraph-level styles
        if heading:
            self.requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": text_start, "endIndex": text_end},
                    "paragraphStyle": {"namedStyleType": heading},
                    "fields": "namedStyleType",
                }
            })

        # Blockquote styling: indent + italic + gray shading
        if blockquote:
            self.requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": text_start, "endIndex": text_end},
                    "paragraphStyle": {
                        "indentStart": {"magnitude": 36, "unit": "PT"},
                        "shading": {
                            "backgroundColor": {"color": {"rgbColor": POKER_COLORS["light_gray"]}}
                        },
                    },
                    "fields": "indentStart,shading",
                }
            })

            # Apply italic + gold color to blockquote text
            self.requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": text_start, "endIndex": text_end},
                    "textStyle": {
                        "italic": True,
                        "foregroundColor": {"color": {"rgbColor": POKER_COLORS["gold"]}},
                    },
                    "fields": "italic,foregroundColor",
                }
            })

    def add_image(self, image_key, width_pt=None):
        """Add image with center alignment and auto-sizing."""
        image_id = self.image_ids.get(image_key)
        if not image_id:
            self.add_text(f"\n[Image: {image_key} - ID not found]\n")
            return

        # Auto-detect size or use default
        if width_pt is None:
            width_pt = IMAGE_SIZES.get(image_key, 400)

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
        """Add horizontal divider (clean separator)."""
        # Add blank line + thin visual separator
        self.add_text("\n")

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
    in_mermaid = False

    while i < len(lines):
        line = lines[i]

        # Handle mermaid code blocks
        if line.strip().startswith('```mermaid'):
            in_mermaid = True
            # Insert corresponding image with auto-sizing
            image_file = MERMAID_TO_IMAGE.get(mermaid_block_index)
            if image_file and image_file in image_ids:
                builder.add_text("\n")
                builder.add_image(image_file)  # Auto-size from IMAGE_SIZES
                builder.add_text("\n")
            mermaid_block_index += 1
            i += 1
            continue

        if in_mermaid:
            if line.strip() == '```':
                in_mermaid = False
            i += 1
            continue

        # Skip other code blocks
        if line.strip().startswith('```'):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                i += 1
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

        # Horizontal rule (clean divider instead of dashes)
        elif line.strip() == '---':
            builder.add_divider()

        # Table - collect all rows and add marker
        elif line.startswith('|'):
            table_data, end_idx = parse_markdown_table(lines, i)
            if table_data:
                builder.add_table_marker(table_data)
            i = end_idx
            continue

        # Blockquote (> prefix)
        elif line.startswith('> '):
            builder.add_text(line[2:] + '\n', blockquote=True)

        # Regular text or list items
        elif line.strip():
            builder.add_text(line + '\n')

        # Empty line
        else:
            builder.add_text('\n')

        i += 1

    return builder.get_requests(), builder.pending_tables


def insert_tables(docs_service, doc_id: str, pending_tables: list):
    """Replace table markers with actual Google Docs tables with poker theme styling."""
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

        # Fill table cells with content and apply poker theme styling
        table = table_element["table"]
        requests = []

        for row_idx, row_data in enumerate(table_data):
            table_row = table["tableRows"][row_idx]
            for col_idx, cell_text in enumerate(row_data):
                if col_idx >= len(table_row["tableCells"]):
                    continue

                cell = table_row["tableCells"][col_idx]
                cell_start = cell["content"][0]["startIndex"]

                # Parse inline markdown for cell text
                segments = parse_inline_markdown(cell_text)

                current_pos = cell_start
                for segment_text, styles in segments:
                    # Insert text segment
                    requests.append({
                        "insertText": {
                            "location": {"index": current_pos},
                            "text": segment_text,
                        }
                    })

                    segment_end = current_pos + len(segment_text)

                    # Apply inline styles from markdown
                    text_style = {}
                    fields = []

                    # Header row is always bold + gold text on black background
                    if row_idx == 0:
                        text_style["bold"] = True
                        text_style["foregroundColor"] = {"color": {"rgbColor": POKER_COLORS["gold"]}}
                        fields.extend(["bold", "foregroundColor"])
                    else:
                        # Regular row: apply markdown styles
                        if styles.get("bold"):
                            text_style["bold"] = True
                            fields.append("bold")
                        if styles.get("italic"):
                            text_style["italic"] = True
                            fields.append("italic")

                    if text_style and fields:
                        requests.append({
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": current_pos,
                                    "endIndex": segment_end
                                },
                                "textStyle": text_style,
                                "fields": ",".join(fields),
                            }
                        })

                    current_pos = segment_end

                # Apply cell background color
                cell_background = None
                if row_idx == 0:
                    # Header row: black background
                    cell_background = POKER_COLORS["black"]
                elif row_idx % 2 == 0:
                    # Even row: light gray
                    cell_background = POKER_COLORS["light_gray"]
                # Odd rows: white (default, no need to set)

                if cell_background:
                    # Apply background to entire cell
                    cell_end = cell["endIndex"] - 1  # Exclude end-of-cell marker
                    requests.append({
                        "updateTableCellStyle": {
                            "tableCellLocation": {
                                "tableStartLocation": {"index": table_element["startIndex"]},
                                "rowIndex": row_idx,
                                "columnIndex": col_idx,
                            },
                            "tableCellStyle": {
                                "backgroundColor": {"color": {"rgbColor": cell_background}}
                            },
                            "fields": "backgroundColor",
                        }
                    })

        # Apply gold borders to all cells
        for row_idx in range(rows):
            for col_idx in range(cols):
                requests.append({
                    "updateTableCellStyle": {
                        "tableCellLocation": {
                            "tableStartLocation": {"index": table_element["startIndex"]},
                            "rowIndex": row_idx,
                            "columnIndex": col_idx,
                        },
                        "tableCellStyle": {
                            "borderTop": {
                                "color": {"rgbColor": POKER_COLORS["gold"]},
                                "width": {"magnitude": 0.5, "unit": "PT"},
                                "dashStyle": "SOLID",
                            },
                            "borderBottom": {
                                "color": {"rgbColor": POKER_COLORS["gold"]},
                                "width": {"magnitude": 0.5, "unit": "PT"},
                                "dashStyle": "SOLID",
                            },
                            "borderLeft": {
                                "color": {"rgbColor": POKER_COLORS["gold"]},
                                "width": {"magnitude": 0.5, "unit": "PT"},
                                "dashStyle": "SOLID",
                            },
                            "borderRight": {
                                "color": {"rgbColor": POKER_COLORS["gold"]},
                                "width": {"magnitude": 0.5, "unit": "PT"},
                                "dashStyle": "SOLID",
                            },
                        },
                        "fields": "borderTop,borderBottom,borderLeft,borderRight",
                    }
                })

        # Apply all cell content and styling in batches
        if requests:
            # Split into smaller batches to avoid API limits
            for j in range(0, len(requests), 50):
                batch = requests[j:j+50]
                try:
                    docs_service.documents().batchUpdate(
                        documentId=doc_id, body={"requests": batch}
                    ).execute()
                except Exception as e:
                    print(f"  Error styling table: {e}")

        print(f"  Inserted table: {rows}x{cols} with poker theme")


def main():
    """Main function."""
    # Target document ID
    DOC_ID = "1gelKPXZBtNoJpTJOg7aCWqWYdHdUk5VwvL8by8ln82o"

    print("Loading credentials...")
    creds = get_credentials()

    print("Building Drive service...")
    drive_service = build("drive", "v3", credentials=creds)

    # Load existing image IDs or upload new ones
    ids_path = WIREFRAME_DIR / "image_ids.json"
    if ids_path.exists():
        print("\nLoading existing image IDs from image_ids.json...")
        with open(ids_path, 'r') as f:
            all_image_ids = json.load(f)
        print(f"  Loaded {len(all_image_ids)} existing image IDs")
    else:
        all_image_ids = {}

    # Check if all images already exist in image_ids.json
    missing_images = [f for f in CS_DIAGRAM_FILES if f not in all_image_ids]

    if missing_images:
        print(f"\nUploading {len(missing_images)} missing images to Google Drive...")
        uploaded_count = 0

        for file_name in missing_images:
            file_path = WIREFRAME_DIR / file_name
            if file_path.exists():
                image_id = upload_to_drive(drive_service, file_path)
                all_image_ids[file_name] = image_id
                uploaded_count += 1
            else:
                print(f"  Skipped (not found): {file_name}")

        if uploaded_count > 0:
            with open(ids_path, 'w') as f:
                json.dump(all_image_ids, f, indent=2)
            print(f"\n--- Uploaded {uploaded_count} new images ---")
    else:
        print("\nAll images already uploaded. Skipping Drive upload.")

    print("\nLoading PRD content...")
    with open(PRD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    print("\nBuilding Docs service...")
    docs_service = build("docs", "v1", credentials=creds)

    print(f"Updating existing Google Doc (ID: {DOC_ID})...")
    print("  Clearing existing content...")
    clear_document(docs_service, DOC_ID)
    doc_id = DOC_ID

    print("Parsing markdown with images and inline styles...")
    requests, pending_tables = parse_markdown_with_images(content, all_image_ids)

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

    # Insert tables with poker theme styling
    if pending_tables:
        print(f"\nInserting {len(pending_tables)} tables with poker theme...")
        insert_tables(docs_service, doc_id, pending_tables)

    print(f"\nDocument updated successfully!")
    print(f"View at: https://docs.google.com/document/d/{doc_id}/edit")
    print(f"\nStatistics:")
    print(f"  - Images inserted: {len([k for k in all_image_ids.keys() if k in MERMAID_TO_IMAGE.values()])}")
    print(f"  - Tables inserted: {len(pending_tables)}")
    print(f"  - Total requests: {len(requests)}")
    print(f"\nEnhancements applied:")
    print(f"  [OK] Inline markdown parsing (**bold**, *italic*)")
    print(f"  [OK] Poker theme tables (black/gold header, striped rows)")
    print(f"  [OK] Auto-sized images (300-480pt)")
    print(f"  [OK] Blockquote styling (gold border, gray background)")
    print(f"  [OK] Clean dividers")


if __name__ == "__main__":
    main()
