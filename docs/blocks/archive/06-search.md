# PRD: Search Block

**Version**: 1.0.0
**Date**: 2025-12-11
**Block ID**: search
**전담 에이전트**: search-agent
**Status**: Draft

---

## 1. Block Overview

Search Block은 WSOPTV 플랫폼의 전문 검색 기능을 담당하는 독립 블럭입니다. MeiliSearch를 기반으로 빠르고 정확한 전문 검색을 제공하며, 장애 시 PostgreSQL LIKE 검색으로 자동 폴백합니다.

### 1.1 핵심 책임

| 책임 | 설명 |
|------|------|
| **전문 검색** | 콘텐츠 제목, 설명, 카탈로그명 검색 |
| **자동완성** | 실시간 검색어 제안 |
| **인덱스 관리** | 콘텐츠 추가/수정/삭제 시 인덱스 동기화 |
| **필터링** | 카탈로그별, 길이별 필터 제공 |
| **Fallback** | MeiliSearch 장애 시 DB 검색 전환 |

### 1.2 Non-Goals (이 블럭이 하지 않는 것)

- 콘텐츠 저장/수정 (Content Block 담당)
- 사용자 인증/인가 (Auth Block 담당)
- 검색 결과 캐싱 (Cache Block 담당)

---

## 2. Agent Rules

Search Block 전담 에이전트(`search-agent`)는 다음 규칙을 준수해야 합니다:

### 2.1 컨텍스트 제한

| 허용 | 금지 |
|------|------|
| `api/app/blocks/search/` 수정 | `api/app/blocks/content/` 수정 |
| `tests/blocks/search/` 수정 | `api/app/blocks/auth/` 수정 |
| `docs/blocks/06-search.md` 수정 | `api/app/orchestration/` 수정 (읽기만 허용) |
| 오케스트레이터 계약 **읽기** | 다른 블럭 코드 **직접 호출** |

### 2.2 통신 규칙

```python
# ✅ 올바른 방법: 오케스트레이터 경유
user = await orchestrator.request(
    target="auth",
    action="validate_token",
    payload={"token": token}
)

# ❌ 잘못된 방법: 직접 import
from app.blocks.auth.service import AuthService  # 금지!
```

### 2.3 코드 라인 제한

- 블럭 전체 코드: **500줄 이하**
- 단일 파일: **200줄 이하**
- 함수당: **50줄 이하**

---

## 3. API Endpoints

### 3.1 Search

```yaml
GET /api/search?q={query}&catalog_id={id}&min_duration={seconds}&max_duration={seconds}&page={num}&limit={num}

Parameters:
  - q: string (required, min: 2자)
    검색 쿼리
  - catalog_id: string (optional)
    카탈로그 필터
  - min_duration: int (optional)
    최소 영상 길이 (초)
  - max_duration: int (optional)
    최대 영상 길이 (초)
  - page: int (default: 1)
    페이지 번호
  - limit: int (default: 20, max: 100)
    페이지당 결과 수

Response (200):
  {
    "results": [
      {
        "id": "content-123",
        "title": "WSOP 2024 Main Event Final Table",
        "description": "Historic final table...",
        "catalog_id": "catalog-wsop",
        "catalog_name": "WSOP",
        "duration": 7200,
        "thumbnail_url": "/api/thumbnails/content-123/poster.jpg",
        "added_at": "2024-12-10T10:00:00Z",
        "_score": 0.95  # 검색 관련도 점수
      }
    ],
    "total": 42,
    "page": 1,
    "pages": 3,
    "query": "wsop final",
    "engine": "meilisearch"  # or "postgres"
  }

Errors:
  400: VALIDATION_QUERY_TOO_SHORT - 검색어 최소 2자 이상
  503: SEARCH_SERVICE_UNAVAILABLE - MeiliSearch, PostgreSQL 모두 장애
```

### 3.2 Suggest (자동완성)

```yaml
GET /api/search/suggest?q={query}&limit={num}

Parameters:
  - q: string (required, min: 1자)
    자동완성 쿼리
  - limit: int (default: 10, max: 20)
    제안 개수

Response (200):
  {
    "suggestions": [
      "wsop 2024",
      "wsop main event",
      "wsop final table"
    ],
    "query": "wsop"
  }

Errors:
  400: VALIDATION_QUERY_EMPTY - 검색어 필수
```

### 3.3 Stats (검색 통계, 관리자용)

```yaml
GET /api/search/stats

Auth: Admin only

Response (200):
  {
    "index": {
      "total_documents": 1523,
      "index_size_bytes": 4194304,
      "last_updated": "2025-12-11T10:30:00Z"
    },
    "health": {
      "meilisearch": "healthy",  # healthy, degraded, unavailable
      "fallback_active": false
    },
    "usage": {
      "searches_today": 342,
      "avg_response_ms": 42,
      "cache_hit_rate": 0.65
    }
  }

Errors:
  403: ADMIN_FORBIDDEN - 관리자 권한 필요
```

---

## 4. MeiliSearch Index

### 4.1 Index Configuration

```python
# 인덱스 이름: contents
index_config = {
    "primaryKey": "id",

    # 검색 대상 필드 (우선순위 순)
    "searchableAttributes": [
        "title",           # 최우선
        "description",
        "catalog_name"
    ],

    # 필터 가능 필드
    "filterableAttributes": [
        "catalog_id",
        "duration",
        "added_at"
    ],

    # 정렬 가능 필드
    "sortableAttributes": [
        "added_at",
        "title",
        "duration"
    ],

    # 표시 필드
    "displayedAttributes": [
        "id",
        "title",
        "description",
        "catalog_id",
        "catalog_name",
        "duration",
        "thumbnail_path",
        "added_at"
    ],

    # 랭킹 규칙 (순서대로 적용)
    "rankingRules": [
        "words",        # 검색어 매칭 개수
        "typo",         # 오타 허용
        "proximity",    # 검색어 간 거리
        "attribute",    # searchableAttributes 순서
        "sort",         # 정렬
        "exactness"     # 정확도
    ],

    # 오타 허용 설정
    "typoTolerance": {
        "enabled": True,
        "minWordSizeForTypos": {
            "oneTypo": 4,    # 4자 이상 단어에서 1개 오타 허용
            "twoTypos": 8    # 8자 이상 단어에서 2개 오타 허용
        }
    },

    # 페이지네이션
    "pagination": {
        "maxTotalHits": 1000  # 최대 결과 수
    }
}
```

### 4.2 Document Structure

```python
# MeiliSearch에 저장되는 문서 형식
class SearchDocument(BaseModel):
    id: str                      # 콘텐츠 ID
    title: str                   # 제목
    description: str             # 설명
    catalog_id: str              # 카탈로그 ID
    catalog_name: str            # 카탈로그 이름
    duration: int                # 영상 길이 (초)
    thumbnail_path: str          # 썸네일 경로
    added_at: str                # 추가 시각 (ISO 8601)

# 예시
{
    "id": "content-abc123",
    "title": "WSOP 2024 Main Event Final Table",
    "description": "Unprecedented final table featuring Daniel Negreanu...",
    "catalog_id": "catalog-wsop",
    "catalog_name": "WSOP",
    "duration": 7200,
    "thumbnail_path": "/cache/thumbnails/content-abc123/poster.jpg",
    "added_at": "2024-12-10T10:00:00Z"
}
```

### 4.3 Index Initialization

```python
# app/blocks/search/indexer.py

class MeiliSearchIndexer:
    def __init__(self, client: meilisearch.Client):
        self.client = client
        self.index_name = "contents"

    async def initialize_index(self):
        """인덱스 생성 및 설정"""
        # 인덱스 생성
        self.client.create_index(
            uid=self.index_name,
            options={"primaryKey": "id"}
        )

        index = self.client.index(self.index_name)

        # 설정 업데이트
        index.update_searchable_attributes([
            "title",
            "description",
            "catalog_name"
        ])

        index.update_filterable_attributes([
            "catalog_id",
            "duration",
            "added_at"
        ])

        index.update_sortable_attributes([
            "added_at",
            "title",
            "duration"
        ])

        index.update_ranking_rules([
            "words",
            "typo",
            "proximity",
            "attribute",
            "sort",
            "exactness"
        ])

        index.update_typo_tolerance({
            "enabled": True,
            "minWordSizeForTypos": {
                "oneTypo": 4,
                "twoTypos": 8
            }
        })

        logger.info("MeiliSearch index initialized", index=self.index_name)
```

---

## 5. Provided Contracts

Search Block이 다른 블럭에 제공하는 API:

```python
# app/orchestration/contracts/search.py

class SearchBlockAPI:
    """Search Block 인터페이스 계약"""

    async def search(
        self,
        query: str,
        filters: SearchFilters | None = None,
        page: int = 1,
        limit: int = 20
    ) -> SearchResult:
        """
        콘텐츠 검색

        Args:
            query: 검색 쿼리 (2자 이상)
            filters: 필터 조건 (카탈로그, 길이 등)
            page: 페이지 번호 (1부터 시작)
            limit: 페이지당 결과 수 (최대 100)

        Returns:
            SearchResult: 검색 결과 목록 + 메타데이터

        Raises:
            ValidationError: 잘못된 입력
            SearchServiceError: 검색 서비스 장애
        """
        ...

    async def suggest(
        self,
        query: str,
        limit: int = 10
    ) -> list[str]:
        """
        검색어 자동완성

        Args:
            query: 검색어 일부 (1자 이상)
            limit: 제안 개수 (최대 20)

        Returns:
            list[str]: 추천 검색어 목록
        """
        ...

    async def index_content(
        self,
        content: Content
    ) -> None:
        """
        콘텐츠 인덱싱 (추가/수정)

        Args:
            content: 인덱싱할 콘텐츠

        Note:
            - 이벤트 구독으로 자동 호출됨 (content_added, content_updated)
            - 동기화 실패 시 재시도 큐에 추가
        """
        ...

    async def remove_content(
        self,
        content_id: str
    ) -> None:
        """
        콘텐츠 인덱스 삭제

        Args:
            content_id: 삭제할 콘텐츠 ID

        Note:
            - 이벤트 구독으로 자동 호출됨 (content_deleted)
        """
        ...

    async def reindex_all(self) -> dict:
        """
        전체 재인덱싱 (관리자 전용)

        Returns:
            dict: 재인덱싱 통계 (처리 건수, 소요 시간 등)

        Note:
            - DB에서 모든 콘텐츠를 읽어 인덱스 재구축
            - 수동 실행 또는 스케줄링 (주 1회)
        """
        ...
```

### Data Models

```python
# app/blocks/search/models.py

class SearchFilters(BaseModel):
    """검색 필터"""
    catalog_id: str | None = None
    min_duration: int | None = None  # 초
    max_duration: int | None = None  # 초

class SearchResultItem(BaseModel):
    """검색 결과 항목"""
    id: str
    title: str
    description: str
    catalog_id: str
    catalog_name: str
    duration: int
    thumbnail_url: str
    added_at: datetime
    score: float  # 관련도 점수 (0.0 ~ 1.0)

class SearchResult(BaseModel):
    """검색 결과"""
    results: list[SearchResultItem]
    total: int
    page: int
    pages: int
    query: str
    engine: Literal["meilisearch", "postgres"]  # 사용된 검색 엔진
```

---

## 6. Required Contracts

Search Block이 다른 블럭으로부터 필요로 하는 API:

### 6.1 Auth Block

```python
# 사용자 인증 (검색 통계용)
user = await orchestrator.request(
    target="auth",
    action="validate_token",
    payload={"token": request.headers.get("Authorization")}
)

# 관리자 권한 확인 (통계/재인덱싱 API)
is_admin = await orchestrator.request(
    target="auth",
    action="check_permission",
    payload={
        "user_id": user.id,
        "resource": "search:admin"
    }
)
```

### 6.2 Content Block (재인덱싱 시)

```python
# 전체 콘텐츠 목록 조회 (재인덱싱)
contents = await orchestrator.request(
    target="content",
    action="list_all_contents",
    payload={}
)
```

---

## 7. Events Subscribed

Search Block이 구독하는 이벤트:

### 7.1 content_added

```python
@orchestrator.subscribe("content_added")
async def on_content_added(event: BlockMessage):
    """
    콘텐츠 추가 시 인덱스에 추가

    Event Payload:
        {
            "content_id": "content-abc",
            "title": "WSOP 2024",
            "description": "...",
            "catalog_id": "catalog-wsop",
            "catalog_name": "WSOP",
            "duration": 7200,
            "thumbnail_path": "...",
            "added_at": "2024-12-10T10:00:00Z"
        }
    """
    try:
        await indexer.add_document({
            "id": event.payload["content_id"],
            "title": event.payload["title"],
            "description": event.payload["description"],
            "catalog_id": event.payload["catalog_id"],
            "catalog_name": event.payload["catalog_name"],
            "duration": event.payload["duration"],
            "thumbnail_path": event.payload["thumbnail_path"],
            "added_at": event.payload["added_at"]
        })
        logger.info("Content indexed", content_id=event.payload["content_id"])
    except Exception as e:
        logger.error("Indexing failed", content_id=event.payload["content_id"], error=str(e))
        # 재시도 큐에 추가
        await retry_queue.push(event)
```

### 7.2 content_updated

```python
@orchestrator.subscribe("content_updated")
async def on_content_updated(event: BlockMessage):
    """
    콘텐츠 수정 시 인덱스 업데이트

    Event Payload:
        {
            "content_id": "content-abc",
            "title": "Updated Title",
            "description": "...",
            ...
        }
    """
    try:
        await indexer.update_document(event.payload)
        logger.info("Content reindexed", content_id=event.payload["content_id"])
    except Exception as e:
        logger.error("Reindexing failed", content_id=event.payload["content_id"], error=str(e))
        await retry_queue.push(event)
```

### 7.3 content_deleted

```python
@orchestrator.subscribe("content_deleted")
async def on_content_deleted(event: BlockMessage):
    """
    콘텐츠 삭제 시 인덱스에서 제거

    Event Payload:
        {
            "content_id": "content-abc"
        }
    """
    try:
        await indexer.delete_document(event.payload["content_id"])
        logger.info("Content removed from index", content_id=event.payload["content_id"])
    except Exception as e:
        logger.error("Deletion failed", content_id=event.payload["content_id"], error=str(e))
```

---

## 8. Fallback Strategy

MeiliSearch 장애 시 PostgreSQL LIKE 검색으로 자동 전환합니다.

### 8.1 Circuit Breaker

```python
# app/blocks/search/service.py

class SearchService:
    def __init__(
        self,
        meilisearch: MeiliSearchIndexer,
        fallback: PostgresSearcher,
        circuit_breaker: CircuitBreaker
    ):
        self.meilisearch = meilisearch
        self.fallback = fallback
        self.circuit = circuit_breaker

    async def search(self, query: str, filters: SearchFilters | None = None) -> SearchResult:
        """검색 (자동 폴백)"""

        # Circuit Breaker 확인
        if self.circuit.is_open():
            logger.warning("MeiliSearch circuit open, using fallback")
            return await self.fallback.search(query, filters)

        try:
            # Primary: MeiliSearch
            result = await self.meilisearch.search(query, filters)
            self.circuit.on_success()
            result.engine = "meilisearch"
            return result

        except MeiliSearchError as e:
            logger.error("MeiliSearch failed", error=str(e))
            self.circuit.on_failure()

            # Fallback: PostgreSQL
            logger.info("Falling back to PostgreSQL search")
            result = await self.fallback.search(query, filters)
            result.engine = "postgres"
            return result
```

### 8.2 PostgreSQL Fallback Searcher

```python
# app/blocks/search/fallback.py

class PostgresSearcher:
    """PostgreSQL LIKE 검색 (Fallback)"""

    async def search(
        self,
        query: str,
        filters: SearchFilters | None = None,
        page: int = 1,
        limit: int = 20
    ) -> SearchResult:
        """
        PostgreSQL 전문 검색

        - 성능: MeiliSearch보다 느림 (100ms vs 10ms)
        - 기능: 오타 허용 없음, 관련도 점수 부정확
        - 장점: 외부 의존성 없음, DB 직접 조회로 일관성 보장
        """
        # LIKE 검색 쿼리
        stmt = (
            select(Content, Catalog)
            .join(Catalog)
            .where(
                or_(
                    Content.title.ilike(f"%{query}%"),
                    Content.description.ilike(f"%{query}%"),
                    Catalog.name.ilike(f"%{query}%")
                )
            )
        )

        # 필터 적용
        if filters:
            if filters.catalog_id:
                stmt = stmt.where(Content.catalog_id == filters.catalog_id)
            if filters.min_duration:
                stmt = stmt.where(Content.duration >= filters.min_duration)
            if filters.max_duration:
                stmt = stmt.where(Content.duration <= filters.max_duration)

        # 페이지네이션
        total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        # 실행
        rows = await db.execute(stmt)
        results = []

        for content, catalog in rows:
            results.append(SearchResultItem(
                id=content.id,
                title=content.title,
                description=content.description,
                catalog_id=catalog.id,
                catalog_name=catalog.name,
                duration=content.duration,
                thumbnail_url=f"/api/thumbnails/{content.id}/poster.jpg",
                added_at=content.added_at,
                score=self._calculate_score(content, query)  # 간단한 점수 계산
            ))

        return SearchResult(
            results=results,
            total=total,
            page=page,
            pages=(total + limit - 1) // limit,
            query=query,
            engine="postgres"
        )

    def _calculate_score(self, content: Content, query: str) -> float:
        """간단한 관련도 점수 (0.0 ~ 1.0)"""
        query_lower = query.lower()
        title_lower = content.title.lower()

        # 제목에 완전 일치
        if query_lower == title_lower:
            return 1.0

        # 제목 시작 일치
        if title_lower.startswith(query_lower):
            return 0.9

        # 제목 포함
        if query_lower in title_lower:
            return 0.7

        # 설명 포함
        if query_lower in content.description.lower():
            return 0.5

        return 0.3
```

### 8.3 Circuit Breaker Configuration

```python
# app/blocks/search/circuit.py

class SearchCircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,    # 5회 연속 실패 시 Open
        recovery_timeout: int = 60,    # 60초 후 Half-Open
        success_threshold: int = 2     # Half-Open에서 2회 성공 시 Close
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def is_open(self) -> bool:
        """Circuit이 열려있는지 확인"""
        if self.state == CircuitState.CLOSED:
            return False

        if self.state == CircuitState.OPEN:
            # 복구 타임아웃 경과 시 Half-Open
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit half-open, trying recovery")
                return False
            return True

        # HALF_OPEN: 일부 트래픽 허용
        return False

    def on_success(self):
        """성공 시 호출"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit closed, MeiliSearch recovered")

        if self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def on_failure(self):
        """실패 시 호출"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning("Circuit opened, MeiliSearch unavailable")

class CircuitState(str, Enum):
    CLOSED = "closed"      # 정상
    OPEN = "open"          # 장애 (Fallback 사용)
    HALF_OPEN = "half_open"  # 복구 시도 중
```

### 8.4 Performance Comparison

| 검색 엔진 | 평균 응답 시간 | 오타 허용 | 관련도 정확도 | 의존성 |
|----------|---------------|----------|--------------|--------|
| **MeiliSearch** | ~10ms | O | 높음 | 외부 서비스 |
| **PostgreSQL** | ~100ms | X | 중간 | DB 직접 |

---

## 9. Directory Structure

```
api/app/blocks/search/
├── __init__.py
├── router.py              # FastAPI 라우터 (API 엔드포인트)
├── service.py             # 검색 서비스 (비즈니스 로직)
├── indexer.py             # MeiliSearch 인덱서
├── fallback.py            # PostgreSQL Fallback 검색
├── circuit.py             # Circuit Breaker
├── models.py              # 데이터 모델
└── dependencies.py        # DI 의존성

tests/blocks/search/
├── __init__.py
├── conftest.py            # pytest fixtures
├── test_search_api.py     # API 테스트
├── test_search_service.py # 서비스 테스트
├── test_indexer.py        # 인덱서 테스트
├── test_fallback.py       # Fallback 테스트
└── test_circuit.py        # Circuit Breaker 테스트

docs/blocks/
└── 06-search.md           # 이 문서
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

```python
# tests/blocks/search/test_search_service.py

class TestSearchService:
    """검색 서비스 단위 테스트"""

    @pytest.fixture
    def mock_meilisearch(self):
        """MeiliSearch Mock"""
        mock = AsyncMock()
        mock.search.return_value = SearchResult(
            results=[
                SearchResultItem(
                    id="content-1",
                    title="WSOP 2024",
                    score=0.95,
                    ...
                )
            ],
            total=1,
            page=1,
            pages=1,
            query="wsop",
            engine="meilisearch"
        )
        return mock

    @pytest.fixture
    def mock_fallback(self):
        """PostgreSQL Fallback Mock"""
        mock = AsyncMock()
        mock.search.return_value = SearchResult(
            results=[],
            total=0,
            page=1,
            pages=0,
            query="wsop",
            engine="postgres"
        )
        return mock

    async def test_search_uses_meilisearch_when_healthy(
        self,
        mock_meilisearch,
        mock_fallback
    ):
        """정상 시 MeiliSearch 사용"""
        circuit = SearchCircuitBreaker()
        service = SearchService(mock_meilisearch, mock_fallback, circuit)

        result = await service.search("wsop")

        assert result.engine == "meilisearch"
        assert result.total == 1
        mock_meilisearch.search.assert_called_once_with("wsop", None)
        mock_fallback.search.assert_not_called()

    async def test_search_uses_fallback_when_meilisearch_fails(
        self,
        mock_meilisearch,
        mock_fallback
    ):
        """MeiliSearch 실패 시 Fallback 사용"""
        mock_meilisearch.search.side_effect = MeiliSearchError("Connection failed")

        circuit = SearchCircuitBreaker()
        service = SearchService(mock_meilisearch, mock_fallback, circuit)

        result = await service.search("wsop")

        assert result.engine == "postgres"
        mock_meilisearch.search.assert_called_once()
        mock_fallback.search.assert_called_once()

    async def test_circuit_opens_after_threshold_failures(
        self,
        mock_meilisearch,
        mock_fallback
    ):
        """5회 실패 시 Circuit Open"""
        mock_meilisearch.search.side_effect = MeiliSearchError("Fail")

        circuit = SearchCircuitBreaker(failure_threshold=5)
        service = SearchService(mock_meilisearch, mock_fallback, circuit)

        # 5회 호출
        for _ in range(5):
            await service.search("test")

        assert circuit.is_open() == True

        # 6번째 호출은 MeiliSearch 시도 없이 바로 Fallback
        await service.search("test")
        assert mock_meilisearch.search.call_count == 5  # 더 이상 증가 안함
```

### 10.2 Integration Tests

```python
# tests/blocks/search/test_search_api.py

class TestSearchAPI:
    """검색 API 통합 테스트"""

    @pytest.fixture
    async def setup_test_data(self, db):
        """테스트 데이터 생성"""
        catalog = Catalog(id="cat-1", name="WSOP")
        content1 = Content(
            id="content-1",
            catalog_id="cat-1",
            title="WSOP 2024 Main Event",
            description="Final table action",
            duration=7200
        )
        content2 = Content(
            id="content-2",
            catalog_id="cat-1",
            title="WSOP 2024 High Roller",
            description="Big blinds and big plays",
            duration=5400
        )

        db.add_all([catalog, content1, content2])
        await db.commit()

        # MeiliSearch 인덱싱
        await indexer.add_document({
            "id": "content-1",
            "title": "WSOP 2024 Main Event",
            ...
        })
        await indexer.add_document({
            "id": "content-2",
            "title": "WSOP 2024 High Roller",
            ...
        })

    async def test_search_returns_results(self, client, setup_test_data):
        """검색 결과 반환"""
        response = await client.get("/api/search?q=wsop")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["title"] == "WSOP 2024 Main Event"
        assert data["engine"] == "meilisearch"

    async def test_search_with_catalog_filter(self, client, setup_test_data):
        """카탈로그 필터 적용"""
        response = await client.get("/api/search?q=wsop&catalog_id=cat-1")

        assert response.status_code == 200
        data = response.json()
        assert all(r["catalog_id"] == "cat-1" for r in data["results"])

    async def test_search_with_duration_filter(self, client, setup_test_data):
        """영상 길이 필터 적용"""
        response = await client.get(
            "/api/search?q=wsop&min_duration=6000&max_duration=8000"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1  # 7200초짜리만
        assert data["results"][0]["id"] == "content-1"

    async def test_search_validates_query_length(self, client):
        """검색어 길이 검증"""
        response = await client.get("/api/search?q=a")

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_QUERY_TOO_SHORT"

    async def test_suggest_returns_completions(self, client, setup_test_data):
        """자동완성 제안"""
        response = await client.get("/api/search/suggest?q=wso")

        assert response.status_code == 200
        data = response.json()

        assert "wsop" in [s.lower() for s in data["suggestions"]]
```

### 10.3 E2E Tests (Playwright)

```typescript
// web/tests/e2e/search.spec.ts

test.describe('Search', () => {
  test('검색어 입력 시 실시간 제안', async ({ page }) => {
    await page.goto('/');

    // 검색창 포커스
    await page.click('[data-testid="search-input"]');

    // "wso" 입력
    await page.fill('[data-testid="search-input"]', 'wso');

    // 자동완성 드롭다운 표시
    await expect(page.locator('[data-testid="suggestions"]')).toBeVisible();

    // "wsop 2024" 제안 확인
    await expect(
      page.locator('[data-testid="suggestion-item"]').first()
    ).toContainText('wsop');
  });

  test('검색 결과 페이지 이동 및 필터', async ({ page }) => {
    await page.goto('/search?q=wsop');

    // 결과 로딩 대기
    await page.waitForSelector('[data-testid="search-results"]');

    // 결과 개수 확인
    const results = page.locator('[data-testid="content-card"]');
    await expect(results).toHaveCount(20);  // 기본 limit

    // 카탈로그 필터 적용
    await page.click('[data-testid="filter-catalog"]');
    await page.click('[data-testid="catalog-wsop"]');

    // URL 업데이트 확인
    await expect(page).toHaveURL(/catalog_id=catalog-wsop/);

    // 필터링된 결과 확인
    const filteredResults = await results.all();
    for (const result of filteredResults) {
      await expect(result.locator('.catalog-badge')).toContainText('WSOP');
    }
  });

  test('검색 결과 없음 처리', async ({ page }) => {
    await page.goto('/search?q=nonexistentquery12345');

    // 결과 없음 메시지
    await expect(
      page.locator('[data-testid="no-results"]')
    ).toContainText('검색 결과가 없습니다');

    // 추천 검색어 표시
    await expect(
      page.locator('[data-testid="suggested-queries"]')
    ).toBeVisible();
  });
});
```

### 10.4 Performance Tests

```python
# tests/blocks/search/test_search_performance.py

import pytest
import time
from statistics import mean, stdev

class TestSearchPerformance:
    """검색 성능 테스트"""

    @pytest.mark.benchmark
    async def test_meilisearch_latency(self, search_service):
        """MeiliSearch 응답 시간 < 50ms"""
        latencies = []

        for _ in range(100):
            start = time.perf_counter()
            await search_service.meilisearch.search("wsop")
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        avg_latency = mean(latencies)
        p99_latency = sorted(latencies)[98]

        assert avg_latency < 50, f"평균 {avg_latency:.2f}ms > 50ms"
        assert p99_latency < 100, f"P99 {p99_latency:.2f}ms > 100ms"

    @pytest.mark.benchmark
    async def test_fallback_latency(self, search_service):
        """PostgreSQL Fallback 응답 시간 < 200ms"""
        latencies = []

        for _ in range(50):
            start = time.perf_counter()
            await search_service.fallback.search("wsop")
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        avg_latency = mean(latencies)

        assert avg_latency < 200, f"평균 {avg_latency:.2f}ms > 200ms"

    @pytest.mark.load
    async def test_concurrent_searches(self, search_service):
        """동시 검색 100개 처리"""
        import asyncio

        async def search_task():
            return await search_service.search("wsop")

        start = time.perf_counter()
        results = await asyncio.gather(*[search_task() for _ in range(100)])
        duration = time.perf_counter() - start

        assert len(results) == 100
        assert all(r.total > 0 for r in results)
        assert duration < 5.0, f"100개 검색 {duration:.2f}초 > 5초"
```

### 10.5 Test Coverage Target

| 범위 | 목표 |
|------|------|
| **전체** | 85%+ |
| **router.py** | 90%+ (모든 엔드포인트) |
| **service.py** | 95%+ (비즈니스 로직) |
| **fallback.py** | 90%+ (Fallback 경로) |
| **circuit.py** | 100% (Circuit Breaker 로직) |

---

## 11. Deployment & Operations

### 11.1 MeiliSearch 설치 (Windows)

```powershell
# MeiliSearch 다운로드 및 설치
# scripts/setup-meilisearch.ps1

$version = "v1.11.0"
$url = "https://github.com/meilisearch/meilisearch/releases/download/$version/meilisearch-windows-amd64.exe"
$installDir = "D:\WSOPTV\meilisearch"

# 디렉토리 생성
New-Item -ItemType Directory -Path $installDir -Force

# 다운로드
Invoke-WebRequest -Uri $url -OutFile "$installDir\meilisearch.exe"

# 환경 변수 설정
[Environment]::SetEnvironmentVariable(
    "MEILI_MASTER_KEY",
    "your_master_key_here",
    "Machine"
)

Write-Host "MeiliSearch installed at $installDir" -ForegroundColor Green
```

### 11.2 MeiliSearch 서비스 등록

```powershell
# NSSM (Non-Sucking Service Manager) 사용
# scripts/register-meilisearch-service.ps1

nssm install MeiliSearch "D:\WSOPTV\meilisearch\meilisearch.exe"
nssm set MeiliSearch AppParameters "--env production --db-path D:\WSOPTV\meilisearch\data --http-addr 0.0.0.0:7700"
nssm set MeiliSearch AppDirectory "D:\WSOPTV\meilisearch"
nssm set MeiliSearch DisplayName "MeiliSearch"
nssm set MeiliSearch Description "WSOPTV Search Engine"
nssm set MeiliSearch Start SERVICE_AUTO_START

# 서비스 시작
nssm start MeiliSearch

Write-Host "MeiliSearch registered as Windows service" -ForegroundColor Green
```

### 11.3 Index 초기화 스크립트

```python
# scripts/init_search_index.py

import asyncio
import meilisearch
from app.core.config import settings
from app.blocks.search.indexer import MeiliSearchIndexer
from app.db.session import async_session
from sqlalchemy import select
from app.models import Content, Catalog

async def main():
    # MeiliSearch 클라이언트
    client = meilisearch.Client(
        settings.MEILI_HOST,
        settings.MEILI_MASTER_KEY
    )

    indexer = MeiliSearchIndexer(client)

    # 인덱스 초기화
    print("Initializing MeiliSearch index...")
    await indexer.initialize_index()

    # DB에서 모든 콘텐츠 로드
    print("Loading contents from database...")
    async with async_session() as db:
        stmt = select(Content, Catalog).join(Catalog)
        rows = await db.execute(stmt)

        documents = []
        for content, catalog in rows:
            documents.append({
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "catalog_id": catalog.id,
                "catalog_name": catalog.name,
                "duration": content.duration,
                "thumbnail_path": content.thumbnail_path,
                "added_at": content.added_at.isoformat()
            })

        # 인덱싱
        print(f"Indexing {len(documents)} documents...")
        await indexer.add_documents(documents)

        print(f"✅ Indexed {len(documents)} contents successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

### 11.4 Monitoring

```python
# app/blocks/search/monitoring.py

class SearchMonitoring:
    """검색 메트릭 수집"""

    async def collect_metrics(self) -> dict:
        # MeiliSearch 통계
        index = self.client.index("contents")
        stats = index.get_stats()

        # Circuit Breaker 상태
        circuit_state = self.circuit.state.value

        # Redis에서 검색 횟수 조회
        searches_today = await redis.get("metrics:searches:today") or 0

        return {
            "index": {
                "total_documents": stats["numberOfDocuments"],
                "index_size_bytes": stats["indexSize"],
                "is_indexing": stats["isIndexing"]
            },
            "health": {
                "meilisearch": "healthy" if not self.circuit.is_open() else "unavailable",
                "fallback_active": self.circuit.is_open()
            },
            "usage": {
                "searches_today": int(searches_today),
                "circuit_state": circuit_state
            }
        }
```

---

## 12. Success Metrics

| Metric | Target | 측정 방법 |
|--------|--------|----------|
| **검색 응답 시간 (P99)** | < 50ms | MeiliSearch 로그 |
| **Fallback 응답 시간 (P99)** | < 200ms | PostgreSQL 쿼리 로그 |
| **검색 정확도** | > 90% | 수동 테스트 (상위 10개 결과 관련성) |
| **인덱스 동기화율** | > 99.9% | 이벤트 처리 성공률 |
| **Circuit Breaker 복구 시간** | < 60초 | Circuit 상태 전환 로그 |
| **Uptime (MeiliSearch)** | > 99% | 헬스체크 |
| **Uptime (Search API)** | > 99.9% | Fallback 포함 |

---

## 13. Future Enhancements

| 기능 | 우선순위 | 설명 |
|------|---------|------|
| **검색 추천** | P2 | "다른 사람들이 검색한 항목" |
| **검색 히스토리** | P2 | 사용자별 최근 검색어 저장 |
| **고급 필터** | P2 | 날짜 범위, 플레이어명 등 |
| **패싯 검색** | P2 | 카탈로그별 결과 개수 표시 |
| **검색 분석** | P3 | 인기 검색어, 검색 실패율 분석 |
| **동의어 지원** | P3 | "WSOP" ↔ "World Series of Poker" |

---

## Appendix

### A. MeiliSearch Health Check

```python
async def check_meilisearch_health() -> bool:
    """MeiliSearch 헬스체크"""
    try:
        resp = await httpx.get(f"{settings.MEILI_HOST}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False
```

### B. Index Rebuild Script

```python
# scripts/rebuild_search_index.py

async def rebuild_index():
    """인덱스 재구축 (데이터 손상 시)"""
    # 기존 인덱스 삭제
    client.delete_index("contents")

    # 새 인덱스 생성
    await indexer.initialize_index()

    # 전체 재인덱싱
    from scripts.init_search_index import main
    await main()
```

### C. Search Query Examples

```python
# 기본 검색
GET /api/search?q=wsop

# 카탈로그 필터
GET /api/search?q=final table&catalog_id=catalog-wsop

# 영상 길이 필터 (1-2시간)
GET /api/search?q=tournament&min_duration=3600&max_duration=7200

# 페이지네이션
GET /api/search?q=poker&page=2&limit=50

# 자동완성
GET /api/search/suggest?q=wso&limit=5
```

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-11 | Claude Code | Initial draft |
