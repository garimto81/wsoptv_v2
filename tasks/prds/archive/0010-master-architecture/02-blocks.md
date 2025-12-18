# 02. Block Architecture

*← [01-architecture.md](./01-architecture.md) | [03-api-spec.md](./03-api-spec.md) →*

---

## 1. Block Overview

### 1.1 Block Dependency Graph

```mermaid
flowchart LR
    subgraph Wave1["Wave 1 (L0) - No Dependencies"]
        direction TB
        Auth["auth<br/>v1.0.0<br/>━━━━━━━━━━━━━━<br/>JWT 인증<br/>사용자 관리<br/>권한 검증"]
        Cache["cache<br/>v1.0.0<br/>━━━━━━━━━━━━━━<br/>Redis L1 캐시<br/>SSD L2 캐시<br/>TTL 관리"]
        TitleGen["title_generator<br/>v1.0.0<br/>━━━━━━━━━━━━━━<br/>파일명 파싱<br/>제목 생성<br/>메타데이터 추출"]
    end

    subgraph Wave2["Wave 2 (L1)"]
        direction TB
        Content["content<br/>v1.0.0<br/>━━━━━━━━━━━━━━<br/>메타데이터<br/>진행률 관리<br/>관련 콘텐츠"]
        Search["search<br/>v1.0.0<br/>━━━━━━━━━━━━━━<br/>MeiliSearch<br/>전문 검색<br/>자동완성"]
        Worker["worker<br/>v1.0.0<br/>━━━━━━━━━━━━━━<br/>썸네일 생성<br/>NAS 스캔<br/>백그라운드"]
        FlatCatalog["flat_catalog<br/>v1.0.0<br/>━━━━━━━━━━━━━━<br/>단일 계층<br/>NAS 매핑<br/>필터/정렬"]
    end

    subgraph Wave3["Wave 3 (L2)"]
        direction TB
        Stream["stream<br/>v1.0.0<br/>━━━━━━━━━━━━━━<br/>HTTP Range<br/>Rate Limiting<br/>동시 접속"]
        Admin["admin<br/>v1.0.0<br/>━━━━━━━━━━━━━━<br/>대시보드<br/>사용자 승인<br/>모니터링"]
    end

    %% Dependencies
    Content --> Auth
    Content --> Cache
    Search --> Auth
    Worker --> Cache
    FlatCatalog --> TitleGen
    FlatCatalog --> Cache
    Stream --> Auth
    Stream --> Cache
    Stream --> Content
    Admin --> Auth
    Admin --> Content
    Admin --> Stream
```

### 1.2 Block Contract Matrix

| Block | provides | requires | Wave |
|-------|----------|----------|------|
| **auth** | `auth.validate_token`, `auth.get_user`, `auth.check_permission` | - | L0 |
| **cache** | `cache.get`, `cache.set`, `cache.delete` | - | L0 |
| **title_generator** | `title.generate`, `title.parse`, `title.batch` | - | L0 |
| **content** | `content.get_content`, `content.get_metadata` | `auth.validate_token`, `cache.get` | L1 |
| **search** | `search.search`, `search.index` | `auth.validate_token` | L1 |
| **worker** | `worker.enqueue`, `worker.process` | `cache.get` | L1 |
| **flat_catalog** | `catalog.list`, `catalog.get`, `catalog.search`, `catalog.sync` | `title.generate` | L1 |
| **stream** | `stream.get_url`, `stream.range` | `auth.validate_token`, `cache.get`, `content.get_metadata` | L2 |
| **admin** | `admin.dashboard`, `admin.users` | `auth.validate_token`, `auth.check_permission` | L2 |

---

## 2. Orchestration Components

### 2.1 MessageBus

```mermaid
classDiagram
    class MessageBus {
        -_instance: MessageBus
        -_subscribers: dict
        -_message_queue: Queue
        +get_instance() MessageBus
        +reset_instance() void
        +subscribe(channel, handler) void
        +unsubscribe(channel, handler) void
        +publish(channel, message) void
        +request_response(channel, message, timeout) BlockMessage
    }

    class BlockMessage {
        +source_block: str
        +event_type: str
        +payload: dict
        +correlation_id: str
        +timestamp: datetime
        +to_dict() dict
        +from_dict(data) BlockMessage
    }

    MessageBus --> BlockMessage : publishes
```

**사용 예시:**

```python
from src.orchestration.message_bus import MessageBus, BlockMessage

# 메시지 발행
bus = MessageBus.get_instance()
await bus.publish("catalog.updated", BlockMessage(
    source_block="flat_catalog",
    event_type="item_created",
    payload={"item_id": "123", "display_title": "WSOP 2024 Event #5"}
))

# 메시지 구독
async def on_catalog_update(msg: BlockMessage):
    print(f"New item: {msg.payload['display_title']}")

await bus.subscribe("catalog.updated", on_catalog_update)
```

### 2.2 BlockRegistry

```mermaid
classDiagram
    class BlockRegistry {
        -_blocks: dict
        -_provided_functions: dict
        +register(block: BlockInfo) void
        +unregister(block_id: str) void
        +get_block(block_id: str) BlockInfo
        +can_register(block: BlockInfo) bool
        +is_healthy(block_id: str) bool
        +update_health(block_id, status) void
        +get_all_blocks() list
        +get_dependency_order() list
    }

    class BlockInfo {
        +block_id: str
        +version: str
        +provides: list~str~
        +requires: list~str~
        +status: BlockStatus
        +registered_at: datetime
        +last_health_check: datetime
        +metadata: dict
        +get_required_blocks() set
    }

    class BlockStatus {
        <<enumeration>>
        INITIALIZING
        HEALTHY
        UNHEALTHY
        DEGRADED
        STOPPED
    }

    BlockRegistry --> BlockInfo : manages
    BlockInfo --> BlockStatus : has
```

### 2.3 Block Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Initializing: BlockRegistry.register()

    Initializing --> Healthy: 의존성 충족
    Initializing --> Unhealthy: 의존성 미충족

    Healthy --> Degraded: 부분 장애
    Healthy --> Unhealthy: 전체 장애

    Degraded --> Healthy: 복구
    Degraded --> Unhealthy: 추가 장애

    Unhealthy --> Healthy: 완전 복구
    Unhealthy --> Stopped: 수동 중지

    Stopped --> [*]

    note right of Initializing
        의존성 검증
        Contract 체크
        provides/requires 매칭
    end note

    note right of Healthy
        정상 운영
        헬스체크 통과
    end note
```

---

## 3. Block Details

### 3.1 Auth Block (L0)

```mermaid
flowchart TB
    subgraph AuthBlock["Auth Block"]
        direction TB
        subgraph Models["Models"]
            User["User<br/>━━━━━━━━━━━━━━<br/>id, email<br/>password_hash<br/>status, is_admin"]
            Session["Session<br/>━━━━━━━━━━━━━━<br/>id, user_id<br/>token, expires_at"]
        end

        subgraph Service["AuthService"]
            Register["register()"]
            Login["login()"]
            Verify["verify_token()"]
            Approve["approve_user()"]
        end

        subgraph Router["Router /auth"]
            R1["POST /register"]
            R2["POST /login"]
            R3["GET /me"]
            R4["POST /users/{id}/approve"]
        end
    end

    R1 --> Register
    R2 --> Login
    R3 --> Verify
    R4 --> Approve

    Register --> User
    Login --> Session
```

**provides:**
- `auth.validate_token` - JWT 토큰 검증
- `auth.get_user` - 사용자 정보 조회
- `auth.check_permission` - 권한 확인 (admin 등)

**File Structure:**
```
src/blocks/auth/
├── __init__.py
├── models.py      # User, Session, UserStatus
├── service.py     # AuthService
└── router.py      # FastAPI router
```

### 3.2 Cache Block (L0)

```mermaid
flowchart TB
    subgraph CacheBlock["Cache Block"]
        direction TB
        subgraph Tiers["Cache Tiers"]
            L1["L1 Redis<br/>━━━━━━━━━━━━━━<br/>Metadata<br/>Session<br/>TTL 5-10min"]
            L2["L2 SSD<br/>━━━━━━━━━━━━━━<br/>Hot Content<br/>500GB LRU"]
            L3["L3 Limiter<br/>━━━━━━━━━━━━━━<br/>Global: 20<br/>Per User: 3"]
            L4["L4 NAS<br/>━━━━━━━━━━━━━━<br/>Origin<br/>18TB+"]
        end

        subgraph Service["CacheService"]
            Get["get(key)"]
            Set["set(key, value, ttl)"]
            Delete["delete(key)"]
            GetChunk["get_chunk(id, n)"]
        end
    end

    Get --> L1
    L1 -->|Miss| L2
    L2 -->|Miss| L3
    L3 --> L4
```

**provides:**
- `cache.get` - 캐시 조회
- `cache.set` - 캐시 저장
- `cache.delete` - 캐시 삭제

**File Structure:**
```
src/blocks/cache/
├── __init__.py
├── models.py
├── service.py
└── tiers/
    ├── __init__.py
    ├── l1_redis.py
    ├── l2_ssd.py
    ├── l3_limiter.py
    └── l4_nas.py
```

### 3.3 Title Generator Block (L0)

```mermaid
flowchart TB
    subgraph TitleGenBlock["Title Generator Block (G)"]
        direction TB
        subgraph Patterns["Pattern Registry"]
            WSOP["WSOP Patterns (6)"]
            HCL["HCL Patterns (4)"]
            GG["GGMillions Patterns (3)"]
            Other["Other Patterns (5)"]
        end

        subgraph Service["TitleGeneratorService"]
            Generate["generate(filename)"]
            Parse["parse(filename)"]
            Batch["batch_generate(filenames)"]
        end

        subgraph Output["Output"]
            Title["GeneratedTitle<br/>━━━━━━━━━━━━━━<br/>display_title<br/>short_title<br/>confidence"]
            Meta["ParsedMetadata<br/>━━━━━━━━━━━━━━<br/>project_code<br/>year, event<br/>game_type"]
        end
    end

    Generate --> Patterns
    Patterns --> Title
    Parse --> Meta
```

**provides:**
- `title.generate` - 단일 제목 생성
- `title.parse` - 메타데이터 파싱
- `title.batch` - 배치 제목 생성

**Pattern Examples:**
```python
# WSOP 패턴
r"WSOP[_\s]*(?P<year>\d{4})[_\s]*Event[_\s#]*(?P<event>\d+)[_\s]*Day[_\s]*(?P<day>\d+)"
# → "WSOP 2024 Event #5 - Day 1"

# HCL 패턴
r"HCL[_\s]*S(?P<season>\d+)E(?P<episode>\d+)"
# → "Hustler Casino Live Season 12 Episode 5"
```

### 3.4 Flat Catalog Block (L1)

```mermaid
flowchart TB
    subgraph CatalogBlock["Flat Catalog Block (F)"]
        direction TB
        subgraph Models["Models"]
            Item["CatalogItem<br/>━━━━━━━━━━━━━━<br/>display_title<br/>project_code<br/>file_path<br/>confidence"]
            NASFile["NASFileInfo<br/>━━━━━━━━━━━━━━<br/>path, name<br/>size, extension"]
        end

        subgraph Service["FlatCatalogService"]
            GetAll["get_all(filters)"]
            Search["search(query)"]
            Sync["sync_from_nas()"]
            Create["create_from_nas_file()"]
        end

        subgraph Events["Event Handlers"]
            OnCreate["on_nas_file_created"]
            OnUpdate["on_nas_file_updated"]
            OnDelete["on_nas_file_deleted"]
        end
    end

    Sync --> Create
    Create --> TitleGen["title_generator"]
    TitleGen --> Item

    OnCreate --> Create
```

**provides:**
- `catalog.list` - 카탈로그 목록
- `catalog.get` - 단일 아이템 조회
- `catalog.search` - 검색
- `catalog.sync` - NAS 동기화

**requires:**
- `title.generate` - Title Generator Block

### 3.5 Stream Block (L2)

```mermaid
flowchart TB
    subgraph StreamBlock["Stream Block"]
        direction TB
        subgraph Service["StreamService"]
            Start["start_stream(user, content)"]
            GetUrl["get_stream_url(content)"]
            Range["handle_range_request()"]
            End["end_stream(session)"]
        end

        subgraph RateLimit["Rate Limiter"]
            Global["Global Limit: 20"]
            PerUser["Per User: 3"]
        end

        subgraph Router["Router /stream"]
            R1["POST /{id}/start"]
            R2["GET /{id}/video"]
            R3["POST /{id}/end"]
        end
    end

    R1 --> Start
    Start --> RateLimit
    R2 --> Range
    Range --> Cache["Cache Block"]
    R3 --> End
```

**provides:**
- `stream.get_url` - 스트림 URL 생성
- `stream.range` - HTTP Range 처리

**requires:**
- `auth.validate_token`
- `cache.get`
- `content.get_metadata`

### 3.6 Admin Block (L2)

```mermaid
flowchart TB
    subgraph AdminBlock["Admin Block"]
        direction TB
        subgraph Dashboard["Dashboard Service"]
            Stats["get_stats()"]
            Users["get_users(filters)"]
            Streams["get_active_streams()"]
        end

        subgraph UserMgmt["User Management"]
            Approve["approve_user(id)"]
            Suspend["suspend_user(id)"]
            List["list_pending_users()"]
        end

        subgraph Router["Router /admin"]
            R1["GET /dashboard"]
            R2["GET /users"]
            R3["POST /users/{id}/approve"]
            R4["GET /streams"]
        end
    end

    R1 --> Stats
    R2 --> Users
    R3 --> Approve
    R4 --> Streams
```

**provides:**
- `admin.dashboard` - 대시보드 통계
- `admin.users` - 사용자 관리

**requires:**
- `auth.validate_token`
- `auth.check_permission`

---

## 4. Inter-Block Communication

### 4.1 Event Types

| Channel | Publisher | Subscribers | Description |
|---------|-----------|-------------|-------------|
| `nas.file.created` | Worker | Flat Catalog | 새 파일 발견 |
| `nas.file.updated` | Worker | Flat Catalog | 파일 변경 |
| `nas.file.deleted` | Worker | Flat Catalog | 파일 삭제 |
| `catalog.item.created` | Flat Catalog | Search | 카탈로그 아이템 생성 |
| `catalog.item.updated` | Flat Catalog | Search | 카탈로그 아이템 수정 |
| `user.registered` | Auth | Admin | 새 사용자 가입 |
| `user.approved` | Auth | - | 사용자 승인됨 |
| `stream.started` | Stream | Admin | 스트림 시작 |
| `stream.ended` | Stream | Admin, Content | 스트림 종료 |

### 4.2 Sync Flow Example

```mermaid
sequenceDiagram
    participant Admin as Admin/Cron
    participant API as FastAPI
    participant Catalog as Flat Catalog
    participant Title as Title Generator
    participant Bus as MessageBus
    participant Search as Search Block

    Admin->>API: POST /api/v1/catalog/sync
    API->>Catalog: sync_from_nas_files(files)

    loop Each file
        Catalog->>Title: generate(filename)
        Title-->>Catalog: GeneratedTitle
        Catalog->>Catalog: Create/Update CatalogItem
        Catalog->>Bus: publish("catalog.item.created")
    end

    Bus->>Search: handler(message)
    Search->>Search: Index new item

    Catalog-->>API: SyncResult
    API-->>Admin: 200 OK
```

---

## 5. Testing

### 5.1 Test Coverage

| Block | Test File | Test Count |
|-------|-----------|------------|
| orchestration | `test_orchestration.py` | - |
| auth | `test_auth_block.py` | - |
| cache | `test_cache_block.py` | - |
| title_generator | `test_title_generator.py` | 35 |
| content | `test_content_block.py` | - |
| search | `test_search_block.py` | - |
| worker | `test_worker_block.py` | - |
| flat_catalog | `test_flat_catalog.py` | 36 |
| flat_catalog events | `test_flat_catalog_events.py` | 14 |
| flat_catalog migration | `test_flat_catalog_migration.py` | 15 |
| stream | `test_stream_block.py` | - |
| admin | `test_admin_block.py` | - |
| **Integration** | `test_catalog_title_integration.py` | 12 |

### 5.2 Test Commands

```bash
# 전체 테스트
pytest tests/ -v

# 특정 블럭 테스트
pytest tests/test_blocks/test_flat_catalog.py -v

# 통합 테스트
pytest tests/test_integration/ -v

# 커버리지
pytest tests/ --cov=src/blocks --cov-report=html
```

---

*← [01-architecture.md](./01-architecture.md) | [03-api-spec.md](./03-api-spec.md) →*
