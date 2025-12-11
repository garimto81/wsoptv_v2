"""
Admin Block 테스트

TDD RED Phase: Admin 블럭의 핵심 기능 검증
- 대시보드 통계 조회
- 사용자 관리 (목록, 승인, 정지)
- 시스템 상태 모니터링
- 스트리밍 현황 조회
- 관리자 권한 검증
"""

import pytest
from datetime import datetime


class TestAdminBlock:
    """Admin Block - L2 (All Blocks 의존) 블럭 테스트"""

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self):
        """대시보드 데이터 조회 (관리자 권한 필요)"""
        from src.blocks.admin.service import AdminService

        service = AdminService()
        admin_token = "admin_token_123"

        dashboard = await service.get_dashboard(admin_token)

        # UserStats 검증
        assert dashboard.user_stats is not None
        assert dashboard.user_stats.total >= 0
        assert dashboard.user_stats.pending >= 0
        assert dashboard.user_stats.active >= 0
        assert dashboard.user_stats.suspended >= 0

        # ContentStats 검증
        assert dashboard.content_stats is not None
        assert dashboard.content_stats.total >= 0
        assert dashboard.content_stats.storage_used_gb >= 0
        assert isinstance(dashboard.content_stats.by_category, dict)

        # StreamStats 검증
        assert dashboard.stream_stats is not None
        assert dashboard.stream_stats.active_streams >= 0
        assert dashboard.stream_stats.peak_today >= 0
        assert dashboard.stream_stats.bandwidth_mbps >= 0

        # CacheStats 검증
        assert dashboard.cache_stats is not None
        assert 0.0 <= dashboard.cache_stats.hit_rate <= 1.0
        assert dashboard.cache_stats.ssd_usage_gb >= 0
        assert dashboard.cache_stats.hot_contents >= 0

        # SystemHealth 검증
        assert dashboard.system_health is not None
        assert dashboard.system_health.api in ["healthy", "degraded", "down"]
        assert dashboard.system_health.redis in ["healthy", "degraded", "down"]
        assert dashboard.system_health.postgres in ["healthy", "degraded", "down"]
        assert dashboard.system_health.meilisearch in ["healthy", "degraded", "down"]

    @pytest.mark.asyncio
    async def test_get_user_list(self):
        """사용자 목록 조회 (관리자 권한 필요)"""
        from src.blocks.admin.service import AdminService

        service = AdminService()
        admin_token = "admin_token_123"

        result = await service.get_user_list(admin_token, page=1, size=20)

        assert "users" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert isinstance(result["users"], list)
        assert result["total"] >= 0
        assert result["page"] == 1
        assert result["size"] == 20

    @pytest.mark.asyncio
    async def test_approve_user(self):
        """사용자 승인 (관리자 권한 필요)"""
        from src.blocks.admin.service import AdminService

        service = AdminService()
        admin_token = "admin_token_123"
        user_id = "pending_user_123"

        result = await service.approve_user(admin_token, user_id)

        assert result["status"] == "success"
        assert result["user_id"] == user_id
        assert result["new_status"] == "active"

    @pytest.mark.asyncio
    async def test_suspend_user(self):
        """사용자 정지 (관리자 권한 필요)"""
        from src.blocks.admin.service import AdminService

        service = AdminService()
        admin_token = "admin_token_123"
        user_id = "active_user_123"

        result = await service.suspend_user(admin_token, user_id)

        assert result["status"] == "success"
        assert result["user_id"] == user_id
        assert result["new_status"] == "suspended"

    @pytest.mark.asyncio
    async def test_get_system_stats(self):
        """시스템 상태 조회 (관리자 권한 필요)"""
        from src.blocks.admin.service import AdminService

        service = AdminService()
        admin_token = "admin_token_123"

        system_health = await service.get_system_stats(admin_token)

        assert system_health is not None
        assert system_health.api in ["healthy", "degraded", "down"]
        assert system_health.redis in ["healthy", "degraded", "down"]
        assert system_health.postgres in ["healthy", "degraded", "down"]
        assert system_health.meilisearch in ["healthy", "degraded", "down"]

    @pytest.mark.asyncio
    async def test_get_active_streams(self):
        """활성 스트림 목록 조회 (관리자 권한 필요)"""
        from src.blocks.admin.service import AdminService

        service = AdminService()
        admin_token = "admin_token_123"

        streams = await service.get_active_streams(admin_token)

        assert isinstance(streams, list)
        # 각 스트림은 stream_id, user_id, started_at, bandwidth_mbps 포함
        for stream in streams:
            assert "stream_id" in stream
            assert "user_id" in stream
            assert "started_at" in stream
            assert "bandwidth_mbps" in stream

    @pytest.mark.asyncio
    async def test_requires_admin_permission(self):
        """관리자 권한 필요 - 일반 사용자 접근 차단"""
        from src.blocks.admin.service import AdminService

        service = AdminService()
        user_token = "user_token_123"  # 일반 사용자 토큰

        # 대시보드 접근 시도 → PermissionError
        with pytest.raises(PermissionError) as exc_info:
            await service.get_dashboard(user_token)
        assert "Admin permission required" in str(exc_info.value)

        # 사용자 목록 접근 시도 → PermissionError
        with pytest.raises(PermissionError) as exc_info:
            await service.get_user_list(user_token)
        assert "Admin permission required" in str(exc_info.value)

        # 사용자 승인 시도 → PermissionError
        with pytest.raises(PermissionError) as exc_info:
            await service.approve_user(user_token, "some_user")
        assert "Admin permission required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """잘못된 토큰으로 접근 시도"""
        from src.blocks.admin.service import AdminService

        service = AdminService()
        invalid_token = "invalid_token"

        # 대시보드 접근 시도 → ValueError (Invalid token)
        with pytest.raises(ValueError) as exc_info:
            await service.get_dashboard(invalid_token)
        assert "Invalid token" in str(exc_info.value)


class TestAdminBlockEvents:
    """Admin Block 이벤트 구독 테스트"""

    @pytest.mark.asyncio
    async def test_subscribe_user_registered_event(self):
        """사용자 등록 이벤트 구독 → user_stats 업데이트"""
        from src.blocks.admin.service import AdminService
        from src.orchestration.message_bus import MessageBus, BlockMessage

        service = AdminService()
        bus = MessageBus.get_instance()

        # 초기 통계
        admin_token = "admin_token_123"
        dashboard_before = await service.get_dashboard(admin_token)
        total_before = dashboard_before.user_stats.total

        # 사용자 등록 이벤트 발행
        await bus.publish(
            "auth.user_registered",
            BlockMessage(
                source_block="auth",
                event_type="user_registered",
                payload={"user_id": "new_user_456", "email": "new@test.com"},
            ),
        )

        # 약간의 대기 (이벤트 처리)
        import asyncio
        await asyncio.sleep(0.1)

        # 통계 확인 - 사용자 수 증가
        dashboard_after = await service.get_dashboard(admin_token)
        assert dashboard_after.user_stats.total == total_before + 1

    @pytest.mark.asyncio
    async def test_subscribe_stream_started_event(self):
        """스트림 시작 이벤트 구독 → stream_stats 업데이트"""
        from src.blocks.admin.service import AdminService
        from src.orchestration.message_bus import MessageBus, BlockMessage

        service = AdminService()
        bus = MessageBus.get_instance()

        # 초기 통계
        admin_token = "admin_token_123"
        dashboard_before = await service.get_dashboard(admin_token)
        active_before = dashboard_before.stream_stats.active_streams

        # 스트림 시작 이벤트 발행
        await bus.publish(
            "stream.started",
            BlockMessage(
                source_block="stream",
                event_type="stream_started",
                payload={"stream_id": "stream_789", "user_id": "user123"},
            ),
        )

        # 약간의 대기 (이벤트 처리)
        import asyncio
        await asyncio.sleep(0.1)

        # 통계 확인 - 활성 스트림 수 증가
        dashboard_after = await service.get_dashboard(admin_token)
        assert dashboard_after.stream_stats.active_streams == active_before + 1

    @pytest.mark.asyncio
    async def test_subscribe_stream_ended_event(self):
        """스트림 종료 이벤트 구독 → stream_stats 업데이트"""
        from src.blocks.admin.service import AdminService
        from src.orchestration.message_bus import MessageBus, BlockMessage

        service = AdminService()
        bus = MessageBus.get_instance()

        # 스트림 시작 (활성 스트림 추가)
        await bus.publish(
            "stream.started",
            BlockMessage(
                source_block="stream",
                event_type="stream_started",
                payload={"stream_id": "stream_999", "user_id": "user123"},
            ),
        )

        import asyncio
        await asyncio.sleep(0.1)

        # 현재 통계
        admin_token = "admin_token_123"
        dashboard_before = await service.get_dashboard(admin_token)
        active_before = dashboard_before.stream_stats.active_streams

        # 스트림 종료 이벤트 발행
        await bus.publish(
            "stream.ended",
            BlockMessage(
                source_block="stream",
                event_type="stream_ended",
                payload={"stream_id": "stream_999", "user_id": "user123"},
            ),
        )

        await asyncio.sleep(0.1)

        # 통계 확인 - 활성 스트림 수 감소
        dashboard_after = await service.get_dashboard(admin_token)
        assert dashboard_after.stream_stats.active_streams == active_before - 1

    @pytest.mark.asyncio
    async def test_subscribe_cache_miss_event(self):
        """캐시 미스 이벤트 구독 → cache_stats 업데이트"""
        from src.blocks.admin.service import AdminService
        from src.orchestration.message_bus import MessageBus, BlockMessage

        service = AdminService()
        bus = MessageBus.get_instance()

        # 캐시 미스 이벤트 발행
        await bus.publish(
            "cache.miss",
            BlockMessage(
                source_block="cache",
                event_type="cache_miss",
                payload={"content_id": "content_123"},
            ),
        )

        # 약간의 대기 (이벤트 처리)
        import asyncio
        await asyncio.sleep(0.1)

        # 캐시 히트율이 업데이트되었는지 확인
        admin_token = "admin_token_123"
        dashboard = await service.get_dashboard(admin_token)
        assert 0.0 <= dashboard.cache_stats.hit_rate <= 1.0
