"""
Admin Block Models

대시보드, 통계, 시스템 상태 모델
"""

from dataclasses import dataclass


@dataclass
class UserStats:
    """사용자 통계"""
    total: int          # 전체 사용자 수
    pending: int        # 승인 대기 사용자 수
    active: int         # 활성 사용자 수
    suspended: int      # 정지된 사용자 수


@dataclass
class ContentStats:
    """콘텐츠 통계"""
    total: int                      # 전체 콘텐츠 수
    storage_used_gb: float          # 사용 중인 스토리지 (GB)
    by_category: dict[str, int]     # 카테고리별 콘텐츠 수


@dataclass
class StreamStats:
    """스트리밍 통계"""
    active_streams: int     # 현재 활성 스트림 수
    peak_today: int         # 오늘의 피크 동시 스트림 수
    bandwidth_mbps: float   # 현재 사용 중인 대역폭 (Mbps)


@dataclass
class CacheStats:
    """캐시 통계"""
    hit_rate: float         # 캐시 히트율 (0.0 ~ 1.0)
    ssd_usage_gb: float     # SSD 캐시 사용량 (GB)
    hot_contents: int       # 핫 콘텐츠 수


@dataclass
class SystemHealth:
    """시스템 상태"""
    api: str            # API 서버 상태 (healthy, degraded, down)
    redis: str          # Redis 상태
    postgres: str       # PostgreSQL 상태
    meilisearch: str    # Meilisearch 상태


@dataclass
class DashboardData:
    """대시보드 통합 데이터"""
    user_stats: UserStats
    content_stats: ContentStats
    stream_stats: StreamStats
    cache_stats: CacheStats
    system_health: SystemHealth
