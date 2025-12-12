"""
Stream Service - HTTP Range Streaming 비즈니스 로직

기능:
- 스트리밍 URL 제공
- HTTP Range Request 처리
- 캐시 티어별 소스 선택
- 동시 스트리밍 제한 (사용자당 최대 3개)
- 대역폭 조절
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..cache.models import CacheTier
from .models import (
    BandwidthInfo,
    RangeResponse,
    StreamInfo,
    StreamResult,
    StreamSession,
    StreamSource,
)


class StreamService:
    """스트리밍 서비스"""

    MAX_CONCURRENT_STREAMS = 3
    DEFAULT_BANDWIDTH_LIMIT_MBPS = 100.0
    CHUNK_SIZE = 1024 * 1024  # 1MB

    def __init__(
        self,
        auth_service: Optional[Any] = None,
        cache_service: Optional[Any] = None,
        content_service: Optional[Any] = None,
    ):
        """
        Args:
            auth_service: 인증 서비스 (Mock 가능)
            cache_service: 캐시 서비스 (Mock 가능)
            content_service: 컨텐츠 서비스 (Mock 가능)
        """
        self._auth_service = auth_service
        self._cache_service = cache_service
        self._content_service = content_service

        # 활성 스트리밍 세션 (user_id -> [content_ids])
        self._active_streams: Dict[str, List[str]] = {}

        # 사용자별 대역폭 사용량 (user_id -> current_mbps)
        self._bandwidth_usage: Dict[str, float] = {}

    async def get_stream_url(self, content_id: str, token: str) -> StreamInfo:
        """
        스트리밍 URL 획득

        Args:
            content_id: 컨텐츠 ID
            token: 인증 토큰

        Returns:
            StreamInfo: 스트리밍 정보

        Raises:
            ValueError: 인증 실패 시
        """
        # Auth 검증
        if token is None:
            raise ValueError("Authentication required")

        if self._auth_service:
            # 실제 auth 서비스 사용
            token_result = await self._auth_service.validate_token(token)
            if not token_result.valid:
                raise ValueError("Invalid authentication token")

        # Content metadata 조회
        content_type = "video/mp4"
        content_length = 104857600  # 100MB 기본값

        if self._content_service:
            metadata = await self._content_service.get_metadata(content_id)
            content_type = metadata.content_type
            content_length = metadata.size

        # Cache 위치 조회 (MessageBus 통해 - 항상 발행)
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        await bus.publish(
            "cache.get_location",
            {"content_id": content_id, "requester": "stream"},
        )

        # 스트리밍 URL 생성
        stream_url = f"/stream/{content_id}/video"

        return StreamInfo(
            url=stream_url, content_type=content_type, content_length=content_length
        )

    async def get_range(
        self, content_id: str, start_byte: int, end_byte: int
    ) -> RangeResponse:
        """
        HTTP Range Request 처리 (206 Partial Content)

        Args:
            content_id: 컨텐츠 ID
            start_byte: 시작 바이트
            end_byte: 종료 바이트

        Returns:
            RangeResponse: Range 응답
        """
        # 스트리밍 소스 조회
        source = await self.get_stream_source(content_id)

        # 파일에서 Range 데이터 읽기
        file_path = source.path
        total_size = file_path.stat().st_size if file_path.exists() else 104857600

        # 실제 end_byte 조정 (파일 크기 초과 방지)
        actual_end = min(end_byte, total_size - 1)
        content_length = actual_end - start_byte + 1

        # Range 데이터 읽기 (Mock)
        data = b"\x00" * content_length

        if file_path.exists():
            with open(file_path, "rb") as f:
                f.seek(start_byte)
                data = f.read(content_length)

        # Content-Range 헤더 생성
        content_range = f"bytes {start_byte}-{actual_end}/{total_size}"

        return RangeResponse(
            status_code=206,
            content_length=content_length,
            content_range=content_range,
            data=data,
        )

    async def get_stream_source(self, content_id: str) -> StreamSource:
        """
        캐시 티어별 스트리밍 소스 선택

        Args:
            content_id: 컨텐츠 ID

        Returns:
            StreamSource: 스트리밍 소스
        """
        # Cache 서비스에서 경로 조회
        if self._cache_service:
            cache_path = await self._cache_service.get_stream_path(content_id)
            tier = self._determine_tier(cache_path)
            return StreamSource(path=cache_path, tier=tier)

        # Flat Catalog에서 file_path 조회
        try:
            from uuid import UUID
            from src.blocks.flat_catalog.service import get_flat_catalog_service

            catalog_service = get_flat_catalog_service()
            item = catalog_service.get_by_id(UUID(content_id))

            if item:
                # Windows 환경: 경로 그대로 사용
                file_path = item.file_path
                return StreamSource(
                    path=Path(file_path), tier=CacheTier.L4
                )
        except Exception as e:
            print(f"Failed to get catalog item: {e}")

        # Fallback
        return StreamSource(
            path=Path(f"Z:/ARCHIVE/{content_id}.mp4"), tier=CacheTier.L4
        )

    def _determine_tier(self, path: Path) -> CacheTier:
        """경로에서 캐시 티어 추론"""
        path_str = str(path).lower()
        if "/l1/" in path_str or "ssd" in path_str:
            return CacheTier.L1
        elif "/l2/" in path_str:
            return CacheTier.L2
        elif "/l3/" in path_str:
            return CacheTier.L3
        else:
            return CacheTier.L4

    async def start_stream(self, user_id: str, content_id: str) -> StreamResult:
        """
        스트리밍 시작 (동시 스트리밍 제한 검증)

        Args:
            user_id: 사용자 ID
            content_id: 컨텐츠 ID

        Returns:
            StreamResult: 시작 허용 여부
        """
        # 현재 스트리밍 수 확인
        current_streams = self._active_streams.get(user_id, [])

        if len(current_streams) >= self.MAX_CONCURRENT_STREAMS:
            return StreamResult(
                allowed=False, error="concurrent_stream_limit_exceeded"
            )

        # 스트리밍 세션 추가
        if user_id not in self._active_streams:
            self._active_streams[user_id] = []

        self._active_streams[user_id].append(content_id)

        # 이벤트 발행
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        await bus.publish(
            "stream.started",
            {"user_id": user_id, "content_id": content_id, "timestamp": datetime.now()},
        )

        return StreamResult(allowed=True)

    async def end_stream(self, user_id: str, content_id: str) -> None:
        """
        스트리밍 종료

        Args:
            user_id: 사용자 ID
            content_id: 컨텐츠 ID
        """
        # 세션 제거
        if user_id in self._active_streams:
            if content_id in self._active_streams[user_id]:
                self._active_streams[user_id].remove(content_id)

            # 빈 리스트 제거
            if not self._active_streams[user_id]:
                del self._active_streams[user_id]

        # 이벤트 발행
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        await bus.publish(
            "stream.ended",
            {
                "user_id": user_id,
                "content_id": content_id,
                "timestamp": datetime.now(),
                "duration": 0,  # TODO: 실제 duration 계산
            },
        )

    async def get_user_bandwidth(self, user_id: str) -> BandwidthInfo:
        """
        사용자 대역폭 조회

        Args:
            user_id: 사용자 ID

        Returns:
            BandwidthInfo: 대역폭 정보
        """
        # 사용자별 대역폭 제한 (설정 가능)
        limit_mbps = self.DEFAULT_BANDWIDTH_LIMIT_MBPS

        # 현재 사용량 조회
        current_mbps = self._bandwidth_usage.get(user_id, 0.0)

        return BandwidthInfo(limit_mbps=limit_mbps, current_mbps=current_mbps)
