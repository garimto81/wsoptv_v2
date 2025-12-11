"""
Stream Block 테스트

TDD RED Phase: HTTP Range Streaming 검증
"""

import pytest


class TestStreamBlock:
    """Stream Block - Direct Play 스트리밍 테스트"""

    @pytest.mark.asyncio
    async def test_get_stream_url(self):
        """스트리밍 URL 획득"""
        from src.blocks.stream.service import StreamService

        service = StreamService()

        stream_info = await service.get_stream_url(
            content_id="video123",
            token="valid_token"
        )

        assert stream_info.url is not None
        assert stream_info.content_type == "video/mp4"

    @pytest.mark.asyncio
    async def test_range_request(self):
        """HTTP Range Request (206 Partial Content)"""
        from src.blocks.stream.service import StreamService

        service = StreamService()

        # Range: bytes=0-1023
        response = await service.get_range(
            content_id="video123",
            start_byte=0,
            end_byte=1023
        )

        assert response.status_code == 206
        assert response.content_length == 1024
        assert "bytes 0-1023" in response.content_range

    @pytest.mark.asyncio
    async def test_stream_from_cache_tier(self):
        """캐시 티어에 따른 스트리밍 소스 선택"""
        from src.blocks.stream.service import StreamService
        from src.blocks.cache.models import CacheTier

        service = StreamService()

        # Hot content는 SSD에서 스트리밍
        source = await service.get_stream_source("hot_video")
        assert source.tier in [CacheTier.L1, CacheTier.L2]

        # Cold content는 NAS에서 스트리밍
        source = await service.get_stream_source("cold_video")
        assert source.tier == CacheTier.L4

    @pytest.mark.asyncio
    async def test_concurrent_stream_limit(self):
        """동시 스트리밍 제한 (사용자당 최대 3개)"""
        from src.blocks.stream.service import StreamService

        service = StreamService()
        user_id = "user123"

        # 3개까지 허용
        for i in range(3):
            result = await service.start_stream(user_id, f"video{i}")
            assert result.allowed is True

        # 4번째는 거부
        result = await service.start_stream(user_id, "video4")
        assert result.allowed is False
        assert result.error == "concurrent_stream_limit_exceeded"

    @pytest.mark.asyncio
    async def test_bandwidth_throttling(self):
        """대역폭 조절 (Rate Limiter - L3)"""
        from src.blocks.stream.service import StreamService

        service = StreamService()

        # 사용자별 대역폭 제한 확인
        bandwidth = await service.get_user_bandwidth("user123")
        assert bandwidth.limit_mbps > 0
        assert bandwidth.current_mbps <= bandwidth.limit_mbps


class TestStreamBlockDependencies:
    """Stream Block 의존성 테스트"""

    @pytest.mark.asyncio
    async def test_requires_auth(self):
        """스트리밍 시 auth 검증 필요"""
        from src.blocks.stream.service import StreamService

        service = StreamService()

        with pytest.raises(Exception) as exc_info:
            await service.get_stream_url("video123", token=None)

        assert "authentication" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_requires_cache_lookup(self):
        """스트리밍 전 cache에서 위치 조회"""
        from src.blocks.stream.service import StreamService
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        cache_requests = []

        async def handler(msg):
            cache_requests.append(msg)

        await bus.subscribe("cache.get_location", handler)

        service = StreamService()
        await service.get_stream_url("video123", token="valid_token")

        assert len(cache_requests) >= 1


class TestStreamBlockEvents:
    """Stream Block 이벤트 테스트"""

    @pytest.mark.asyncio
    async def test_stream_started_event(self):
        """스트리밍 시작 이벤트"""
        from src.blocks.stream.service import StreamService
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        received_events = []

        async def handler(msg):
            received_events.append(msg)

        await bus.subscribe("stream.started", handler)

        service = StreamService()
        await service.start_stream("user123", "video123")

        assert len(received_events) == 1

    @pytest.mark.asyncio
    async def test_stream_ended_event(self):
        """스트리밍 종료 이벤트"""
        from src.blocks.stream.service import StreamService
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        received_events = []

        async def handler(msg):
            received_events.append(msg)

        await bus.subscribe("stream.ended", handler)

        service = StreamService()
        await service.end_stream("user123", "video123")

        assert len(received_events) == 1


class TestStreamRouter:
    """Stream Router 테스트"""

    @pytest.fixture
    def client(self):
        """TestClient 생성 (StreamService Mock 포함)"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.blocks.stream.router import router
        from src.blocks.stream.service import StreamService

        app = FastAPI()
        app.include_router(router)

        # StreamService를 app.state에 주입
        app.state.stream_service = StreamService()

        return TestClient(app)

    def test_get_stream_url_success(self, client):
        """스트리밍 URL 획득 성공"""
        response = client.get(
            "/stream/video123",
            headers={"Authorization": "Bearer valid_jwt_token_123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "content_type" in data
        assert data["content_type"] == "video/mp4"

    def test_get_stream_url_without_token(self, client):
        """토큰 없이 스트리밍 URL 요청"""
        response = client.get("/stream/video123")
        assert response.status_code == 401

    def test_start_stream(self, client):
        """스트리밍 시작"""
        response = client.post("/stream/video123/start")
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True

    def test_end_stream(self, client):
        """스트리밍 종료"""
        # 먼저 스트리밍 시작
        client.post("/stream/video123/start")

        # 스트리밍 종료
        response = client.post("/stream/video123/end")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ended"

    def test_get_bandwidth(self, client):
        """대역폭 조회"""
        response = client.get("/stream/video123/bandwidth")
        assert response.status_code == 200
        data = response.json()
        assert "limit_mbps" in data
        assert "current_mbps" in data
        assert data["limit_mbps"] > 0

    def test_concurrent_stream_limit(self, client):
        """동시 스트리밍 제한 테스트"""
        # 3개까지 허용
        for i in range(3):
            response = client.post(f"/stream/video{i}/start")
            assert response.status_code == 200

        # 4번째는 429 에러
        response = client.post("/stream/video4/start")
        assert response.status_code == 429


class TestRangeHandler:
    """HTTP Range Handler 테스트"""

    def test_parse_range_header_valid(self):
        """유효한 Range 헤더 파싱"""
        from src.blocks.stream.range_handler import parse_range_header

        result = parse_range_header("bytes=0-1023", total_size=10000)
        assert result is not None
        assert result.start_byte == 0
        assert result.end_byte == 1023

    def test_parse_range_header_open_end(self):
        """열린 끝 Range 헤더 파싱 (bytes=1000-)"""
        from src.blocks.stream.range_handler import parse_range_header

        result = parse_range_header("bytes=1000-", total_size=10000)
        assert result is not None
        assert result.start_byte == 1000
        # total_size가 주어지면 끝까지 (total_size - 1)
        assert result.end_byte == 9999

    def test_parse_range_header_invalid(self):
        """잘못된 Range 헤더"""
        from src.blocks.stream.range_handler import parse_range_header

        result = parse_range_header("invalid", total_size=10000)
        assert result is None

    def test_validate_range_success(self):
        """유효한 Range 검증"""
        from src.blocks.stream.range_handler import validate_range

        valid, error = validate_range(0, 1023, 10000)
        assert valid is True
        assert error is None

    def test_validate_range_invalid_start(self):
        """시작이 끝보다 큰 경우"""
        from src.blocks.stream.range_handler import validate_range

        valid, error = validate_range(1000, 500, 10000)
        assert valid is False
        assert error is not None

    def test_validate_range_start_exceeds_size(self):
        """시작이 파일 크기를 초과"""
        from src.blocks.stream.range_handler import validate_range

        valid, error = validate_range(10000, 20000, 10000)
        assert valid is False
        assert "start_byte >= total_size" in error

    def test_build_range_response_headers(self):
        """Range 응답 헤더 생성"""
        from src.blocks.stream.range_handler import build_range_response

        headers = build_range_response(10000, 0, 1023)
        assert "Content-Range" in headers
        assert headers["Content-Range"] == "bytes 0-1023/10000"
        assert headers["Content-Length"] == "1024"
        assert headers["Accept-Ranges"] == "bytes"
