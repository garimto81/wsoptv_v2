# Content Block PRD

**Version**: 2.0.0 | **Block ID**: content | **Level**: L1 (Depends on auth, cache)

---

## 1. Overview

Content Block은 WSOPTV 플랫폼의 **콘텐츠 메타데이터 관리**를 담당하는 핵심 블록입니다.

### 책임 범위

| 책임 영역 | 세부 기능 |
|----------|----------|
| **콘텐츠 CRUD** | 영상, 시리즈, 에피소드 메타데이터 관리 |
| **카탈로그** | 장르, 연도, 이벤트별 분류 |
| **홈페이지** | Row 구성 (추천, 인기, 신작, 이어보기) |
| **시청 추적** | 진행률 저장 및 이어보기 |
| **Best Hands** | 핸드별 타임스탬프 관리 |

### 비책임 범위

- 실제 영상 파일 스트리밍 (Stream Block)
- 사용자 프로필 관리 (Auth Block)
- 검색 인덱싱 (Search Block)

---

## 2. API Endpoints

### 홈페이지

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/home` | 홈페이지 Row 데이터 |

### 콘텐츠

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/contents` | 콘텐츠 목록 |
| GET | `/api/contents/{id}` | 콘텐츠 상세 |
| GET | `/api/contents/{id}/hands` | Best Hands 목록 |
| POST | `/api/contents/{id}/progress` | 시청 진행률 저장 |

### 시리즈

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/series` | 시리즈 목록 |
| GET | `/api/series/{id}` | 시리즈 상세 (에피소드 포함) |

---

## 3. Data Models

### Content

```python
class Content(Base):
    id: UUID
    title: str
    description: str
    duration_seconds: int
    file_path: str
    thumbnail_path: str
    series_id: UUID | None
    episode_number: int | None
    event_type: str           # main_event, bracelet, high_roller
    year: int
    brand: str                # wsop_vegas, wsop_europe, wsop_paradise
    quality: str              # sd, hd, 4k
    is_remastered: bool
    created_at: datetime
```

### BestHand

```python
class BestHand(Base):
    id: UUID
    content_id: UUID
    hand_index: int
    start_seconds: int
    end_seconds: int
    category: str             # all_in, bluff, hero_call, bad_beat
    title: str
    players: list[str]
    pot_size: Decimal | None
```

### WatchProgress

```python
class WatchProgress(Base):
    user_id: UUID
    content_id: UUID
    progress_seconds: int
    completed: bool
    updated_at: datetime
```

---

## 4. Home Page Rows

### Row Types

| Type | 설명 | 정렬 |
|------|------|------|
| `continue_watching` | 이어보기 (사용자별) | 최근 시청순 |
| `recently_added` | 최근 추가 | 추가일 역순 |
| `trending` | 인기 콘텐츠 | 7일 조회수순 |
| `main_event` | 메인 이벤트 | 연도 역순 |
| `best_hands` | 베스트 핸드 | 큐레이션 |
| `4k_remastered` | 4K 리마스터 | 연도순 |

---

## 5. Events

### 발행 이벤트

| 채널 | 페이로드 | 설명 |
|------|----------|------|
| `content.created` | `{content_id}` | 콘텐츠 생성됨 |
| `content.updated` | `{content_id}` | 콘텐츠 수정됨 |
| `content.viewed` | `{content_id, user_id}` | 콘텐츠 시청됨 |
| `content.progress_updated` | `{content_id, user_id, progress}` | 진행률 업데이트 |

### 구독 이벤트

| 채널 | 처리 |
|------|------|
| `auth.user_created` | 사용자별 이어보기 초기화 |

---

## 6. Contracts

### 제공 계약

```python
class ContentContract:
    async def get_content(content_id: UUID) -> Content:
        """콘텐츠 조회"""

    async def get_file_path(content_id: UUID) -> str:
        """파일 경로 반환 (Stream Block용)"""

    async def get_best_hands(content_id: UUID) -> list[BestHand]:
        """Best Hands 목록"""

    async def update_progress(user_id: UUID, content_id: UUID, seconds: int) -> None:
        """시청 진행률 업데이트"""
```

---

*Parent: [04-technical.md](../04-technical.md)*
