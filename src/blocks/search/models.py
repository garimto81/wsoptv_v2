"""
Search Block Models

검색 쿼리, 결과, 아이템 모델
"""

from dataclasses import dataclass, field


@dataclass
class SearchQuery:
    """검색 쿼리 모델"""
    keyword: str
    filters: dict[str, str] = field(default_factory=dict)
    page: int = 1
    size: int = 10

    def __post_init__(self):
        """유효성 검증"""
        if self.page < 1:
            self.page = 1
        if self.size < 1:
            self.size = 10
        if self.size > 100:
            self.size = 100


@dataclass
class SearchItem:
    """검색 결과 아이템"""
    id: str
    title: str
    score: float
    highlights: list[str] = field(default_factory=list)

    # 추가 메타데이터
    description: str | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """검색 결과"""
    items: list[SearchItem]
    total: int
    took_ms: float

    # 페이지네이션 정보
    page: int = 1
    size: int = 10

    @property
    def total_pages(self) -> int:
        """총 페이지 수"""
        if self.size == 0:
            return 0
        return (self.total + self.size - 1) // self.size

    @property
    def has_next(self) -> bool:
        """다음 페이지 존재 여부"""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """이전 페이지 존재 여부"""
        return self.page > 1
