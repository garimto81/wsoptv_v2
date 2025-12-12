"""
NAS 스캔 및 카탈로그 동기화 스크립트

호스트에서 실행하여 NAS 파일을 스캔하고 API로 동기화합니다.

사용법:
    python scripts/sync_nas.py [--nas-path Z:\ARCHIVE] [--api-url http://localhost:8002]
"""

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import requests

# 비디오 확장자
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts"}


def scan_nas(nas_path: str) -> list[dict]:
    """NAS 폴더를 스캔하여 비디오 파일 목록 반환"""
    files = []
    nas_root = Path(nas_path)

    if not nas_root.exists():
        print(f"Error: NAS path not found: {nas_path}")
        sys.exit(1)

    print(f"Scanning: {nas_path}")

    for file_path in nas_root.rglob("*"):
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()
        if ext not in VIDEO_EXTENSIONS:
            continue

        # 숨김 파일 제외
        if file_path.name.startswith("."):
            continue

        try:
            stat = file_path.stat()
            files.append({
                "id": str(uuid.uuid4()),
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size_bytes": stat.st_size,
                "file_extension": ext.lstrip("."),
                "file_category": "VIDEO",
                "is_hidden_file": False,
            })
        except OSError as e:
            print(f"Warning: Cannot access {file_path}: {e}")

    print(f"Found {len(files)} video files")
    return files


def sync_to_api(api_url: str, files: list[dict], batch_size: int = 500) -> dict:
    """API로 파일 목록 동기화"""
    total_result = {
        "created": 0,
        "updated": 0,
        "deleted": 0,
        "skipped": 0,
        "errors": 0,
    }

    # 배치로 나누어 동기화
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        print(f"Syncing batch {i // batch_size + 1}: {len(batch)} files...")

        try:
            response = requests.post(
                f"{api_url}/api/v1/catalog/sync",
                json={"files": batch},
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                total_result["created"] += result.get("created", 0)
                total_result["updated"] += result.get("updated", 0)
                total_result["deleted"] += result.get("deleted", 0)
                total_result["skipped"] += result.get("skipped", 0)
                total_result["errors"] += result.get("errors", 0)

                if result.get("error_messages"):
                    for msg in result["error_messages"][:5]:
                        print(f"  Error: {msg}")
            else:
                print(f"Error: API returned {response.status_code}")
                print(response.text)
                total_result["errors"] += len(batch)

        except requests.RequestException as e:
            print(f"Error: {e}")
            total_result["errors"] += len(batch)

    return total_result


def main():
    parser = argparse.ArgumentParser(description="NAS 스캔 및 카탈로그 동기화")
    parser.add_argument(
        "--nas-path",
        default=r"Z:\ARCHIVE",
        help="NAS 경로 (기본값: Z:\\ARCHIVE)",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8002",
        help="API URL (기본값: http://localhost:8002)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="스캔만 하고 동기화하지 않음",
    )

    args = parser.parse_args()

    # NAS 스캔
    files = scan_nas(args.nas_path)

    if not files:
        print("No video files found.")
        return

    # 샘플 출력
    print("\nSample files:")
    for f in files[:5]:
        size_mb = f["file_size_bytes"] / (1024 * 1024)
        print(f"  - {f['file_name']} ({size_mb:.1f} MB)")

    if args.dry_run:
        print("\n[Dry run] Skipping sync.")
        return

    # API 동기화
    print(f"\nSyncing to {args.api_url}...")
    result = sync_to_api(args.api_url, files)

    print("\n=== Sync Result ===")
    print(f"Created: {result['created']}")
    print(f"Updated: {result['updated']}")
    print(f"Deleted: {result['deleted']}")
    print(f"Skipped: {result['skipped']}")
    print(f"Errors:  {result['errors']}")


if __name__ == "__main__":
    main()
