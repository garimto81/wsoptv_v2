# PRD: Content Block

**Version**: 1.0.0
**Block ID**: content
**전담 에이전트**: content-agent
**Last Updated**: 2025-12-11

---

## 1. Block Overview

### 1.1 책임 범위

Content Block은 WSOPTV 플랫폼의 콘텐츠 관리 핵심 블록입니다.

**핵심 책임**:
- 콘텐츠 메타데이터 CRUD (영상, 시리즈, 라이브)
- 카탈로그 관리 (장르, 연도, 큐레이션)
- 홈페이지 Row 구성 (추천, 인기, 신작, 이어보기)
- 시청 진행률 추적 및 이어보기 기능
- 콘텐츠 검색 및 필터링

**독립성 원칙**:
- Content Block은 **auth**, **cache** 블록에만 의존
- 다른 블록(payment, user, notification)은 Content Block이 제공하는 계약(Contract)을 통해서만 접근
- 콘텐츠 메타데이터는 Content Block이 단일 진실 공급원(Single Source of Truth)

### 1.2 비책임 범위

다음은 **Content Block의 책임이 아닙니다**:
- 실제 영상 파일 스트리밍 (CDN/미디어 서버 담당)
- 사용자 프로필 관리 (user 블록)
- 결제 및 구독 검증 (payment 블록)
- 댓글/좋아요 같은 소셜 기능 (social 블록, 별도 구현 시)

---

## 2. Agent Rules

### 2.1 content-agent 컨텍스트 제한

content-agent는 다음 디렉토리만 접근 가능:

```
D:\AI\claude01\wsoptv_v2\api\app\blocks\content\
D:\AI\claude01\wsoptv_v2\api\app\shared\events.py (이벤트 정의 읽기 전용)
D:\AI\claude01\wsoptv_v2\api\app\shared\contracts.py (계약 정의 읽기 전용)
D:\AI\claude01\wsoptv_v2\docs\blocks\02-content.md (이 문서)
D:\AI\claude01\wsoptv_v2\tests\blocks\content\ (테스트 코드)
```

### 2.2 수정 가능 파일

content-agent가 **직접 수정 가능**한 파일:

```
api/app/blocks/content/
├── __init__.py
├── models.py           # Content, Catalog, WatchProgress 모델
├── routes.py           # Content API 엔드포인트
├── services.py         # 비즈니스 로직
├── contracts.py        # 외부 제공 계약 구현
├── events.py           # 이벤트 발행/구독 핸들러
└── config.py           # Content 블록 설정
```

### 2.3 수정 불가 파일 (읽기 전용)

```
api/app/shared/events.py      # 이벤트 스키마 (arch-agent만 수정)
api/app/shared/contracts.py   # 계약 인터페이스 (arch-agent만 수정)
api/app/blocks/auth/          # auth-agent 전용
api/app/blocks/cache/         # cache-agent 전용
```

### 2.4 블록 간 통신 규칙

| 상황 | 방법 | 예시 |
|------|------|------|
| 다른 블록이 Content 데이터 필요 | `contracts.py`의 함수 호출 | `get_content(content_id)` |
| Content 상태 변경 알림 | `events.py`로 이벤트 발행 | `content_updated` 이벤트 |
| Auth 토큰 검증 필요 | `auth.contracts.validate_token()` 호출 | 보호된 엔드포인트 |
| 캐싱 필요 | `cache.contracts.get/set()` 호출 | 콘텐츠 메타데이터 캐싱 |

**절대 금지**:
- ❌ `from ..user.models import User` (직접 import)
- ❌ `db.query(PaymentSubscription)` (다른 블록 DB 직접 접근)
- ✅ `auth.validate_token(token)` (계약 사용)

---

## 3. API Endpoints

### 3.1 홈페이지 조회

```http
GET /api/home
Authorization: Bearer {token}
```

**Response**:
```json
{
  "rows": [
    {
      "row_id": "continue_watching",
      "type": "continue_watching",
      "title": "이어보기",
      "contents": [
        {
          "content_id": "content_001",
          "title": "Dune: Part Two",
          "type": "movie",
          "thumbnail_url": "https://cdn.wsoptv.com/dune2_thumb.jpg",
          "progress_percent": 42.5,
          "duration_seconds": 7200
        }
      ]
    },
    {
      "row_id": "trending_now",
      "type": "trending",
      "title": "지금 인기",
      "contents": [...]
    }
  ]
}
```

**Row Types**:
- `continue_watching`: 이어보기 (사용자별)
- `trending`: 실시간 인기 (전체 사용자 시청 기반)
- `new_releases`: 신작 (출시일 기준)
- `recommended`: 추천 (사용자 시청 이력 기반, Phase 2)
- `catalog_{catalog_id}`: 특정 카탈로그 (예: `catalog_action`)

### 3.2 콘텐츠 목록 조회

```http
GET /api/contents?type=movie&catalog=action&limit=20&offset=0
```

**Query Parameters**:
- `type` (optional): `movie` | `series` | `live`
- `catalog` (optional): 카탈로그 ID (예: `action`, `2024`)
- `limit` (default: 20, max: 100)
- `offset` (default: 0)

**Response**:
```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "contents": [
    {
      "content_id": "content_001",
      "title": "Dune: Part Two",
      "type": "movie",
      "release_date": "2024-02-28",
      "duration_seconds": 7200,
      "thumbnail_url": "https://cdn.wsoptv.com/dune2_thumb.jpg",
      "catalogs": ["action", "scifi", "2024"]
    }
  ]
}
```

### 3.3 콘텐츠 상세 조회

```http
GET /api/contents/{content_id}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "content_id": "content_001",
  "title": "Dune: Part Two",
  "type": "movie",
  "description": "폴 아트레이데스가 프레멘과 함께...",
  "release_date": "2024-02-28",
  "duration_seconds": 7200,
  "video_url": "https://cdn.wsoptv.com/dune2_master.m3u8",
  "thumbnail_url": "https://cdn.wsoptv.com/dune2_thumb.jpg",
  "poster_url": "https://cdn.wsoptv.com/dune2_poster.jpg",
  "catalogs": [
    {"catalog_id": "action", "name": "액션"},
    {"catalog_id": "scifi", "name": "SF"}
  ],
  "metadata": {
    "director": "드니 빌뇌브",
    "cast": ["티모시 샬라메", "젠데이아"],
    "rating": "15세 관람가"
  },
  "watch_progress": {
    "position_seconds": 3060,
    "progress_percent": 42.5,
    "last_watched_at": "2024-03-15T14:30:00Z"
  }
}
```

### 3.4 카탈로그 목록 조회

```http
GET /api/catalogs
```

**Response**:
```json
{
  "catalogs": [
    {
      "catalog_id": "action",
      "name": "액션",
      "type": "genre",
      "content_count": 45
    },
    {
      "catalog_id": "2024",
      "name": "2024 신작",
      "type": "year",
      "content_count": 23
    }
  ]
}
```

### 3.5 시청 진행률 업데이트

```http
PUT /api/progress/{content_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "position_seconds": 3060,
  "duration_seconds": 7200
}
```

**Response**:
```json
{
  "content_id": "content_001",
  "position_seconds": 3060,
  "progress_percent": 42.5,
  "updated_at": "2024-03-15T14:30:00Z"
}
```

**이벤트 발행**: `progress_updated`

### 3.6 시청 진행률 조회

```http
GET /api/progress/{content_id}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "content_id": "content_001",
  "position_seconds": 3060,
  "progress_percent": 42.5,
  "last_watched_at": "2024-03-15T14:30:00Z"
}
```

---

## 4. Data Models

### 4.1 Content (콘텐츠)

```python
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import ARRAY
import enum

class ContentType(enum.Enum):
    MOVIE = "movie"
    SERIES = "series"
    LIVE = "live"

class Content(Base):
    __tablename__ = "contents"

    content_id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False, index=True)
    type = Column(Enum(ContentType), nullable=False, index=True)
    description = Column(String(2000))
    release_date = Column(DateTime, index=True)
    duration_seconds = Column(Integer)  # 영화/에피소드 길이 (초)

    # 미디어 URL
    video_url = Column(String(500), nullable=False)  # HLS/DASH manifest
    thumbnail_url = Column(String(500))
    poster_url = Column(String(500))

    # 메타데이터 (JSON)
    metadata = Column(JSON)  # {director, cast, rating, etc.}

    # 카탈로그 연결 (Many-to-Many)
    catalog_ids = Column(ARRAY(String(50)), index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 인덱스
    __table_args__ = (
        Index('idx_content_type_release', 'type', 'release_date'),
        Index('idx_content_catalogs', 'catalog_ids', postgresql_using='gin'),
    )
```

### 4.2 Catalog (카탈로그)

```python
class CatalogType(enum.Enum):
    GENRE = "genre"         # 장르 (액션, 드라마)
    YEAR = "year"           # 연도 (2024)
    CURATION = "curation"   # 큐레이션 (감독 특집, 시리즈)

class Catalog(Base):
    __tablename__ = "catalogs"

    catalog_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum(CatalogType), nullable=False, index=True)
    description = Column(String(500))

    # 정렬 순서 (홈페이지 Row 순서)
    sort_order = Column(Integer, default=0, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 4.3 WatchProgress (시청 진행률)

```python
class WatchProgress(Base):
    __tablename__ = "watch_progress"

    user_id = Column(String(50), primary_key=True)
    content_id = Column(String(50), primary_key=True, index=True)

    position_seconds = Column(Integer, default=0)
    duration_seconds = Column(Integer, nullable=False)
    progress_percent = Column(Integer, default=0)  # 0-100

    last_watched_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_last_watched', 'user_id', 'last_watched_at'),
    )
```

### 4.4 RowType (홈페이지 Row 타입)

```python
class RowType(enum.Enum):
    CONTINUE_WATCHING = "continue_watching"
    TRENDING = "trending"
    NEW_RELEASES = "new_releases"
    RECOMMENDED = "recommended"  # Phase 2
    CATALOG = "catalog"          # catalog_{catalog_id}
```

### 4.5 RowData (홈페이지 Row 응답)

```python
from pydantic import BaseModel
from typing import List

class ContentSummary(BaseModel):
    content_id: str
    title: str
    type: str
    thumbnail_url: str
    duration_seconds: int
    progress_percent: Optional[int] = None  # 이어보기 전용

class RowData(BaseModel):
    row_id: str
    type: RowType
    title: str
    contents: List[ContentSummary]
```

---

## 5. Provided Contracts

Content Block이 **다른 블록에 제공**하는 계약:

```python
# api/app/blocks/content/contracts.py

from typing import Optional
from .models import Content, Catalog, WatchProgress

class ContentContracts:
    """다른 블록이 Content 데이터에 접근하기 위한 계약"""

    @staticmethod
    def get_content(content_id: str) -> Optional[Content]:
        """
        콘텐츠 메타데이터 조회

        Usage:
            from app.blocks.content.contracts import ContentContracts
            content = ContentContracts.get_content("content_001")
        """
        return db.query(Content).filter(Content.content_id == content_id).first()

    @staticmethod
    def get_catalog(catalog_id: str) -> Optional[Catalog]:
        """카탈로그 정보 조회"""
        return db.query(Catalog).filter(Catalog.catalog_id == catalog_id).first()

    @staticmethod
    def update_progress(user_id: str, content_id: str, position_seconds: int, duration_seconds: int) -> WatchProgress:
        """
        시청 진행률 업데이트 (외부 블록용)

        Usage:
            from app.blocks.content.contracts import ContentContracts
            progress = ContentContracts.update_progress(
                user_id="user_123",
                content_id="content_001",
                position_seconds=3060,
                duration_seconds=7200
            )
        """
        progress = db.query(WatchProgress).filter(
            WatchProgress.user_id == user_id,
            WatchProgress.content_id == content_id
        ).first()

        if not progress:
            progress = WatchProgress(
                user_id=user_id,
                content_id=content_id,
                duration_seconds=duration_seconds
            )
            db.add(progress)

        progress.position_seconds = position_seconds
        progress.duration_seconds = duration_seconds
        progress.progress_percent = int((position_seconds / duration_seconds) * 100)
        progress.last_watched_at = datetime.utcnow()

        db.commit()

        # 이벤트 발행
        from .events import publish_progress_updated
        publish_progress_updated(user_id, content_id, position_seconds)

        return progress

    @staticmethod
    def get_user_progress(user_id: str, content_id: str) -> Optional[WatchProgress]:
        """사용자별 시청 진행률 조회"""
        return db.query(WatchProgress).filter(
            WatchProgress.user_id == user_id,
            WatchProgress.content_id == content_id
        ).first()

    @staticmethod
    def is_content_exists(content_id: str) -> bool:
        """콘텐츠 존재 여부 확인 (결제 검증 등에서 사용)"""
        return db.query(Content).filter(Content.content_id == content_id).count() > 0
```

---

## 6. Required Contracts

Content Block이 **의존하는** 다른 블록의 계약:

### 6.1 auth.validate_token (사용자 인증)

```python
from app.blocks.auth.contracts import AuthContracts

# routes.py에서 사용
@router.get("/api/home")
async def get_home(token: str = Header(...)):
    user = AuthContracts.validate_token(token)  # user_id 반환
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 이어보기 등 사용자별 데이터 조회
    ...
```

### 6.2 cache.get / cache.set (메타데이터 캐싱)

```python
from app.blocks.cache.contracts import CacheContracts

# services.py에서 사용
def get_content_cached(content_id: str) -> Optional[Content]:
    cache_key = f"content:{content_id}"

    # 캐시 확인
    cached = CacheContracts.get(cache_key)
    if cached:
        return Content(**cached)

    # DB 조회
    content = db.query(Content).filter(Content.content_id == content_id).first()
    if content:
        CacheContracts.set(cache_key, content.dict(), ttl=3600)  # 1시간

    return content
```

---

## 7. Events Published

Content Block이 **발행**하는 이벤트:

```python
# api/app/blocks/content/events.py

from app.shared.events import publish_event

def publish_content_added(content_id: str, content_type: str):
    """
    새 콘텐츠 추가 시 발행

    Subscribers:
        - notification 블록: "신작 알림" 푸시 발송
        - analytics 블록: 콘텐츠 추가 로그
    """
    publish_event("content_added", {
        "content_id": content_id,
        "type": content_type,
        "timestamp": datetime.utcnow().isoformat()
    })

def publish_content_updated(content_id: str, fields: list):
    """
    콘텐츠 메타데이터 수정 시 발행

    Subscribers:
        - cache 블록: 캐시 무효화
    """
    publish_event("content_updated", {
        "content_id": content_id,
        "updated_fields": fields,
        "timestamp": datetime.utcnow().isoformat()
    })

def publish_progress_updated(user_id: str, content_id: str, position_seconds: int):
    """
    시청 진행률 업데이트 시 발행

    Subscribers:
        - analytics 블록: 시청 통계 수집
        - recommendation 블록: 추천 알고리즘 학습 (Phase 2)
    """
    publish_event("progress_updated", {
        "user_id": user_id,
        "content_id": content_id,
        "position_seconds": position_seconds,
        "timestamp": datetime.utcnow().isoformat()
    })
```

---

## 8. Events Subscribed

Content Block이 **구독**하는 이벤트:

```python
# api/app/blocks/content/events.py

from app.shared.events import subscribe_event

@subscribe_event("user_approved")
def on_user_approved(event_data: dict):
    """
    신규 사용자 승인 시 이어보기 초기화

    Publisher: user 블록

    Action:
        - 해당 사용자의 WatchProgress 레코드 없음 → 자동 생성되므로 별도 처리 불필요
        - 웰컴 콘텐츠 Row 구성 (선택 사항)
    """
    user_id = event_data["user_id"]
    print(f"[Content] New user approved: {user_id}")

    # 선택: 웰컴 큐레이션 생성
    # create_welcome_catalog(user_id)

@subscribe_event("cache_invalidated")
def on_cache_invalidated(event_data: dict):
    """
    캐시 무효화 이벤트 처리

    Publisher: cache 블록 (관리자가 수동 캐시 클리어 시)

    Action:
        - 콘텐츠 메타데이터 재조회 대비
    """
    print(f"[Content] Cache invalidated: {event_data.get('keys')}")
```

---

## 9. Directory Structure

```
api/app/blocks/content/
├── __init__.py
├── models.py           # Content, Catalog, WatchProgress 모델
├── routes.py           # FastAPI 엔드포인트
├── services.py         # 비즈니스 로직
│   ├── get_home_rows()
│   ├── get_trending_contents()
│   ├── get_continue_watching()
│   └── update_watch_progress()
├── contracts.py        # 외부 제공 계약
│   └── ContentContracts
├── events.py           # 이벤트 발행/구독
│   ├── publish_content_added()
│   ├── publish_progress_updated()
│   └── on_user_approved()
├── config.py           # Content 블록 설정
│   ├── MAX_CONTINUE_WATCHING = 10
│   ├── TRENDING_PERIOD_HOURS = 24
│   └── CACHE_TTL_SECONDS = 3600
└── dependencies.py     # 의존성 주입 (auth 토큰 검증 등)
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

**파일**: `tests/blocks/content/test_services.py`

```python
import pytest
from app.blocks.content.services import get_continue_watching
from app.blocks.content.models import WatchProgress, Content

def test_get_continue_watching_order():
    """이어보기는 최근 시청 순서로 정렬"""
    user_id = "test_user"

    # Given: 3개 콘텐츠 시청 이력
    create_progress(user_id, "content_001", last_watched="2024-03-15 10:00:00")
    create_progress(user_id, "content_002", last_watched="2024-03-15 14:00:00")
    create_progress(user_id, "content_003", last_watched="2024-03-15 12:00:00")

    # When
    results = get_continue_watching(user_id, limit=10)

    # Then: content_002 (최신) → content_003 → content_001
    assert results[0].content_id == "content_002"
    assert results[1].content_id == "content_003"
    assert results[2].content_id == "content_001"

def test_get_continue_watching_exclude_completed():
    """100% 시청 완료한 콘텐츠는 이어보기에서 제외"""
    user_id = "test_user"

    # Given
    create_progress(user_id, "content_001", progress_percent=42)
    create_progress(user_id, "content_002", progress_percent=100)

    # When
    results = get_continue_watching(user_id, limit=10)

    # Then
    assert len(results) == 1
    assert results[0].content_id == "content_001"
```

### 10.2 Integration Tests

**파일**: `tests/blocks/content/test_routes.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_home_requires_auth():
    """홈 조회는 인증 필수"""
    response = client.get("/api/home")
    assert response.status_code == 401

def test_get_home_success():
    """정상 홈 조회"""
    # Given: 유효한 토큰
    token = create_test_token("test_user")

    # When
    response = client.get("/api/home", headers={"Authorization": f"Bearer {token}"})

    # Then
    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert len(data["rows"]) > 0

def test_update_progress():
    """시청 진행률 업데이트"""
    token = create_test_token("test_user")

    # When
    response = client.put(
        "/api/progress/content_001",
        headers={"Authorization": f"Bearer {token}"},
        json={"position_seconds": 3060, "duration_seconds": 7200}
    )

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["progress_percent"] == 42
```

### 10.3 Contract Tests

**파일**: `tests/blocks/content/test_contracts.py`

```python
import pytest
from app.blocks.content.contracts import ContentContracts

def test_get_content_contract():
    """get_content 계약 검증"""
    # Given
    create_test_content("content_001", title="Test Movie")

    # When
    content = ContentContracts.get_content("content_001")

    # Then
    assert content is not None
    assert content.title == "Test Movie"

def test_update_progress_contract():
    """update_progress 계약 검증"""
    # When
    progress = ContentContracts.update_progress(
        user_id="test_user",
        content_id="content_001",
        position_seconds=3060,
        duration_seconds=7200
    )

    # Then
    assert progress.progress_percent == 42
    assert progress.user_id == "test_user"
```

### 10.4 Event Tests

**파일**: `tests/blocks/content/test_events.py`

```python
import pytest
from app.blocks.content.events import publish_progress_updated
from app.shared.events import get_published_events

def test_progress_updated_event_published():
    """progress_updated 이벤트 발행 검증"""
    # When
    publish_progress_updated("test_user", "content_001", 3060)

    # Then
    events = get_published_events("progress_updated")
    assert len(events) == 1
    assert events[0]["user_id"] == "test_user"
    assert events[0]["content_id"] == "content_001"

def test_on_user_approved_handler():
    """user_approved 이벤트 구독 핸들러 검증"""
    from app.blocks.content.events import on_user_approved

    # When
    on_user_approved({"user_id": "new_user"})

    # Then: 에러 없이 실행 (웰컴 큐레이션 생성 로직 확인)
    # 실제 구현 시 웰컴 카탈로그 생성 여부 검증
```

### 10.5 Performance Tests

**파일**: `tests/blocks/content/test_performance.py`

```python
import pytest
import time
from app.blocks.content.services import get_home_rows

def test_get_home_response_time():
    """홈 조회 응답 시간 < 200ms (캐싱 적용 시)"""
    # Given: 캐시 워밍업
    get_home_rows("test_user")

    # When
    start = time.time()
    get_home_rows("test_user")
    elapsed = (time.time() - start) * 1000

    # Then
    assert elapsed < 200, f"Response time {elapsed}ms exceeds 200ms"
```

### 10.6 테스트 커버리지 목표

| 영역 | 목표 커버리지 |
|------|--------------|
| `services.py` | 90% |
| `contracts.py` | 100% |
| `events.py` | 100% |
| `routes.py` | 85% |
| **전체** | **90%** |

### 10.7 테스트 실행

```powershell
# 전체 테스트
pytest tests/blocks/content/ -v --cov=api/app/blocks/content

# 특정 테스트만
pytest tests/blocks/content/test_contracts.py -v

# 커버리지 리포트
pytest tests/blocks/content/ --cov=api/app/blocks/content --cov-report=html
```

---

## 11. Migration & Deployment

### 11.1 데이터베이스 마이그레이션

```sql
-- Phase 1.0: 기본 테이블
CREATE TABLE contents (
    content_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL,
    description VARCHAR(2000),
    release_date TIMESTAMP,
    duration_seconds INTEGER,
    video_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    poster_url VARCHAR(500),
    metadata JSONB,
    catalog_ids VARCHAR(50)[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_content_type_release ON contents(type, release_date);
CREATE INDEX idx_content_catalogs ON contents USING GIN(catalog_ids);

CREATE TABLE catalogs (
    catalog_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL,
    description VARCHAR(500),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE watch_progress (
    user_id VARCHAR(50),
    content_id VARCHAR(50),
    position_seconds INTEGER DEFAULT 0,
    duration_seconds INTEGER NOT NULL,
    progress_percent INTEGER DEFAULT 0,
    last_watched_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, content_id)
);

CREATE INDEX idx_user_last_watched ON watch_progress(user_id, last_watched_at);
```

### 11.2 초기 데이터 시딩

```python
# scripts/seed_content.py

from app.blocks.content.models import Content, Catalog

# 카탈로그
catalogs = [
    Catalog(catalog_id="action", name="액션", type="genre"),
    Catalog(catalog_id="drama", name="드라마", type="genre"),
    Catalog(catalog_id="2024", name="2024 신작", type="year"),
]

# 샘플 콘텐츠
contents = [
    Content(
        content_id="content_001",
        title="Dune: Part Two",
        type="movie",
        release_date=datetime(2024, 2, 28),
        duration_seconds=7200,
        video_url="https://cdn.wsoptv.com/dune2_master.m3u8",
        thumbnail_url="https://cdn.wsoptv.com/dune2_thumb.jpg",
        catalog_ids=["action", "scifi", "2024"]
    ),
]
```

---

## 12. Monitoring & Alerts

### 12.1 주요 메트릭

| 메트릭 | 임계값 | 알림 |
|--------|--------|------|
| `GET /api/home` 응답 시간 | > 500ms | Slack |
| `PUT /api/progress` 실패율 | > 1% | Slack |
| 이어보기 조회 실패 | > 5% | PagerDuty |
| 콘텐츠 메타데이터 캐시 Hit Rate | < 80% | 로그 |

### 12.2 로그 포맷

```python
import structlog

logger = structlog.get_logger()

# 시청 진행률 업데이트 로그
logger.info(
    "progress_updated",
    user_id=user_id,
    content_id=content_id,
    position_seconds=position_seconds,
    progress_percent=progress_percent
)
```

---

## 13. Future Enhancements (Phase 2+)

| 기능 | Phase | 설명 |
|------|-------|------|
| 추천 알고리즘 | 2.0 | 협업 필터링 기반 개인화 추천 |
| 시리즈 에피소드 관리 | 2.0 | Content 하위에 Episode 모델 추가 |
| 댓글/좋아요 | 3.0 | social 블록과 연동 |
| 라이브 스케줄 | 2.5 | 실시간 방송 편성표 |

---

## 14. References

| 문서 | 경로 |
|------|------|
| 블록 아키텍처 개요 | `D:\AI\claude01\wsoptv_v2\docs\ARCHITECTURE.md` |
| API 명세 | `D:\AI\claude01\wsoptv_v2\docs\api\CONTENT_API.md` |
| 데이터 스키마 | `D:\AI\claude01\wsoptv_v2\docs\schemas\content_schema.sql` |
| Auth 블록 PRD | `D:\AI\claude01\wsoptv_v2\docs\blocks\01-auth.md` |

---

**Last Reviewed**: 2025-12-11
**Approved By**: arch-agent
**Next Review**: Phase 1.5 완료 시
