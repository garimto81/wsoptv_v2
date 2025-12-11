"""
ThumbnailWorker

비디오 썸네일 생성 작업 처리
"""

from typing import Optional
from ..models import Task, TaskResult


class ThumbnailWorker:
    """썸네일 생성 워커"""

    def __init__(self, cache_service=None):
        """
        Args:
            cache_service: CacheService 인스턴스 (Optional)
        """
        self._cache_service = cache_service

    async def process(self, task: Task) -> TaskResult:
        """
        썸네일 생성 작업 처리

        Args:
            task: Task 인스턴스

        Returns:
            TaskResult: 작업 결과
        """
        try:
            # Payload 검증
            if "video_id" not in task.payload:
                return TaskResult(
                    success=False,
                    message="Missing required field: video_id",
                    data={}
                )

            video_id = task.payload["video_id"]
            frame_time = task.payload.get("frame_time", 5)  # 기본 5초

            # Mock: 썸네일 생성 시뮬레이션
            # 실제 구현에서는 FFmpeg 등을 사용하여 비디오에서 프레임 추출
            thumbnail_path = f"/ssd/thumbs/{video_id}_frame{frame_time}.jpg"

            return TaskResult(
                success=True,
                message=f"Thumbnail generated for {video_id}",
                data={
                    "video_id": video_id,
                    "thumbnail_path": thumbnail_path,
                    "frame_time": frame_time,
                }
            )

        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Thumbnail generation failed: {str(e)}",
                data={"error": str(e)}
            )
