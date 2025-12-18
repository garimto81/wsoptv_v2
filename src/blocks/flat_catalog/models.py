"""
Block F: Flat Catalog - 데이터 모델

단일 계층 카탈로그 아이템을 표현하는 데이터클래스.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any
from uuid import UUID, uuid4


@dataclass
class CatalogItem:
    """
    단일 계층 카탈로그 아이템

    NAS 파일을 직접 카탈로그 아이템으로 매핑.
    기존 4단계 계층(Project → Season → Event → Episode)을 대체.
    """

    id: UUID = field(default_factory=uuid4)
    nas_file_id: UUID | None = None  # NASFile FK

    # 표시 정보
    display_title: str = ""
    short_title: str = ""
    thumbnail_url: str | None = None

    # 분류
    project_code: str = "OTHER"  # WSOP, HCL, GGMILLIONS, etc.
    year: int | None = None
    category_tags: list[str] = field(default_factory=list)

    # 파일 정보
    file_path: str = ""
    file_name: str = ""
    file_size_bytes: int = 0
    file_extension: str = ""

    # 미디어 메타데이터
    duration_seconds: int | None = None
    quality: str | None = None  # HD, 4K, etc.
    codec: str | None = None

    # 상태
    is_visible: bool = True
    confidence: float = 0.0  # 제목 생성 신뢰도

    # 타임스탬프
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": str(self.id),
            "nas_file_id": str(self.nas_file_id) if self.nas_file_id else None,
            "display_title": self.display_title,
            "short_title": self.short_title,
            "thumbnail_url": self.thumbnail_url,
            "project_code": self.project_code,
            "year": self.year,
            "category_tags": self.category_tags,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size_bytes": self.file_size_bytes,
            "file_extension": self.file_extension,
            "duration_seconds": self.duration_seconds,
            "quality": self.quality,
            "codec": self.codec,
            "is_visible": self.is_visible,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CatalogItem:
        """딕셔너리에서 생성"""
        item = cls()
        item.id = UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id", uuid4())
        item.nas_file_id = UUID(data["nas_file_id"]) if data.get("nas_file_id") else None
        item.display_title = data.get("display_title", "")
        item.short_title = data.get("short_title", "")
        item.thumbnail_url = data.get("thumbnail_url")
        item.project_code = data.get("project_code", "OTHER")
        item.year = data.get("year")
        item.category_tags = data.get("category_tags", [])
        item.file_path = data.get("file_path", "")
        item.file_name = data.get("file_name", "")
        item.file_size_bytes = data.get("file_size_bytes", 0)
        item.file_extension = data.get("file_extension", "")
        item.duration_seconds = data.get("duration_seconds")
        item.quality = data.get("quality")
        item.codec = data.get("codec")
        item.is_visible = data.get("is_visible", True)
        item.confidence = data.get("confidence", 0.0)

        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                item.created_at = datetime.fromisoformat(data["created_at"])
            else:
                item.created_at = data["created_at"]

        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                item.updated_at = datetime.fromisoformat(data["updated_at"])
            else:
                item.updated_at = data["updated_at"]

        return item

    def update_timestamp(self) -> None:
        """업데이트 타임스탬프 갱신"""
        self.updated_at = datetime.now(UTC)

    def format_file_size(self) -> str:
        """파일 크기 포맷팅 (예: 1.5 GB)"""
        size = self.file_size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


@dataclass
class CatalogSyncResult:
    """카탈로그 동기화 결과"""

    created: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    error_messages: list[str] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        """총 처리 개수"""
        return self.created + self.updated + self.deleted + self.skipped

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "created": self.created,
            "updated": self.updated,
            "deleted": self.deleted,
            "skipped": self.skipped,
            "errors": self.errors,
            "total_processed": self.total_processed,
            "duration_seconds": self.duration_seconds,
            "error_messages": self.error_messages[:10],  # 최대 10개만
        }


@dataclass
class NASFileInfo:
    """NAS 파일 정보 (Block A에서 전달받는 형태)"""

    id: UUID
    file_path: str
    file_name: str
    file_size_bytes: int
    file_extension: str
    file_category: str  # VIDEO, METADATA, etc.
    is_hidden_file: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NASFileInfo:
        """딕셔너리에서 생성"""
        return cls(
            id=UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id"),
            file_path=data.get("file_path", ""),
            file_name=data.get("file_name", ""),
            file_size_bytes=data.get("file_size_bytes", 0),
            file_extension=data.get("file_extension", ""),
            file_category=data.get("file_category", "OTHER"),
            is_hidden_file=data.get("is_hidden_file", False),
        )
