"""
Cache Service - 4-Tier Cache 통합 서비스
"""

from pathlib import Path
from typing import Any, Optional
from datetime import datetime

from .models import CacheTier, HotContent, BandwidthInfo
from .tiers import L1RedisCache, L2SSDCache, L3Limiter, L4NASCache


class CacheService:
    """
    4-Tier Cache 통합 서비스

    L1: Redis (메타데이터, 세션) → TTL 600초
    L2: SSD (Hot content) → 500GB
    L3: Limiter (Rate limit) → 사용자당 3개 스트리밍
    L4: NAS (Cold content) → 18TB
    """

    def __init__(self):
        """초기화"""
        self.l1 = L1RedisCache()
        self.l2 = L2SSDCache()
        self.l3 = L3Limiter(max_streams_per_user=3)
        self.l4 = L4NASCache()

        # Hot content 추적
        self._hot_content: dict[str, HotContent] = {}

        # MessageBus (이벤트 발행용)
        self._bus = None

    def _get_bus(self):
        """MessageBus 인스턴스 lazy loading"""
        if self._bus is None:
            from src.orchestration.message_bus import MessageBus
            self._bus = MessageBus.get_instance()
        return self._bus

    async def get(self, key: str) -> Any | None:
        """
        캐시 조회 (L1 → L2 → L3 → L4 순서)

        Returns:
            캐시 값 또는 None
        """
        # L1 Redis 조회
        value = await self.l1.get(key)
        if value is not None:
            return value

        # 캐시 미스 이벤트 발행
        bus = self._get_bus()
        from src.orchestration.message_bus import BlockMessage
        await bus.publish("cache.miss", BlockMessage(
            source_block="cache",
            event_type="cache.miss",
            payload={"key": key}
        ))

        return None

    async def set(self, key: str, value: Any, ttl: int = 600, tier: Optional[CacheTier] = None) -> None:
        """
        캐시 저장

        Args:
            key: 캐시 키
            value: 캐시 값
            ttl: TTL (초)
            tier: 캐시 티어 (None이면 L1)
        """
        if tier is None or tier == CacheTier.L1:
            await self.l1.set(key, value, ttl)

    async def get_with_tier(self, key: str) -> tuple[Any, CacheTier] | tuple[None, None]:
        """
        캐시 조회 + 티어 정보 반환

        Returns:
            (값, 티어) 또는 (None, None)
        """
        # L1 조회
        value = await self.l1.get(key)
        if value is not None:
            return value, CacheTier.L1

        return None, None

    async def invalidate(self, key: str) -> None:
        """캐시 무효화 (삭제)"""
        await self.l1.delete(key)

    async def evict(self, key: str) -> None:
        """
        캐시 퇴출 (강제 삭제)

        이벤트 발행: cache.evicted
        """
        await self.l1.delete(key)

        # 퇴출 이벤트 발행
        bus = self._get_bus()
        from src.orchestration.message_bus import BlockMessage
        await bus.publish("cache.evicted", BlockMessage(
            source_block="cache",
            event_type="cache.evicted",
            payload={"key": key}
        ))

    async def record_access(self, content_id: str) -> None:
        """
        컨텐츠 접근 기록 (Hot content 감지용)

        7일 내 5회 이상 조회 시 Hot content로 분류
        """
        if content_id not in self._hot_content:
            self._hot_content[content_id] = HotContent(content_id=content_id)

        self._hot_content[content_id].record_view()

    async def is_hot_content(self, content_id: str) -> bool:
        """Hot content 여부 확인"""
        if content_id not in self._hot_content:
            return False

        return self._hot_content[content_id].is_hot()

    async def mark_as_hot(self, content_id: str, file_path: str) -> None:
        """
        Hot content로 표시 및 SSD(L2)로 승격

        이벤트 발행: cache.ssd_promoted
        """
        # SSD에 저장
        await self.l2.store(content_id, file_path)

        # Hot content 기록
        if content_id not in self._hot_content:
            self._hot_content[content_id] = HotContent(content_id=content_id, view_count=5)
        else:
            self._hot_content[content_id].view_count = max(5, self._hot_content[content_id].view_count)

        # SSD 승격 이벤트 발행
        bus = self._get_bus()
        from src.orchestration.message_bus import BlockMessage
        await bus.publish("cache.ssd_promoted", BlockMessage(
            source_block="cache",
            event_type="cache.ssd_promoted",
            payload={"content_id": content_id}
        ))

    async def get_content_tier(self, content_id: str) -> CacheTier:
        """컨텐츠가 저장된 티어 확인"""
        # L2 SSD 확인
        if await self.l2.exists(content_id):
            return CacheTier.L2

        # L4 NAS (기본)
        return CacheTier.L4

    async def get_stream_path(self, content_id: str) -> Optional[Path]:
        """
        스트리밍용 파일 경로 조회 (L2 → L4)

        Returns:
            파일 경로 또는 None
        """
        # L2 SSD 확인
        path = await self.l2.get_path(content_id)
        if path is not None:
            return path

        # L4 NAS 확인
        path = await self.l4.get_path(content_id)
        return path

    async def acquire_stream_slot(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        스트리밍 슬롯 획득 (L3 Limiter)

        Returns:
            (성공 여부, 실패 사유)
        """
        # 임시 content_id (실제로는 요청에서 받아야 함)
        content_id = f"stream_{user_id}_{datetime.now().timestamp()}"
        return await self.l3.acquire_slot(user_id, content_id)

    async def release_stream_slot(self, user_id: str) -> None:
        """스트리밍 슬롯 해제"""
        await self.l3.release_slot(user_id)

    async def get_user_bandwidth(self, user_id: str) -> BandwidthInfo:
        """사용자 대역폭 정보 조회"""
        return await self.l3.get_bandwidth_info(user_id)
