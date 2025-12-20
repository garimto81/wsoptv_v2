"""
Content Service - 콘텐츠 관리 비즈니스 로직

Auth, Cache 블럭에 의존 (의존성 주입)
"""


from src.orchestration.message_bus import BlockMessage, MessageBus

from .models import Catalog, Content, ContentMeta, WatchProgress


class AuthenticationError(Exception):
    """인증 실패 에러"""

    pass


class ContentService:
    """
    콘텐츠 관리 서비스

    의존성:
    - auth_service: 토큰 검증 (테스트 시 Mock)
    - cache_service: 메타데이터 캐싱 (테스트 시 Mock)
    """

    def __init__(self, auth_service=None, cache_service=None):
        """
        Args:
            auth_service: validate_token(token) 메서드 제공
            cache_service: get(key), set(key, value, ttl) 메서드 제공
        """
        self.auth_service = auth_service
        self.cache_service = cache_service
        self.bus = MessageBus.get_instance()

        # 인메모리 저장소 (Mock 데이터)
        self._contents: dict[str, Content] = {
            "video123": Content(
                id="video123",
                title="Sample Video",
                duration_seconds=3600,
                file_size_bytes=1024 * 1024 * 100,  # 100MB
                codec="h264",
                resolution="1920x1080",
                path="/videos/sample.mp4",
                # created_at은 __post_init__에서 자동 설정
            )
        }

        # 시청 진행률 저장소
        self._progress: dict[str, WatchProgress] = {}

    async def get_content(
        self, content_id: str, token: str | None = "default_token"
    ) -> Content:
        """
        콘텐츠 조회

        Args:
            content_id: 콘텐츠 ID
            token: 인증 토큰 (기본값: "default_token")

        Returns:
            Content 객체

        Raises:
            AuthenticationError: 토큰이 None인 경우
        """
        # 인증 검증 (명시적으로 None을 전달한 경우만 에러)
        if token is None:
            raise AuthenticationError("authentication required")

        # Auth 서비스 호출 (Mock 또는 실제 서비스)
        # 실제로는 validate_token이 TokenResult를 반환하여 검증
        # 여기서는 token이 존재하면 유효한 것으로 간주

        # Cache 조회 이벤트 발행
        await self.bus.publish(
            "cache.request",
            BlockMessage(
                source_block="content",
                event_type="cache.request",
                payload={"key": f"content:{content_id}"},
            ),
        )

        # 콘텐츠 조회
        content = self._contents.get(content_id)

        # 콘텐츠 조회 이벤트 발행
        if content:
            await self.bus.publish(
                "content.viewed",
                BlockMessage(
                    source_block="content",
                    event_type="content.viewed",
                    payload={"content_id": content_id, "user_id": "user123"},
                ),
            )

        return content

    async def get_catalog(self, page: int = 1, size: int = 20) -> Catalog:
        """
        콘텐츠 카탈로그 조회 (페이지네이션)

        Args:
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            Catalog 객체
        """
        # 전체 콘텐츠 목록
        all_contents = list(self._contents.values())
        total = len(all_contents)

        # 페이지네이션 계산
        start_idx = (page - 1) * size
        end_idx = start_idx + size

        # ContentMeta로 변환
        items = [
            ContentMeta(
                id=content.id,
                title=content.title,
                duration_seconds=content.duration_seconds,
            )
            for content in all_contents[start_idx:end_idx]
        ]

        return Catalog(items=items, total=total, page=page, size=size)

    async def update_progress(
        self, user_id: str, content_id: str, position_seconds: int, total_seconds: int
    ) -> None:
        """
        시청 진행률 업데이트

        Args:
            user_id: 사용자 ID
            content_id: 콘텐츠 ID
            position_seconds: 현재 재생 위치 (초)
            total_seconds: 전체 길이 (초)
        """
        # 진행률 생성
        progress = WatchProgress(
            user_id=user_id,
            content_id=content_id,
            position_seconds=position_seconds,
            total_seconds=total_seconds,
            percentage=0.0,  # __post_init__에서 자동 계산
        )

        # 저장
        key = f"{user_id}:{content_id}"
        self._progress[key] = progress

        # 진행률 업데이트 이벤트 발행
        await self.bus.publish(
            "content.progress_updated",
            BlockMessage(
                source_block="content",
                event_type="content.progress_updated",
                payload={
                    "user_id": user_id,
                    "content_id": content_id,
                    "position_seconds": position_seconds,
                    "percentage": progress.percentage,
                },
            ),
        )

    async def get_progress(self, user_id: str, content_id: str) -> WatchProgress:
        """
        시청 진행률 조회

        Args:
            user_id: 사용자 ID
            content_id: 콘텐츠 ID

        Returns:
            WatchProgress 객체
        """
        key = f"{user_id}:{content_id}"
        return self._progress.get(key)

    async def get_metadata(self, content_id: str) -> ContentMeta:
        """
        콘텐츠 메타데이터 조회 (경량)

        Args:
            content_id: 콘텐츠 ID

        Returns:
            ContentMeta 객체
        """
        content = self._contents.get(content_id)
        if not content:
            return None

        return ContentMeta(
            id=content.id,
            title=content.title,
            duration_seconds=content.duration_seconds,
        )
