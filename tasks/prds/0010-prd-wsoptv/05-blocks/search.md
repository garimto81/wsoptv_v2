# Search Block PRD

**Version**: 2.0.0 | **Block ID**: search | **Level**: L1 (Depends on auth, content)

---

## 1. Overview

Search Block은 **MeiliSearch** 기반의 전문 검색 기능을 제공합니다.

### 책임 범위

| 책임 영역 | 세부 기능 |
|----------|----------|
| **인덱스 관리** | 콘텐츠/플레이어 인덱스 생성 및 관리 |
| **검색 실행** | 전문 검색, 필터링, 정렬 |
| **자동완성** | 타이핑 중 실시간 검색 제안 |
| **동기화** | 콘텐츠 변경 시 인덱스 업데이트 |

---

## 2. API Endpoints

### 검색

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/search` | 전문 검색 |
| GET | `/api/search/suggest` | 자동완성 제안 |

### Query Parameters

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `q` | string | 검색어 |
| `type` | string | 콘텐츠 유형 (episode, series) |
| `year` | int | 연도 필터 |
| `event` | string | 이벤트 유형 필터 |
| `player` | string | 플레이어 필터 |
| `limit` | int | 결과 수 (기본: 20) |
| `offset` | int | 시작 위치 |

---

## 3. MeiliSearch Configuration

### 인덱스 구조

```json
// contents 인덱스
{
  "primaryKey": "id",
  "searchableAttributes": [
    "title",
    "description",
    "players",
    "event_type"
  ],
  "filterableAttributes": [
    "year",
    "brand",
    "event_type",
    "quality"
  ],
  "sortableAttributes": [
    "year",
    "created_at",
    "view_count"
  ]
}
```

### 검색 가중치

| 필드 | 가중치 | 설명 |
|------|--------|------|
| title | 최우선 | 제목 일치 |
| players | 높음 | 플레이어 이름 |
| description | 보통 | 설명 텍스트 |
| event_type | 낮음 | 이벤트 유형 |

---

## 4. Search Features

### 기본 검색

```http
GET /api/search?q=phil+ivey&limit=20

Response:
{
  "hits": [
    {
      "id": "content-123",
      "title": "WSOP 2024 Main Event Day 5",
      "players": ["Phil Ivey", "Daniel Negreanu"],
      "year": 2024,
      "highlight": {
        "players": ["<em>Phil Ivey</em>", "Daniel Negreanu"]
      }
    }
  ],
  "total": 45,
  "processingTimeMs": 12
}
```

### 필터 검색

```http
GET /api/search?q=main+event&year=2024&event=main_event
```

### 자동완성

```http
GET /api/search/suggest?q=phi

Response:
{
  "suggestions": [
    "phil ivey",
    "phil hellmuth",
    "phillips"
  ]
}
```

---

## 5. Index Synchronization

### 동기화 트리거

| 이벤트 | 처리 |
|--------|------|
| `content.created` | 인덱스에 추가 |
| `content.updated` | 인덱스 업데이트 |
| `content.deleted` | 인덱스에서 삭제 |

### 배치 동기화

```python
# 매일 새벽 3시 전체 동기화
@scheduler.cron("0 3 * * *")
async def full_reindex():
    contents = await content_service.get_all()
    await meilisearch.index("contents").update_documents(contents)
```

---

## 6. Contracts

### 의존 계약 (호출)

```python
# Auth Block
auth.validate_token(token) -> User

# Content Block
content.get_all_contents() -> list[Content]
```

### 제공 계약

```python
class SearchContract:
    async def search(query: str, filters: dict) -> SearchResult:
        """전문 검색 실행"""

    async def suggest(query: str) -> list[str]:
        """자동완성 제안"""

    async def reindex_content(content_id: str) -> None:
        """단일 콘텐츠 재인덱싱"""
```

---

## 7. Events

### 구독 이벤트

| 채널 | 처리 |
|------|------|
| `content.created` | 인덱스 추가 |
| `content.updated` | 인덱스 업데이트 |
| `content.deleted` | 인덱스 삭제 |

---

*Parent: [04-technical.md](../04-technical.md)*
