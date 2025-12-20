"""
Admin Block Service

관리자 기능 비즈니스 로직:
- 대시보드 통계 조회
- 사용자 관리 (목록, 승인, 정지)
- 시스템 상태 모니터링
- 활성 스트림 조회
"""

from datetime import datetime

from src.orchestration.message_bus import BlockMessage, MessageBus

from .models import (
    CacheStats,
    ContentStats,
    DashboardData,
    StreamStats,
    SystemHealth,
    UserStats,
)


class AdminService:
    """
    관리자 서비스

    TDD 구현:
    - 모든 블럭 이벤트 구독 (통계 업데이트)
    - 관리자 권한 검증 필수
    - 인메모리 통계 저장소 (테스트용)
    """

    def __init__(self, auth_service=None):
        """
        초기화

        Args:
            auth_service: Auth 서비스 (Mock 가능)
        """
        self._auth_service = auth_service
        self._bus = MessageBus.get_instance()
        self._subscribers_initialized = False

        # 통계 저장소 (실제로는 Redis/DB 사용)
        self._stats = {
            # 사용자 통계
            "user_total": 2,  # 초기 사용자 (일반 user123, 관리자 admin_user)
            "user_pending": 1,  # pending_user_123
            "user_active": 2,
            "user_suspended": 0,
            # 콘텐츠 통계
            "content_total": 500,
            "content_storage_gb": 18000.0,
            "content_by_category": {"Movie": 200, "Drama": 150, "Variety": 150},
            # 스트리밍 통계
            "stream_active": 0,
            "stream_peak_today": 0,
            "stream_bandwidth_mbps": 0.0,
            # 캐시 통계
            "cache_hits": 850,
            "cache_misses": 150,
            "cache_ssd_gb": 450.0,
            "cache_hot_contents": 120,
            # 시스템 상태
            "system_api": "healthy",
            "system_redis": "healthy",
            "system_postgres": "healthy",
            "system_meilisearch": "healthy",
        }

        # 활성 스트림 목록
        self._active_streams: list[dict] = []

        # 사용자 목록 (Mock 데이터)
        self._users = {
            "user123": {
                "id": "user123",
                "email": "test@test.com",
                "status": "active",
                "is_admin": False,
            },
            "admin_user": {
                "id": "admin_user",
                "email": "admin@test.com",
                "status": "active",
                "is_admin": True,
            },
            "pending_user_123": {
                "id": "pending_user_123",
                "email": "pending@test.com",
                "status": "pending",
                "is_admin": False,
            },
            "active_user_123": {
                "id": "active_user_123",
                "email": "active@test.com",
                "status": "active",
                "is_admin": False,
            },
        }

        # 토큰 매핑 (Mock)
        self._tokens = {
            "admin_token_123": "admin_user",
            "user_token_123": "user123",
        }

    async def _setup_event_subscribers(self):
        """이벤트 구독 설정 (async)"""
        if self._subscribers_initialized:
            return

        # Auth Block 이벤트
        await self._bus.subscribe("auth.user_registered", self._on_user_registered)
        await self._bus.subscribe("auth.user_login", self._on_user_login)
        await self._bus.subscribe("auth.user_approved", self._on_user_approved)

        # Stream Block 이벤트
        await self._bus.subscribe("stream.started", self._on_stream_started)
        await self._bus.subscribe("stream.ended", self._on_stream_ended)

        # Cache Block 이벤트
        await self._bus.subscribe("cache.hit", self._on_cache_hit)
        await self._bus.subscribe("cache.miss", self._on_cache_miss)

        # Content Block 이벤트
        await self._bus.subscribe("content.viewed", self._on_content_viewed)

        # Worker Block 이벤트
        await self._bus.subscribe("worker.task_completed", self._on_task_completed)

        self._subscribers_initialized = True

    async def _on_user_registered(self, msg: BlockMessage):
        """사용자 등록 이벤트 핸들러"""
        self._stats["user_total"] += 1
        self._stats["user_pending"] += 1

    async def _on_user_login(self, msg: BlockMessage):
        """사용자 로그인 이벤트 핸들러"""
        pass  # 로그인 통계 추적 가능

    async def _on_user_approved(self, msg: BlockMessage):
        """사용자 승인 이벤트 핸들러"""
        self._stats["user_pending"] -= 1
        self._stats["user_active"] += 1

    async def _on_stream_started(self, msg: BlockMessage):
        """스트림 시작 이벤트 핸들러"""
        self._stats["stream_active"] += 1
        if self._stats["stream_active"] > self._stats["stream_peak_today"]:
            self._stats["stream_peak_today"] = self._stats["stream_active"]

        # 활성 스트림 목록에 추가
        stream_data = {
            "stream_id": msg.payload.get("stream_id"),
            "user_id": msg.payload.get("user_id"),
            "started_at": datetime.now().isoformat(),
            "bandwidth_mbps": 20.0,  # Mock
        }
        self._active_streams.append(stream_data)

        # 대역폭 업데이트
        self._stats["stream_bandwidth_mbps"] = len(self._active_streams) * 20.0

    async def _on_stream_ended(self, msg: BlockMessage):
        """스트림 종료 이벤트 핸들러"""
        self._stats["stream_active"] -= 1

        # 활성 스트림 목록에서 제거
        stream_id = msg.payload.get("stream_id")
        self._active_streams = [
            s for s in self._active_streams if s["stream_id"] != stream_id
        ]

        # 대역폭 업데이트
        self._stats["stream_bandwidth_mbps"] = len(self._active_streams) * 20.0

    async def _on_cache_hit(self, msg: BlockMessage):
        """캐시 히트 이벤트 핸들러"""
        self._stats["cache_hits"] += 1

    async def _on_cache_miss(self, msg: BlockMessage):
        """캐시 미스 이벤트 핸들러"""
        self._stats["cache_misses"] += 1

    async def _on_content_viewed(self, msg: BlockMessage):
        """콘텐츠 조회 이벤트 핸들러"""
        pass  # 콘텐츠 조회 통계 추적 가능

    async def _on_task_completed(self, msg: BlockMessage):
        """워커 작업 완료 이벤트 핸들러"""
        pass  # 워커 작업 통계 추적 가능

    async def _require_admin(self, token: str) -> None:
        """
        관리자 권한 확인

        Args:
            token: 인증 토큰

        Raises:
            ValueError: 잘못된 토큰
            PermissionError: 관리자 권한 없음
        """
        # 토큰 검증
        user_id = self._tokens.get(token)
        if not user_id:
            raise ValueError("Invalid token")

        # 사용자 조회
        user = self._users.get(user_id)
        if not user:
            raise ValueError("User not found")

        # 관리자 권한 확인
        if not user.get("is_admin", False):
            raise PermissionError("Admin permission required")

    async def get_dashboard(self, token: str) -> DashboardData:
        """
        대시보드 데이터 조회

        Args:
            token: 관리자 토큰

        Returns:
            대시보드 통합 데이터

        Raises:
            ValueError: 잘못된 토큰
            PermissionError: 관리자 권한 없음
        """
        # 이벤트 구독 초기화
        await self._setup_event_subscribers()

        await self._require_admin(token)

        # 캐시 히트율 계산
        total_cache = self._stats["cache_hits"] + self._stats["cache_misses"]
        hit_rate = self._stats["cache_hits"] / total_cache if total_cache > 0 else 0.0

        return DashboardData(
            user_stats=UserStats(
                total=self._stats["user_total"],
                pending=self._stats["user_pending"],
                active=self._stats["user_active"],
                suspended=self._stats["user_suspended"],
            ),
            content_stats=ContentStats(
                total=self._stats["content_total"],
                storage_used_gb=self._stats["content_storage_gb"],
                by_category=self._stats["content_by_category"],
            ),
            stream_stats=StreamStats(
                active_streams=self._stats["stream_active"],
                peak_today=self._stats["stream_peak_today"],
                bandwidth_mbps=self._stats["stream_bandwidth_mbps"],
            ),
            cache_stats=CacheStats(
                hit_rate=hit_rate,
                ssd_usage_gb=self._stats["cache_ssd_gb"],
                hot_contents=self._stats["cache_hot_contents"],
            ),
            system_health=SystemHealth(
                api=self._stats["system_api"],
                redis=self._stats["system_redis"],
                postgres=self._stats["system_postgres"],
                meilisearch=self._stats["system_meilisearch"],
            ),
        )

    async def get_user_list(
        self, token: str, page: int = 1, size: int = 20
    ) -> dict:
        """
        사용자 목록 조회

        Args:
            token: 관리자 토큰
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            사용자 목록 및 페이징 정보

        Raises:
            ValueError: 잘못된 토큰
            PermissionError: 관리자 권한 없음
        """
        await self._require_admin(token)

        # 사용자 목록 (간단한 페이징)
        users_list = list(self._users.values())
        total = len(users_list)

        # 페이징
        start = (page - 1) * size
        end = start + size
        paginated_users = users_list[start:end]

        return {
            "users": paginated_users,
            "total": total,
            "page": page,
            "size": size,
        }

    async def approve_user(self, token: str, user_id: str) -> dict:
        """
        사용자 승인

        Args:
            token: 관리자 토큰
            user_id: 승인할 사용자 ID

        Returns:
            승인 결과

        Raises:
            ValueError: 잘못된 토큰 또는 사용자 없음
            PermissionError: 관리자 권한 없음
        """
        await self._require_admin(token)

        user = self._users.get(user_id)
        if not user:
            raise ValueError("User not found")

        # 상태 업데이트
        user["status"] = "active"

        # 이벤트 발행
        await self._bus.publish(
            "admin.user_approved",
            BlockMessage(
                source_block="admin",
                event_type="user_approved",
                payload={"user_id": user_id, "status": "active"},
            ),
        )

        return {"status": "success", "user_id": user_id, "new_status": "active"}

    async def suspend_user(self, token: str, user_id: str) -> dict:
        """
        사용자 정지

        Args:
            token: 관리자 토큰
            user_id: 정지할 사용자 ID

        Returns:
            정지 결과

        Raises:
            ValueError: 잘못된 토큰 또는 사용자 없음
            PermissionError: 관리자 권한 없음
        """
        await self._require_admin(token)

        user = self._users.get(user_id)
        if not user:
            raise ValueError("User not found")

        # 상태 업데이트
        user["status"] = "suspended"

        # 이벤트 발행
        await self._bus.publish(
            "admin.user_suspended",
            BlockMessage(
                source_block="admin",
                event_type="user_suspended",
                payload={"user_id": user_id, "status": "suspended"},
            ),
        )

        return {"status": "success", "user_id": user_id, "new_status": "suspended"}

    async def get_system_stats(self, token: str) -> SystemHealth:
        """
        시스템 상태 조회

        Args:
            token: 관리자 토큰

        Returns:
            시스템 상태

        Raises:
            ValueError: 잘못된 토큰
            PermissionError: 관리자 권한 없음
        """
        await self._require_admin(token)

        return SystemHealth(
            api=self._stats["system_api"],
            redis=self._stats["system_redis"],
            postgres=self._stats["system_postgres"],
            meilisearch=self._stats["system_meilisearch"],
        )

    async def get_active_streams(self, token: str) -> list[dict]:
        """
        활성 스트림 목록 조회

        Args:
            token: 관리자 토큰

        Returns:
            활성 스트림 목록

        Raises:
            ValueError: 잘못된 토큰
            PermissionError: 관리자 권한 없음
        """
        await self._require_admin(token)

        return self._active_streams
