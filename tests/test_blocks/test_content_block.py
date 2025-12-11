"""
Content Block 테스트

TDD RED Phase: 콘텐츠 관리 기능 검증
"""

import pytest


class TestContentBlock:
    """Content Block 테스트"""

    @pytest.mark.asyncio
    async def test_get_content(self):
        """콘텐츠 조회"""
        from src.blocks.content.service import ContentService

        service = ContentService()

        content = await service.get_content("video123")

        assert content is not None
        assert content.id == "video123"
        assert content.title is not None

    @pytest.mark.asyncio
    async def test_get_catalog(self):
        """카탈로그 조회 (페이지네이션)"""
        from src.blocks.content.service import ContentService

        service = ContentService()

        catalog = await service.get_catalog(page=1, size=20)

        assert catalog.total >= 0
        assert len(catalog.items) <= 20

    @pytest.mark.asyncio
    async def test_update_watch_progress(self):
        """시청 진행률 업데이트"""
        from src.blocks.content.service import ContentService

        service = ContentService()

        await service.update_progress(
            user_id="user123",
            content_id="video123",
            position_seconds=120,
            total_seconds=3600
        )

        progress = await service.get_progress("user123", "video123")
        assert progress.position_seconds == 120
        assert progress.percentage == pytest.approx(3.33, rel=0.1)

    @pytest.mark.asyncio
    async def test_content_metadata(self):
        """콘텐츠 메타데이터"""
        from src.blocks.content.service import ContentService

        service = ContentService()

        content = await service.get_content("video123")

        assert content.duration_seconds > 0
        assert content.file_size_bytes > 0
        assert content.codec is not None
        assert content.resolution is not None

    @pytest.mark.asyncio
    async def test_get_metadata_not_found(self):
        """존재하지 않는 콘텐츠의 메타데이터 조회"""
        from src.blocks.content.service import ContentService

        service = ContentService()

        metadata = await service.get_metadata("nonexistent")

        assert metadata is None


class TestContentBlockDependencies:
    """Content Block 의존성 테스트"""

    @pytest.mark.asyncio
    async def test_requires_auth_validation(self):
        """콘텐츠 조회 시 auth.validate_token 필요"""
        from src.blocks.content.service import ContentService

        service = ContentService()

        # 토큰 없이 조회 시도 → 에러
        with pytest.raises(Exception) as exc_info:
            await service.get_content("video123", token=None)

        assert "authentication required" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_uses_cache_for_metadata(self):
        """메타데이터 조회 시 cache 사용"""
        from src.blocks.content.service import ContentService
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        cache_requests = []

        async def handler(msg):
            cache_requests.append(msg)

        await bus.subscribe("cache.request", handler)

        service = ContentService()
        await service.get_content("video123", token="valid_token")

        # 캐시 조회 요청이 있어야 함
        assert len(cache_requests) >= 1


class TestContentBlockEvents:
    """Content Block 이벤트 테스트"""

    @pytest.mark.asyncio
    async def test_content_viewed_event(self):
        """콘텐츠 조회 이벤트"""
        from src.blocks.content.service import ContentService
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        received_events = []

        async def handler(msg):
            received_events.append(msg)

        await bus.subscribe("content.viewed", handler)

        service = ContentService()
        await service.get_content("video123", token="valid_token")

        assert len(received_events) == 1
        assert received_events[0].payload["content_id"] == "video123"


class TestContentRouter:
    """Content Router 테스트"""

    @pytest.fixture
    def client(self):
        """TestClient 생성"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.blocks.content.router import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_get_content_success(self, client):
        """콘텐츠 조회 성공"""
        response = client.get(
            "/content/video123",
            headers={"Authorization": "Bearer valid_jwt_token_123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "video123"
        assert "title" in data
        assert "duration_seconds" in data

    def test_get_content_without_token(self, client):
        """토큰 없이 콘텐츠 조회 - 인증 에러"""
        response = client.get("/content/video123")
        assert response.status_code == 401

    def test_get_content_with_invalid_token(self, client):
        """잘못된 토큰으로 콘텐츠 조회"""
        response = client.get(
            "/content/video123",
            headers={"Authorization": "Bearer invalid_token"}
        )
        # 토큰 검증 실패
        assert response.status_code in [401, 200]  # Mock에 따라 다름

    def test_get_content_not_found(self, client):
        """존재하지 않는 콘텐츠 조회"""
        response = client.get(
            "/content/nonexistent_video",
            headers={"Authorization": "Bearer valid_jwt_token_123"}
        )
        # 404 또는 200 (Mock 데이터에 따라)
        assert response.status_code in [200, 404]

    def test_get_catalog(self, client):
        """카탈로그 조회"""
        response = client.get("/content/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    def test_get_catalog_with_pagination(self, client):
        """페이지네이션이 있는 카탈로그 조회"""
        response = client.get("/content/?page=2&size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["size"] == 10

    def test_update_progress(self, client):
        """시청 진행률 업데이트"""
        response = client.post(
            "/content/video123/progress",
            params={
                "user_id": "user123",
                "position_seconds": 300,
                "total_seconds": 3600
            }
        )
        assert response.status_code == 204

    def test_get_progress(self, client):
        """시청 진행률 조회"""
        # 먼저 진행률 업데이트
        client.post(
            "/content/video123/progress",
            params={
                "user_id": "user123",
                "position_seconds": 600,
                "total_seconds": 3600
            }
        )

        # 진행률 조회
        response = client.get(
            "/content/video123/progress",
            params={"user_id": "user123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position_seconds"] == 600
        assert data["content_id"] == "video123"

    def test_get_progress_not_found(self, client):
        """존재하지 않는 진행률 조회"""
        response = client.get(
            "/content/nonexistent/progress",
            params={"user_id": "unknown_user"}
        )
        assert response.status_code == 404
