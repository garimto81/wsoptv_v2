"""
NASScannerWorker

NAS 스토리지 스캔 작업 처리
"""

from typing import Optional
from ..models import Task, TaskResult


class NASScannerWorker:
    """NAS 스캔 워커"""

    def __init__(self, cache_service=None):
        """
        Args:
            cache_service: CacheService 인스턴스 (Optional)
        """
        self._cache_service = cache_service

    async def process(self, task: Task) -> TaskResult:
        """
        NAS 스캔 작업 처리

        Args:
            task: Task 인스턴스

        Returns:
            TaskResult: 작업 결과
        """
        try:
            # Payload 검증
            if "path" not in task.payload:
                return TaskResult(
                    success=False,
                    message="Missing required field: path",
                    data={}
                )

            scan_path = task.payload["path"]

            # Mock: NAS 스캔 시뮬레이션
            # 실제 구현에서는 os.walk 또는 pathlib 사용하여 파일 목록 수집
            scanned_files = [
                {"name": "video1.mp4", "size": 1024 * 1024 * 150, "path": f"{scan_path}/video1.mp4"},
                {"name": "video2.mp4", "size": 1024 * 1024 * 200, "path": f"{scan_path}/video2.mp4"},
                {"name": "video3.mp4", "size": 1024 * 1024 * 180, "path": f"{scan_path}/video3.mp4"},
            ]

            return TaskResult(
                success=True,
                message=f"NAS scan completed: {scan_path}",
                data={
                    "scan_path": scan_path,
                    "total_files": len(scanned_files),
                    "files": scanned_files,
                    "total_size_bytes": sum(f["size"] for f in scanned_files),
                }
            )

        except Exception as e:
            return TaskResult(
                success=False,
                message=f"NAS scan failed: {str(e)}",
                data={"error": str(e)}
            )
