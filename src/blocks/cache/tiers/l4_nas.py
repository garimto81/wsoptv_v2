"""
L4 NAS Cache - Cold content 저장소 (18TB)
"""

from pathlib import Path


class L4NASCache:
    """NAS 기반 L4 캐시 (Cold content, 18TB)"""

    def __init__(self, nas_mount_path: str = "/nas/videos"):
        """초기화"""
        self.nas_path = Path(nas_mount_path)

    async def get_path(self, content_id: str) -> Path | None:
        """컨텐츠 파일 경로 조회"""
        # Mock: 기본 경로 반환
        file_path = self.nas_path / f"{content_id}.mp4"
        return file_path

    async def exists(self, content_id: str) -> bool:
        """컨텐츠 존재 확인 (Mock: 항상 True)"""
        # 실제 구현에서는 SMB 3.0 프로토콜로 파일 존재 확인
        return True

    async def get_size_tb(self) -> float:
        """현재 사용 중인 저장 공간 (TB)"""
        # Mock: 임의 값 반환
        return 12.5

    async def has_space(self, required_gb: float) -> bool:
        """사용 가능한 공간 확인"""
        current_tb = await self.get_size_tb()
        max_tb = 18.0
        required_tb = required_gb / 1024
        return (current_tb + required_tb) <= max_tb
