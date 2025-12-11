"""
Stream Block Data Models

HTTP Range Streaming을 위한 데이터 모델 정의
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..cache.models import CacheTier


@dataclass
class StreamInfo:
    """스트리밍 정보"""

    url: str
    content_type: str
    content_length: int

    def __post_init__(self):
        if not self.url:
            raise ValueError("url is required")
        if not self.content_type:
            raise ValueError("content_type is required")
        if self.content_length < 0:
            raise ValueError("content_length must be non-negative")


@dataclass
class RangeRequest:
    """HTTP Range Request"""

    start_byte: int
    end_byte: int

    def __post_init__(self):
        if self.start_byte < 0:
            raise ValueError("start_byte must be non-negative")
        if self.end_byte < self.start_byte:
            raise ValueError("end_byte must be >= start_byte")

    @property
    def size(self) -> int:
        """요청 크기 (바이트)"""
        return self.end_byte - self.start_byte + 1


@dataclass
class RangeResponse:
    """HTTP Range Response (206 Partial Content)"""

    status_code: int
    content_length: int
    content_range: str
    data: bytes

    def __post_init__(self):
        if self.status_code != 206:
            raise ValueError("RangeResponse must have status_code 206")
        if self.content_length < 0:
            raise ValueError("content_length must be non-negative")
        if not self.content_range:
            raise ValueError("content_range is required")


@dataclass
class StreamSource:
    """스트리밍 소스 위치"""

    path: Path
    tier: CacheTier

    def __post_init__(self):
        if not isinstance(self.path, Path):
            self.path = Path(self.path)
        if not isinstance(self.tier, CacheTier):
            raise ValueError("tier must be CacheTier enum")


@dataclass
class StreamSession:
    """스트리밍 세션"""

    user_id: str
    content_id: str
    started_at: datetime

    def __post_init__(self):
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.content_id:
            raise ValueError("content_id is required")
        if not isinstance(self.started_at, datetime):
            raise ValueError("started_at must be datetime")


@dataclass
class BandwidthInfo:
    """대역폭 정보"""

    limit_mbps: float
    current_mbps: float

    def __post_init__(self):
        if self.limit_mbps <= 0:
            raise ValueError("limit_mbps must be positive")
        if self.current_mbps < 0:
            raise ValueError("current_mbps must be non-negative")

    @property
    def is_throttled(self) -> bool:
        """대역폭 제한 초과 여부"""
        return self.current_mbps >= self.limit_mbps


@dataclass
class StreamResult:
    """스트리밍 시작 결과"""

    allowed: bool
    error: Optional[str] = None

    def __post_init__(self):
        if not self.allowed and not self.error:
            raise ValueError("error message required when not allowed")
