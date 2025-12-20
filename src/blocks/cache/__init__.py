"""
Cache Block - 4-Tier Cache System

L1: Redis (메모리 캐시, TTL 관리)
L2: SSD (Hot content, 500GB)
L3: Limiter (Rate limiting, 동시 스트리밍 제한)
L4: NAS (Cold content, 18TB)
"""

from .models import BandwidthInfo, CacheEntry, CacheTier, HotContent, StreamSlot
from .service import CacheService

__all__ = [
    "CacheTier",
    "CacheEntry",
    "HotContent",
    "StreamSlot",
    "BandwidthInfo",
    "CacheService",
]
