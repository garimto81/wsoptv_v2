"""
Search Block - L1 (Auth 의존)

검색 블럭: 컨텐츠 검색, 인덱싱, Fallback 지원
"""

from .fallback import CircuitBreaker, FallbackSearch, SearchWithFallback
from .models import SearchItem, SearchQuery, SearchResult
from .router import router
from .service import SearchService

__all__ = [
    "SearchQuery",
    "SearchItem",
    "SearchResult",
    "SearchService",
    "FallbackSearch",
    "CircuitBreaker",
    "SearchWithFallback",
    "router",
]
