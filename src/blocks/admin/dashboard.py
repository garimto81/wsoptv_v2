"""
Admin Block Dashboard

실시간 통계 집계 및 대시보드 데이터 생성
"""

from typing import Dict
from .models import (
    DashboardData,
    UserStats,
    ContentStats,
    StreamStats,
    CacheStats,
    SystemHealth,
)


class DashboardAggregator:
    """
    대시보드 통계 집계기

    실시간 통계를 집계하여 대시보드 데이터 생성
    """

    def __init__(self, stats_store: Dict):
        """
        초기화

        Args:
            stats_store: 통계 저장소 (dict)
        """
        self._stats = stats_store

    def aggregate_user_stats(self) -> UserStats:
        """
        사용자 통계 집계

        Returns:
            사용자 통계
        """
        return UserStats(
            total=self._stats.get("user_total", 0),
            pending=self._stats.get("user_pending", 0),
            active=self._stats.get("user_active", 0),
            suspended=self._stats.get("user_suspended", 0),
        )

    def aggregate_content_stats(self) -> ContentStats:
        """
        콘텐츠 통계 집계

        Returns:
            콘텐츠 통계
        """
        return ContentStats(
            total=self._stats.get("content_total", 0),
            storage_used_gb=self._stats.get("content_storage_gb", 0.0),
            by_category=self._stats.get("content_by_category", {}),
        )

    def aggregate_stream_stats(self) -> StreamStats:
        """
        스트리밍 통계 집계

        Returns:
            스트리밍 통계
        """
        return StreamStats(
            active_streams=self._stats.get("stream_active", 0),
            peak_today=self._stats.get("stream_peak_today", 0),
            bandwidth_mbps=self._stats.get("stream_bandwidth_mbps", 0.0),
        )

    def aggregate_cache_stats(self) -> CacheStats:
        """
        캐시 통계 집계

        Returns:
            캐시 통계
        """
        hits = self._stats.get("cache_hits", 0)
        misses = self._stats.get("cache_misses", 0)
        total = hits + misses

        hit_rate = hits / total if total > 0 else 0.0

        return CacheStats(
            hit_rate=hit_rate,
            ssd_usage_gb=self._stats.get("cache_ssd_gb", 0.0),
            hot_contents=self._stats.get("cache_hot_contents", 0),
        )

    def aggregate_system_health(self) -> SystemHealth:
        """
        시스템 상태 집계

        Returns:
            시스템 상태
        """
        return SystemHealth(
            api=self._stats.get("system_api", "unknown"),
            redis=self._stats.get("system_redis", "unknown"),
            postgres=self._stats.get("system_postgres", "unknown"),
            meilisearch=self._stats.get("system_meilisearch", "unknown"),
        )

    def aggregate_dashboard(self) -> DashboardData:
        """
        전체 대시보드 데이터 집계

        Returns:
            대시보드 통합 데이터
        """
        return DashboardData(
            user_stats=self.aggregate_user_stats(),
            content_stats=self.aggregate_content_stats(),
            stream_stats=self.aggregate_stream_stats(),
            cache_stats=self.aggregate_cache_stats(),
            system_health=self.aggregate_system_health(),
        )
