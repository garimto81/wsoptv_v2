"""
CacheWarmerWorker

NAS → SSD 캐시 워밍 작업 처리
"""

from typing import Optional
from ..models import Task, TaskResult


class CacheWarmerWorker:
    """캐시 워밍 워커 (NAS → SSD 복사)"""

    def __init__(self, cache_service=None):
        """
        Args:
            cache_service: CacheService 인스턴스 (Optional)
        """
        self._cache_service = cache_service

    async def process(self, task: Task) -> TaskResult:
        """
        캐시 워밍 작업 처리 (NAS → SSD)

        Args:
            task: Task 인스턴스

        Returns:
            TaskResult: 작업 결과
        """
        try:
            # Payload 검증
            nas_path = task.payload.get("nas_path")
            ssd_path = task.payload.get("ssd_path")

            if not nas_path:
                # cache.miss 이벤트에서 온 경우 key만 있을 수 있음
                key = task.payload.get("key")
                if key:
                    nas_path = task.payload.get("nas_path", f"/nas/videos/{key}.mp4")
                    ssd_path = f"/ssd/cache/{key}.mp4"
                else:
                    return TaskResult(
                        success=False,
                        message="Missing required field: nas_path or key",
                        data={}
                    )

            if not ssd_path:
                ssd_path = f"/ssd/cache/{nas_path.split('/')[-1]}"

            # Mock: NAS → SSD 복사 시뮬레이션
            # 실제 구현에서는 shutil.copy 또는 rsync 사용
            copied_size = 1024 * 1024 * 100  # 100MB (Mock)

            return TaskResult(
                success=True,
                message=f"Cache warmed: {nas_path} → {ssd_path}",
                data={
                    "nas_path": nas_path,
                    "ssd_path": ssd_path,
                    "size_bytes": copied_size,
                }
            )

        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Cache warming failed: {str(e)}",
                data={"error": str(e)}
            )
