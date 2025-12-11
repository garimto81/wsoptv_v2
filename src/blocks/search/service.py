"""
Search Block Service

검색 비즈니스 로직 (인메모리 구현)
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import SearchQuery, SearchResult, SearchItem
from src.orchestration.message_bus import MessageBus, BlockMessage


class SearchService:
    """
    검색 서비스

    TDD 구현:
    - 인메모리 인덱스 (테스트용)
    - 간단한 키워드 매칭
    - Auth 의존성 (토큰 검증)
    """

    def __init__(self, auth_service=None, use_fallback=False):
        """
        초기화

        Args:
            auth_service: 인증 서비스 (Optional)
            use_fallback: Fallback 모드 사용 여부
        """
        # 인메모리 인덱스: {content_id: content_data}
        self._index: Dict[str, Dict[str, Any]] = {}
        self._auth_service = auth_service
        self._use_fallback = use_fallback
        self._bus = MessageBus.get_instance()

        # 이벤트 구독 설정
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        # 실제 구현 시 MessageBus를 통해 이벤트 구독
        # 지금은 구조만 정의
        pass

    async def search(self, query: SearchQuery, token: str = None) -> SearchResult:
        """
        검색 수행

        Args:
            query: 검색 쿼리
            token: 인증 토큰 (Optional)

        Returns:
            검색 결과

        Raises:
            ValueError: 인증 실패 시
        """
        start_time = time.time()

        # 토큰 검증 (auth_service가 있는 경우)
        if self._auth_service and token:
            validation = await self._auth_service.validate_token(token)
            if not validation.valid:
                raise ValueError("Invalid token")

        # Fallback 모드인 경우
        if self._use_fallback:
            from .fallback import FallbackSearch
            fallback = FallbackSearch()
            items = await fallback.search(query.keyword)
            took_ms = (time.time() - start_time) * 1000
            return SearchResult(
                items=items,
                total=len(items),
                took_ms=took_ms,
                page=query.page,
                size=query.size
            )

        # 인메모리 검색
        items = self._search_in_memory(query)

        # 페이지네이션 적용
        total = len(items)
        start_idx = (query.page - 1) * query.size
        end_idx = start_idx + query.size
        paginated_items = items[start_idx:end_idx]

        took_ms = (time.time() - start_time) * 1000

        return SearchResult(
            items=paginated_items,
            total=total,
            took_ms=took_ms,
            page=query.page,
            size=query.size
        )

    def _search_in_memory(self, query: SearchQuery) -> List[SearchItem]:
        """
        인메모리 검색

        Args:
            query: 검색 쿼리

        Returns:
            검색 결과 아이템 리스트
        """
        results = []
        keyword_lower = query.keyword.lower()

        for content_id, content_data in self._index.items():
            # 키워드 매칭
            title = content_data.get("title", "").lower()
            description = content_data.get("description", "").lower()

            if keyword_lower in title or keyword_lower in description:
                # 필터 적용
                if query.filters:
                    match = True
                    for filter_key, filter_value in query.filters.items():
                        if content_data.get(filter_key) != filter_value:
                            match = False
                            break
                    if not match:
                        continue

                # 스코어 계산 (간단한 구현)
                score = 1.0
                if keyword_lower in title:
                    score += 0.5

                # 하이라이트 생성
                highlights = []
                if keyword_lower in title:
                    highlights.append(content_data.get("title", ""))
                if keyword_lower in description:
                    highlights.append(content_data.get("description", ""))

                # SearchItem 생성
                item = SearchItem(
                    id=content_id,
                    title=content_data.get("title", ""),
                    score=score,
                    highlights=highlights,
                    description=content_data.get("description"),
                    category=content_data.get("category"),
                    tags=content_data.get("tags", [])
                )
                results.append(item)

        # 스코어 기준 정렬 (내림차순)
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    async def index_content(self, content_id: str, title: str, **metadata) -> None:
        """
        컨텐츠 인덱싱

        Args:
            content_id: 컨텐츠 ID
            title: 제목
            **metadata: 추가 메타데이터
        """
        self._index[content_id] = {
            "title": title,
            "indexed_at": datetime.now(),
            **metadata
        }

        # 이벤트 발행
        await self._bus.publish(
            "search.content_indexed",
            BlockMessage(
                source_block="search",
                event_type="content_indexed",
                payload={
                    "content_id": content_id,
                    "title": title,
                    "indexed_at": datetime.now().isoformat()
                }
            )
        )

    async def remove_from_index(self, content_id: str) -> None:
        """
        인덱스에서 컨텐츠 제거

        Args:
            content_id: 컨텐츠 ID
        """
        if content_id in self._index:
            del self._index[content_id]

            # 이벤트 발행
            await self._bus.publish(
                "search.content_removed",
                BlockMessage(
                    source_block="search",
                    event_type="content_removed",
                    payload={
                        "content_id": content_id
                    }
                )
            )

    async def reindex_all(self) -> int:
        """
        전체 재인덱싱

        Returns:
            인덱싱된 컨텐츠 수
        """
        # 현재 인덱스 개수 반환 (실제로는 DB에서 다시 읽어와야 함)
        count = len(self._index)

        # 이벤트 발행
        await self._bus.publish(
            "search.reindex_completed",
            BlockMessage(
                source_block="search",
                event_type="reindex_completed",
                payload={
                    "count": count,
                    "completed_at": datetime.now().isoformat()
                }
            )
        )

        return count


# 이벤트 핸들러 (실제 구현 시)
async def on_content_added(msg: BlockMessage, service: SearchService):
    """content.added 이벤트 핸들러"""
    payload = msg.payload
    await service.index_content(
        content_id=payload.get("content_id"),
        title=payload.get("title"),
        description=payload.get("description")
    )


async def on_content_updated(msg: BlockMessage, service: SearchService):
    """content.updated 이벤트 핸들러"""
    payload = msg.payload
    await service.index_content(
        content_id=payload.get("content_id"),
        title=payload.get("title"),
        description=payload.get("description")
    )


async def on_content_deleted(msg: BlockMessage, service: SearchService):
    """content.deleted 이벤트 핸들러"""
    payload = msg.payload
    await service.remove_from_index(payload.get("content_id"))
