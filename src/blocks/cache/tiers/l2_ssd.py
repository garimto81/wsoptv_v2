"""
L2 SSD Cache - Hot content 캐시 (500GB)
"""

from pathlib import Path


class L2SSDCache:
    """SSD 기반 L2 캐시 (Hot content 전용)"""

    def __init__(self, cache_dir: str = "/cache/ssd"):
        """초기화"""
        self.cache_dir = Path(cache_dir)
        self._content_paths: dict[str, Path] = {}
        self._max_size_gb = 500

    async def get_path(self, content_id: str) -> Path | None:
        """컨텐츠 파일 경로 조회"""
        return self._content_paths.get(content_id)

    async def store(self, content_id: str, source_path: str) -> Path:
        """
        Hot content를 SSD로 복사 (실제로는 경로만 저장)

        실제 구현에서는:
        1. source_path에서 SSD로 파일 복사
        2. 용량 제한 확인 (500GB)
        3. LRU 정책으로 오래된 파일 삭제
        """
        # Mock: 경로만 저장
        cache_path = self.cache_dir / f"{content_id}.mp4"
        self._content_paths[content_id] = cache_path
        return cache_path

    async def exists(self, content_id: str) -> bool:
        """컨텐츠 존재 확인"""
        return content_id in self._content_paths

    async def delete(self, content_id: str) -> None:
        """컨텐츠 삭제"""
        if content_id in self._content_paths:
            del self._content_paths[content_id]

    async def get_size_gb(self) -> float:
        """현재 사용 중인 캐시 크기 (GB)"""
        # Mock: 임의 값 반환
        return len(self._content_paths) * 2.5  # 파일당 평균 2.5GB

    async def has_space(self, required_gb: float) -> bool:
        """사용 가능한 공간 확인"""
        current = await self.get_size_gb()
        return (current + required_gb) <= self._max_size_gb
