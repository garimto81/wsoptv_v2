#!/usr/bin/env python3
"""
NAS 파일 스캔 및 카탈로그 동기화 스크립트

Z:/ARCHIVE 폴더의 비디오 파일을 스캔하여 Block F 카탈로그 API로 동기화합니다.
"""

import os
import sys
import uuid
import json
import requests
from pathlib import Path
from typing import Generator

# 설정
NAS_BASE_PATH = "Z:/ARCHIVE"
API_BASE_URL = "http://localhost:8002/api/v1"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}
BATCH_SIZE = 2000  # 전체 파일을 한 번에 동기화


def scan_video_files(base_path: str) -> Generator[dict, None, None]:
    """비디오 파일 스캔"""
    base = Path(base_path)

    for root, dirs, files in os.walk(base):
        # 숨김 폴더 제외
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if file.startswith('.'):
                continue

            ext = Path(file).suffix.lower()
            if ext not in VIDEO_EXTENSIONS:
                continue

            file_path = Path(root) / file
            try:
                stat = file_path.stat()
                yield {
                    "id": str(uuid.uuid4()),
                    "file_path": str(file_path),
                    "file_name": file,
                    "file_size_bytes": stat.st_size,
                    "file_extension": ext.lstrip('.').upper(),
                    "file_category": "VIDEO",
                    "is_hidden_file": False,
                }
            except OSError as e:
                print(f"  [SKIP] {file_path}: {e}")


def sync_batch(files: list[dict]) -> dict:
    """배치 동기화 API 호출"""
    response = requests.post(
        f"{API_BASE_URL}/catalog/sync",
        json={"files": files},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def main():
    print("=" * 60)
    print("NAS → Catalog 동기화")
    print("=" * 60)
    print(f"NAS 경로: {NAS_BASE_PATH}")
    print(f"API URL: {API_BASE_URL}")
    print()

    # NAS 마운트 확인
    if not os.path.exists(NAS_BASE_PATH):
        print(f"[ERROR] NAS 경로를 찾을 수 없습니다: {NAS_BASE_PATH}")
        sys.exit(1)

    # 파일 스캔
    print("[SCAN] 비디오 파일 스캔 중...")
    files = list(scan_video_files(NAS_BASE_PATH))
    print(f"   발견된 비디오 파일: {len(files)}개")
    print()

    if not files:
        print("[INFO] 동기화할 파일이 없습니다.")
        return

    # 배치 동기화
    print("[SYNC] 카탈로그 동기화 중...")
    total_created = 0
    total_updated = 0
    total_skipped = 0
    total_errors = 0

    for i in range(0, len(files), BATCH_SIZE):
        batch = files[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(files) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"   배치 {batch_num}/{total_batches} ({len(batch)}개)...", end=" ")

        try:
            result = sync_batch(batch)
            total_created += result["created"]
            total_updated += result["updated"]
            total_skipped += result["skipped"]
            total_errors += result["errors"]
            print(f"OK - 생성:{result['created']} 업데이트:{result['updated']} 스킵:{result['skipped']}")

            if result["error_messages"]:
                for err in result["error_messages"][:3]:
                    print(f"      [WARN] {err}")
        except requests.RequestException as e:
            print(f"FAIL: {e}")
            total_errors += len(batch)

    # 결과 출력
    print()
    print("=" * 60)
    print("[RESULT] 동기화 결과")
    print("=" * 60)
    print(f"   총 파일: {len(files)}개")
    print(f"   생성: {total_created}개")
    print(f"   업데이트: {total_updated}개")
    print(f"   스킵: {total_skipped}개")
    print(f"   오류: {total_errors}개")
    print()

    # 카탈로그 통계 확인
    try:
        stats = requests.get(f"{API_BASE_URL}/catalog/stats", timeout=10).json()
        print("[STATS] 카탈로그 통계")
        print(f"   총 아이템: {stats['total_items']}개")
        print(f"   표시 가능: {stats['visible_items']}개")
        print(f"   프로젝트: {[p['code'] for p in stats['projects']]}")
        print(f"   연도: {stats['years'][:5]}..." if len(stats['years']) > 5 else f"   연도: {stats['years']}")
    except Exception as e:
        print(f"[WARN] 통계 조회 실패: {e}")


if __name__ == "__main__":
    main()
