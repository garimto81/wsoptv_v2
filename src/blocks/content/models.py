"""
Content Block Models

콘텐츠 관련 데이터 모델
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional


@dataclass
class Content:
    """콘텐츠 전체 정보"""

    id: str
    title: str
    duration_seconds: int
    file_size_bytes: int
    codec: str
    resolution: str
    path: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC)


@dataclass
class ContentMeta:
    """콘텐츠 경량 메타데이터 (API용)"""

    id: str
    title: str
    duration_seconds: int


@dataclass
class Catalog:
    """콘텐츠 카탈로그 (페이지네이션)"""

    items: list[ContentMeta]
    total: int
    page: int
    size: int


@dataclass
class WatchProgress:
    """시청 진행률"""

    user_id: str
    content_id: str
    position_seconds: int
    total_seconds: int
    percentage: float

    def __post_init__(self):
        """백분율 자동 계산"""
        if self.total_seconds > 0:
            self.percentage = (self.position_seconds / self.total_seconds) * 100
        else:
            self.percentage = 0.0
