"""
L1 Redis Cache - 메모리 캐시 (TTL 관리)
"""

from datetime import datetime
from typing import Any

from ..models import CacheEntry, CacheTier


class L1RedisCache:
    """Redis 기반 L1 캐시 (인메모리 Mock 구현)"""

    def __init__(self):
        """초기화"""
        self._storage: dict[str, CacheEntry] = {}

    async def get(self, key: str) -> Any | None:
        """캐시 조회"""
        if key not in self._storage:
            return None

        entry = self._storage[key]

        # TTL 만료 확인
        if entry.is_expired():
            await self.delete(key)
            return None

        return entry.value

    async def set(self, key: str, value: Any, ttl: int = 600) -> None:
        """캐시 저장"""
        entry = CacheEntry(
            key=key,
            value=value,
            tier=CacheTier.L1,
            ttl=ttl,
            created_at=datetime.now()
        )
        self._storage[key] = entry

    async def delete(self, key: str) -> None:
        """캐시 삭제"""
        if key in self._storage:
            del self._storage[key]

    async def exists(self, key: str) -> bool:
        """키 존재 확인 (만료되지 않은 경우만)"""
        if key not in self._storage:
            return False

        entry = self._storage[key]
        if entry.is_expired():
            await self.delete(key)
            return False

        return True

    async def clear(self) -> None:
        """모든 캐시 삭제"""
        self._storage.clear()
