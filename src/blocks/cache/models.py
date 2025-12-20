"""
Cache Block Models - 4-Tier Cache 데이터 모델
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CacheTier(Enum):
    """캐시 계층 정의"""
    L1 = "L1_REDIS"      # Redis 메모리 캐시
    L2 = "L2_SSD"        # SSD 캐시 (Hot content)
    L3 = "L3_LIMITER"    # Rate Limiter
    L4 = "L4_NAS"        # NAS 저장소


@dataclass
class CacheEntry:
    """캐시 엔트리"""
    key: str
    value: Any
    tier: CacheTier
    ttl: int
    created_at: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """TTL 만료 확인"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl


@dataclass
class StreamSlot:
    """스트리밍 슬롯 (동시 스트리밍 제한용)"""
    user_id: str
    content_id: str
    acquired_at: datetime = field(default_factory=datetime.now)


@dataclass
class HotContent:
    """Hot content 추적 (7일 내 5회 이상 조회 시 SSD 승격)"""
    content_id: str
    view_count: int = 0
    last_viewed: datetime = field(default_factory=datetime.now)

    def record_view(self) -> None:
        """조회 기록"""
        self.view_count += 1
        self.last_viewed = datetime.now()

    def is_hot(self) -> bool:
        """Hot content 판정 (7일 내 5회 이상)"""
        days_elapsed = (datetime.now() - self.last_viewed).days
        return self.view_count >= 5 and days_elapsed <= 7


@dataclass
class BandwidthInfo:
    """대역폭 정보"""
    limit_mbps: float
    current_mbps: float

    def has_available_bandwidth(self) -> bool:
        """사용 가능한 대역폭 확인"""
        return self.current_mbps < self.limit_mbps
