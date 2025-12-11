"""
Cache Block 테스트

TDD RED Phase: 4-Tier Cache System 검증
"""

import pytest


class TestCacheBlock:
    """Cache Block - 4-Tier 캐시 시스템 테스트"""

    @pytest.mark.asyncio
    async def test_cache_get_set(self):
        """기본 캐시 get/set"""
        from src.blocks.cache.service import CacheService

        service = CacheService()

        await service.set("key1", {"data": "value"}, ttl=3600)
        result = await service.get("key1")

        assert result is not None
        assert result["data"] == "value"

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """캐시 미스"""
        from src.blocks.cache.service import CacheService

        service = CacheService()

        result = await service.get("nonexistent_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_tier_hierarchy(self):
        """캐시 티어 계층 (L1 → L2 → L3 → L4)"""
        from src.blocks.cache.service import CacheService
        from src.blocks.cache.models import CacheTier

        service = CacheService()

        # L1 (Redis)에 데이터 설정
        await service.set("hot_content", {"id": "video1"}, tier=CacheTier.L1)

        # L1에서 먼저 조회
        result, tier = await service.get_with_tier("hot_content")
        assert tier == CacheTier.L1

    @pytest.mark.asyncio
    async def test_hot_content_detection(self):
        """Hot content 자동 감지 (7일 내 5회 이상 조회)"""
        from src.blocks.cache.service import CacheService

        service = CacheService()
        content_id = "popular_video"

        # 5회 조회 시뮬레이션
        for _ in range(5):
            await service.record_access(content_id)

        is_hot = await service.is_hot_content(content_id)
        assert is_hot is True

    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """캐시 무효화"""
        from src.blocks.cache.service import CacheService

        service = CacheService()

        await service.set("to_invalidate", {"data": "old"})
        await service.invalidate("to_invalidate")

        result = await service.get("to_invalidate")
        assert result is None

    @pytest.mark.asyncio
    async def test_ssd_cache_promotion(self):
        """Hot content SSD 승격"""
        from src.blocks.cache.service import CacheService
        from src.blocks.cache.models import CacheTier

        service = CacheService()
        content_id = "hot_video_123"

        # Hot content로 표시
        await service.mark_as_hot(content_id, file_path="/nas/videos/hot.mp4")

        # SSD (L2)로 승격 확인
        tier = await service.get_content_tier(content_id)
        assert tier == CacheTier.L2


class TestCacheBlockEvents:
    """Cache Block 이벤트 테스트"""

    @pytest.mark.asyncio
    async def test_cache_miss_event(self):
        """캐시 미스 이벤트 발행"""
        from src.blocks.cache.service import CacheService
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        received_events = []

        async def handler(msg):
            received_events.append(msg)

        await bus.subscribe("cache.miss", handler)

        service = CacheService()
        await service.get("missing_key")

        assert len(received_events) == 1
        assert received_events[0].payload["key"] == "missing_key"

    @pytest.mark.asyncio
    async def test_cache_evicted_event(self):
        """캐시 퇴출 이벤트 발행"""
        from src.blocks.cache.service import CacheService
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        received_events = []

        async def handler(msg):
            received_events.append(msg)

        await bus.subscribe("cache.evicted", handler)

        service = CacheService()
        await service.evict("old_key")

        assert len(received_events) == 1
