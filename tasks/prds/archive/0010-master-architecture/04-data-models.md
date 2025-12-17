# 04. Data Models

*← [03-api-spec.md](./03-api-spec.md) | [05-user-interface.md](./05-user-interface.md) →*

---

## 1. Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ SESSION : has
    USER ||--o{ WATCH_PROGRESS : tracks
    USER ||--o{ STREAM_SESSION : creates

    CATALOG_ITEM ||--o{ WATCH_PROGRESS : tracked_by
    CATALOG_ITEM ||--o{ STREAM_SESSION : streamed_as
    CATALOG_ITEM ||--|| NAS_FILE : maps_to

    USER {
        uuid id PK
        string email UK
        string password_hash
        enum status "pending|active|suspended"
        bool is_admin
        datetime created_at
        datetime updated_at
        datetime last_login
    }

    SESSION {
        uuid id PK
        uuid user_id FK
        string token UK
        datetime expires_at
        datetime created_at
    }

    CATALOG_ITEM {
        uuid id PK
        uuid nas_file_id FK
        string display_title
        string short_title
        string thumbnail_url
        string project_code
        int year
        array category_tags
        string file_path
        string file_name
        bigint file_size_bytes
        string file_extension
        int duration_seconds
        string quality
        string codec
        bool is_visible
        float confidence
        datetime created_at
        datetime updated_at
    }

    NAS_FILE {
        uuid id PK
        string file_path UK
        string file_name
        bigint file_size_bytes
        string file_extension
        string category
        bool is_hidden
        datetime scanned_at
    }

    WATCH_PROGRESS {
        uuid id PK
        uuid user_id FK
        uuid catalog_item_id FK
        int position_seconds
        int total_seconds
        float percentage
        datetime updated_at
    }

    STREAM_SESSION {
        uuid id PK
        uuid user_id FK
        uuid catalog_item_id FK
        datetime started_at
        datetime ended_at
        bigint bytes_transferred
        string client_ip
        string user_agent
        enum status "active|completed|terminated"
    }
```

---

## 2. User Model

### 2.1 Schema

```python
@dataclass
class User:
    id: UUID
    email: str                    # Unique
    password_hash: str            # bcrypt hashed
    status: UserStatus            # pending | active | suspended
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None
```

### 2.2 User Status Enum

```python
class UserStatus(str, Enum):
    PENDING = "pending"       # 가입 후 승인 대기
    ACTIVE = "active"         # 정상 활성
    SUSPENDED = "suspended"   # 정지됨
```

### 2.3 User State Machine

```mermaid
stateDiagram-v2
    [*] --> Pending: POST /auth/register

    Pending --> Active: Admin 승인
    Pending --> Rejected: Admin 거부

    Active --> Suspended: Admin 정지
    Suspended --> Active: Admin 해제

    Active --> LoggedIn: POST /auth/login
    LoggedIn --> Active: 세션 만료/로그아웃

    LoggedIn --> Streaming: 비디오 재생
    Streaming --> LoggedIn: 재생 종료

    Rejected --> [*]

    note right of Pending
        로그인 불가
        승인 대기 페이지만 접근
    end note

    note right of Streaming
        동시 3개 제한
        진행률 자동 저장
    end note
```

---

## 3. CatalogItem Model

### 3.1 Schema

```python
@dataclass
class CatalogItem:
    id: UUID
    nas_file_id: UUID | None      # NASFile FK

    # Display Info
    display_title: str            # Title Generator 생성
    short_title: str              # 축약 제목 (≤50자)
    thumbnail_url: str | None     # 썸네일 경로

    # Classification
    project_code: str             # WSOP, HCL, GGMILLIONS, etc.
    year: int | None              # 연도
    category_tags: list[str]      # [NLHE, Main Event, Final Table, ...]

    # File Info
    file_path: str                # NAS 경로
    file_name: str
    file_size_bytes: int
    file_extension: str

    # Metadata
    duration_seconds: int | None
    quality: str | None           # HD, 1080p, 4K
    codec: str | None             # h264, h265

    # State
    is_visible: bool = True
    confidence: float             # 제목 생성 신뢰도 (0.0 ~ 1.0)

    created_at: datetime
    updated_at: datetime
```

### 3.2 Project Codes

| Code | Full Name | Description |
|------|-----------|-------------|
| `WSOP` | World Series of Poker | 메인 이벤트 |
| `HCL` | Hustler Casino Live | 라이브 캐시 게임 |
| `GGMILLIONS` | GGPoker Millions | GG 토너먼트 |
| `GOG` | Game of Gold | 골드 시리즈 |
| `PAD` | Poker After Dark | 심야 캐시 |
| `MPP` | Mystery Poker Players | 미스터리 시리즈 |
| `OTHER` | Other/Unknown | 분류 불가 |

### 3.3 CatalogItem Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Scanned: NAS 스캔

    Scanned --> Generated: Title Generator

    Generated --> Visible: confidence ≥ 0.5
    Generated --> Hidden: confidence < 0.5

    Hidden --> Visible: Admin 수동 승인
    Visible --> Hidden: Admin 숨김

    Visible --> Deleted: NAS 파일 삭제
    Hidden --> Deleted: NAS 파일 삭제

    Deleted --> [*]

    note right of Generated
        display_title 생성
        metadata 추출
        confidence 계산
    end note

    note right of Hidden
        카탈로그에 노출 안됨
        수동 검토 필요
    end note
```

---

## 4. NASFile Model

### 4.1 Schema

```python
@dataclass
class NASFileInfo:
    id: UUID
    file_path: str                # Unique, NAS 전체 경로
    file_name: str                # 파일명만
    file_size_bytes: int
    file_extension: str           # mp4, mkv, etc.
    category: str | None          # 폴더 기반 카테고리
    is_hidden: bool = False       # 숨김 파일 여부
    scanned_at: datetime
```

### 4.2 Supported Extensions

| Extension | MIME Type | Support |
|-----------|-----------|---------|
| `.mp4` | video/mp4 | ✅ Full |
| `.mkv` | video/x-matroska | ✅ Full |
| `.avi` | video/x-msvideo | ⚠️ Limited |
| `.mov` | video/quicktime | ⚠️ Limited |
| `.wmv` | video/x-ms-wmv | ⚠️ Limited |

---

## 5. WatchProgress Model

### 5.1 Schema

```python
@dataclass
class WatchProgress:
    id: UUID
    user_id: UUID                 # FK to User
    catalog_item_id: UUID         # FK to CatalogItem
    position_seconds: int         # 현재 위치
    total_seconds: int            # 전체 길이
    percentage: float             # 계산된 진행률
    updated_at: datetime          # 마지막 업데이트
```

### 5.2 Progress Calculation

```python
def calculate_percentage(position: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return min(100.0, (position / total) * 100)
```

### 5.3 Progress States

```mermaid
stateDiagram-v2
    [*] --> NotStarted: 콘텐츠 발견

    NotStarted --> InProgress: 재생 시작
    InProgress --> InProgress: 진행률 업데이트

    InProgress --> Completed: 진행률 ≥ 95%
    Completed --> InProgress: 다시 시청

    note right of InProgress
        10초마다 자동 저장
        이어보기 목록 표시
    end note

    note right of Completed
        "완료" 표시
        추천에서 우선순위 낮춤
    end note
```

---

## 6. StreamSession Model

### 6.1 Schema

```python
@dataclass
class StreamSession:
    id: UUID
    user_id: UUID                 # FK to User
    catalog_item_id: UUID         # FK to CatalogItem
    started_at: datetime
    ended_at: datetime | None
    bytes_transferred: int = 0
    client_ip: str | None
    user_agent: str | None
    status: StreamStatus          # active | completed | terminated
```

### 6.2 Stream Status

```python
class StreamStatus(str, Enum):
    ACTIVE = "active"             # 현재 스트리밍 중
    COMPLETED = "completed"       # 정상 종료
    TERMINATED = "terminated"     # 강제 종료 (Admin/Rate limit)
```

### 6.3 Stream Session Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Session as StreamSession

    User->>API: POST /stream/{id}/start
    API->>API: Rate limit check
    API->>Session: Create (status: active)
    API-->>User: session_id

    loop During playback
        User->>API: GET /stream/{id}/video (Range)
        API->>Session: Update bytes_transferred
        API-->>User: 206 Partial Content
    end

    User->>API: POST /stream/{id}/end
    API->>Session: Update (status: completed, ended_at)
    API-->>User: 200 OK
```

---

## 7. Session Model

### 7.1 Schema

```python
@dataclass
class Session:
    id: UUID
    user_id: UUID                 # FK to User
    token: str                    # JWT token (Unique)
    expires_at: datetime
    created_at: datetime
```

### 7.2 Token Structure

```json
{
  "sub": "user-id-uuid",
  "email": "user@example.com",
  "is_admin": false,
  "exp": 1702900800,
  "iat": 1702814400
}
```

---

## 8. Generated Title Model

### 8.1 Schema (Title Generator Output)

```python
@dataclass
class GeneratedTitle:
    display_title: str            # 최종 표시 제목
    short_title: str              # 축약 제목 (≤50자)
    confidence: float             # 파싱 신뢰도 (0.0 ~ 1.0)
    metadata: ParsedMetadata

@dataclass
class ParsedMetadata:
    project_code: str | None
    year: int | None
    event_number: int | None
    event_name: str | None
    episode_number: int | None
    season_number: int | None
    day_number: int | None
    part_number: int | None
    game_type: str | None         # NLHE, PLO, etc.
    buy_in: float | None
    content_type: str | None      # Main Event, Final Table, etc.
    extra_tags: list[str]
```

### 8.2 Confidence Levels

| Range | Level | Description |
|-------|-------|-------------|
| 0.9 - 1.0 | High | 정확한 패턴 매칭 |
| 0.7 - 0.89 | Medium | 부분 매칭 |
| 0.5 - 0.69 | Low | 추측 기반 |
| 0.0 - 0.49 | Very Low | Fallback, 수동 검토 필요 |

---

## 9. Database Indexes

### 9.1 User Table

```sql
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_status ON users(status);
```

### 9.2 CatalogItem Table

```sql
CREATE INDEX idx_catalog_project ON catalog_items(project_code);
CREATE INDEX idx_catalog_year ON catalog_items(year);
CREATE INDEX idx_catalog_visible ON catalog_items(is_visible);
CREATE INDEX idx_catalog_created ON catalog_items(created_at DESC);
```

### 9.3 WatchProgress Table

```sql
CREATE UNIQUE INDEX idx_progress_user_item ON watch_progress(user_id, catalog_item_id);
CREATE INDEX idx_progress_updated ON watch_progress(updated_at DESC);
```

### 9.4 StreamSession Table

```sql
CREATE INDEX idx_stream_user ON stream_sessions(user_id);
CREATE INDEX idx_stream_status ON stream_sessions(status);
CREATE INDEX idx_stream_started ON stream_sessions(started_at DESC);
```

---

*← [03-api-spec.md](./03-api-spec.md) | [05-user-interface.md](./05-user-interface.md) →*
