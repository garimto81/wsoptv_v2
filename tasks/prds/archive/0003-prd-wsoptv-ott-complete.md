# PRD-0003: WSOPTV OTT 플랫폼 완전 기획서

**Version**: 1.0.0
**Status**: Final
**Author**: Claude Code (AI)
**Created**: 2024-12-15
**Last Updated**: 2024-12-15

---

## 1. Executive Summary

### 1.1 제품 개요

**WSOPTV**는 프라이빗 포커 VOD 스트리밍 플랫폼입니다. 18TB+ 아카이브를 보유하고 있으며, 초대 기반 회원제로 운영됩니다.

```mermaid
mindmap
  root((WSOPTV))
    사용자
      회원가입
      로그인
      시청
    콘텐츠
      WSOP
      HCL
      GGMillions
      GOG
    관리자
      승인
      모니터링
      통계
```

### 1.2 핵심 가치

| 가치 | 설명 |
|------|------|
| **프라이빗** | 초대 기반, 관리자 승인 필수 |
| **고품질** | 원본 그대로 스트리밍 (트랜스코딩 없음) |
| **Netflix UX** | 단일 계층 카탈로그, 이어보기 |
| **확장성** | Block Architecture로 모듈화 |

---

## 2. System Architecture

### 2.1 전체 시스템 아키텍처

```mermaid
flowchart TB
    subgraph Client["클라이언트"]
        Browser["Web Browser<br/>(Next.js 14)"]
    end

    subgraph Backend["Backend Server"]
        subgraph FastAPI["FastAPI App (Port 8002)"]
            API["API Gateway"]

            subgraph Orchestration["Orchestration Layer"]
                MessageBus["MessageBus<br/>(Pub/Sub)"]
                Registry["BlockRegistry<br/>(Lifecycle)"]
                Contract["Contract<br/>(Validation)"]
            end

            subgraph L0["Wave 1 (L0) - No Dependencies"]
                Auth["Auth Block"]
                Cache["Cache Block"]
                TitleGen["Title Generator<br/>(Block G)"]
            end

            subgraph L1["Wave 2 (L1)"]
                Content["Content Block"]
                Search["Search Block"]
                Worker["Worker Block"]
                Catalog["Flat Catalog<br/>(Block F)"]
            end

            subgraph L2["Wave 3 (L2) - Full Dependencies"]
                Stream["Stream Block"]
                Admin["Admin Block"]
            end
        end
    end

    subgraph Infrastructure["Infrastructure (Docker)"]
        Redis["Redis 7<br/>(L1 Cache)<br/>Port 6380"]
        PostgreSQL["PostgreSQL 16<br/>(Metadata)<br/>Port 5434"]
        MeiliSearch["MeiliSearch v1.6<br/>(Search)<br/>Port 7701"]
    end

    subgraph Storage["Storage"]
        NAS["NAS Server<br/>(SMB: 10.10.100.122)<br/>Z:\ARCHIVE → /mnt/nas"]
        SSD["SSD Cache<br/>(L2 Hot Content)<br/>500GB LRU"]
    end

    Browser --> API
    API --> Orchestration
    Orchestration --> L0
    Orchestration --> L1
    Orchestration --> L2

    Auth --> Redis
    Cache --> Redis
    Cache --> SSD
    Content --> PostgreSQL
    Search --> MeiliSearch
    Catalog --> TitleGen
    Stream --> NAS
    Stream --> Cache
    Admin --> PostgreSQL

    L0 --> MessageBus
    L1 --> MessageBus
    L2 --> MessageBus
```

### 2.2 Block Dependencies

```mermaid
flowchart LR
    subgraph Wave1["Wave 1 (L0)<br/>No Dependencies"]
        Auth["auth<br/>v1.0.0"]
        Cache["cache<br/>v1.0.0"]
        TitleGen["title_generator<br/>v1.0.0"]
    end

    subgraph Wave2["Wave 2 (L1)"]
        Content["content<br/>v1.0.0"]
        Search["search<br/>v1.0.0"]
        Worker["worker<br/>v1.0.0"]
        FlatCatalog["flat_catalog<br/>v1.0.0"]
    end

    subgraph Wave3["Wave 3 (L2)"]
        Stream["stream<br/>v1.0.0"]
        Admin["admin<br/>v1.0.0"]
    end

    %% Dependencies
    Content --> Auth
    Content --> Cache
    Search --> Auth
    Worker --> Cache
    FlatCatalog --> TitleGen
    Stream --> Auth
    Stream --> Cache
    Stream --> Content
    Admin --> Auth
```

### 2.3 4-Tier Cache Architecture

```mermaid
flowchart LR
    subgraph Request["User Request"]
        User["User"]
    end

    subgraph L1["L1: Redis<br/>(Metadata)"]
        Redis["Redis 7<br/>TTL: 5-10min"]
    end

    subgraph L2["L2: SSD<br/>(Hot Content)"]
        SSD["Local SSD<br/>500GB LRU<br/>7일 내 5회+"]
    end

    subgraph L3["L3: Rate Limiter"]
        Limiter["Global: 20<br/>Per User: 3"]
    end

    subgraph L4["L4: NAS<br/>(Origin)"]
        NAS["NAS Server<br/>18TB+ Archive<br/>SMB Mount"]
    end

    User --> Redis
    Redis -->|Miss| SSD
    SSD -->|Miss| Limiter
    Limiter --> NAS

    NAS -.->|Populate| SSD
    SSD -.->|Populate| Redis
```

---

## 3. Data Flow

### 3.1 인증 플로우

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend<br/>(Next.js)
    participant API as FastAPI
    participant Auth as Auth Block
    participant DB as PostgreSQL
    participant Admin as Admin

    %% 회원가입
    rect rgb(240, 248, 255)
        Note over User, Admin: 회원가입 플로우
        User->>FE: 1. 회원가입 폼 제출
        FE->>API: POST /auth/register
        API->>Auth: register(email, password)
        Auth->>DB: CREATE user (status: PENDING)
        DB-->>Auth: User created
        Auth-->>API: UserResponse
        API-->>FE: 201 Created
        FE-->>User: "승인 대기 중" 안내
    end

    %% 관리자 승인
    rect rgb(255, 248, 240)
        Note over User, Admin: 관리자 승인 플로우
        Admin->>FE: 대시보드 접속
        FE->>API: GET /admin/users?status=pending
        API-->>FE: Pending users list
        Admin->>FE: 사용자 승인 클릭
        FE->>API: POST /auth/users/{id}/approve
        API->>Auth: approve_user(user_id)
        Auth->>DB: UPDATE status = ACTIVE
        DB-->>Auth: Updated
        Auth-->>API: UserResponse
        API-->>FE: 200 OK
    end

    %% 로그인
    rect rgb(240, 255, 240)
        Note over User, Admin: 로그인 플로우
        User->>FE: 2. 로그인 폼 제출
        FE->>API: POST /auth/login
        API->>Auth: login(email, password)
        Auth->>DB: SELECT user WHERE email
        DB-->>Auth: User (status: ACTIVE)
        Auth->>Auth: verify password
        Auth->>Auth: create session token
        Auth-->>API: LoginResponse {token, user_id}
        API-->>FE: 200 OK + token
        FE->>FE: Store token (localStorage)
        FE-->>User: Redirect to /browse
    end
```

### 3.2 스트리밍 플로우

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant Stream as Stream Block
    participant Cache as Cache Block
    participant NAS as NAS Server

    User->>FE: 1. 비디오 재생 클릭
    FE->>API: POST /stream/{content_id}/start
    API->>Stream: start_stream(user_id, content_id)

    alt Rate Limit 초과
        Stream-->>API: {allowed: false, error: "limit exceeded"}
        API-->>FE: 429 Too Many Requests
        FE-->>User: "동시 시청 제한 초과" 알림
    else 허용
        Stream-->>API: {allowed: true}
        API-->>FE: 200 OK
    end

    FE->>API: GET /stream/{content_id}
    API->>Stream: get_stream_url(content_id, token)
    Stream-->>API: {url, content_type, content_length}
    API-->>FE: Stream URL

    FE->>API: GET /stream/{content_id}/video<br/>Range: bytes=0-1048575
    API->>Stream: stream_video()

    Stream->>Cache: Check L1 (Redis)
    alt L1 Hit
        Cache-->>Stream: Metadata
    else L1 Miss
        Stream->>Cache: Check L2 (SSD)
        alt L2 Hit
            Cache-->>Stream: File chunk
        else L2 Miss
            Stream->>NAS: Read file range
            NAS-->>Stream: Video bytes
            Stream->>Cache: Populate L2 (if hot)
        end
    end

    Stream-->>API: 206 Partial Content
    API-->>FE: Video chunk
    FE-->>User: Video plays

    loop 매 10초마다
        FE->>API: POST /api/v1/progress
        Note right of FE: {content_id, position, duration}
    end

    User->>FE: 재생 종료
    FE->>API: POST /stream/{content_id}/end
    API->>Stream: end_stream(user_id, content_id)
    Stream-->>API: {status: "ended"}
```

### 3.3 카탈로그 동기화 플로우

```mermaid
sequenceDiagram
    autonumber
    participant Cron as Cron Job
    participant API as FastAPI
    participant Catalog as Flat Catalog<br/>(Block F)
    participant Title as Title Generator<br/>(Block G)
    participant NAS as NAS Server

    Cron->>NAS: Scan directories
    NAS-->>Cron: File list
    Cron->>API: POST /api/v1/catalog/sync
    API->>Catalog: sync_from_nas_files(files)

    loop 각 파일에 대해
        Catalog->>Title: generate(filename)
        Title->>Title: Pattern matching
        Title-->>Catalog: GeneratedTitle<br/>{display_title, confidence}
        Catalog->>Catalog: Create/Update CatalogItem
    end

    Catalog-->>API: SyncResult<br/>{created, updated, deleted}
    API-->>Cron: 200 OK
```

---

## 4. User Interface

### 4.1 페이지 라우트 구조

```mermaid
flowchart TB
    subgraph Public["Public Routes"]
        Root["/"] --> Redirect["Redirect"]
        Login["/login"]
        Register["/register"]
        Pending["/register/pending"]
    end

    subgraph Protected["Protected Routes (User)"]
        Browse["/browse"]
        Search["/search"]
        Watch["/watch/[id]"]
        History["/history"]
    end

    subgraph Admin["Admin Routes"]
        Dashboard["/admin/dashboard"]
        Users["/admin/users"]
        Streams["/admin/streams"]
    end

    Redirect -->|"not logged in"| Login
    Redirect -->|"logged in"| Browse

    Login -->|"success"| Browse
    Register -->|"success"| Pending

    Browse --> Watch
    Browse --> Search
    Search --> Watch
```

### 4.2 사용자 상태 전이

```mermaid
stateDiagram-v2
    [*] --> Anonymous: 첫 방문

    Anonymous --> Pending: 회원가입
    Pending --> Active: 관리자 승인
    Pending --> Rejected: 가입 거절

    Active --> Suspended: 정지
    Suspended --> Active: 정지 해제

    Active --> LoggedIn: 로그인
    LoggedIn --> Active: 로그아웃
    LoggedIn --> Streaming: 비디오 재생
    Streaming --> LoggedIn: 재생 종료

    Rejected --> [*]

    note right of Pending
        관리자 승인 필수
        이메일 알림 (추후)
    end note

    note right of Streaming
        동시 3개 제한
        진행률 자동 저장
    end note
```

### 4.3 UI 컴포넌트 구조

```mermaid
flowchart TB
    subgraph Layout["Layout Components"]
        Header["Header<br/>- Logo<br/>- Search<br/>- User Menu"]
        Sidebar["Sidebar (Admin)<br/>- Dashboard<br/>- Users<br/>- Streams"]
        Footer["Footer"]
    end

    subgraph Pages["Page Components"]
        subgraph AuthPages["Auth"]
            LoginPage["LoginPage<br/>- LoginForm"]
            RegisterPage["RegisterPage<br/>- RegisterForm"]
        end

        subgraph MainPages["Main"]
            BrowsePage["BrowsePage<br/>- HeroBanner<br/>- ContentRow[]"]
            SearchPage["SearchPage<br/>- SearchBar<br/>- ContentGrid"]
            WatchPage["WatchPage<br/>- VideoPlayer<br/>- RelatedContent"]
            HistoryPage["HistoryPage<br/>- ContentGrid"]
        end

        subgraph AdminPages["Admin"]
            DashboardPage["DashboardPage<br/>- StatsCard[]<br/>- UserTable"]
            UsersPage["UsersPage<br/>- UserTable<br/>- ApproveModal"]
            StreamsPage["StreamsPage<br/>- StreamMonitor"]
        end
    end

    subgraph Shared["Shared Components"]
        ContentCard["ContentCard<br/>- Thumbnail<br/>- Title<br/>- Progress"]
        ContentGrid["ContentGrid<br/>- ContentCard[]"]
        ContentRow["ContentRow<br/>- Title<br/>- ContentCard[]"]
        VideoPlayer["VideoPlayer<br/>- Controls<br/>- ProgressBar"]
    end

    Header --> MainPages
    Header --> AdminPages
    Sidebar --> AdminPages

    BrowsePage --> ContentRow
    ContentRow --> ContentCard
    SearchPage --> ContentGrid
    ContentGrid --> ContentCard
    WatchPage --> VideoPlayer
```

### 4.4 Browse 페이지 레이아웃

```mermaid
flowchart TB
    subgraph BrowsePage["Browse Page (/browse)"]
        subgraph Header["Header"]
            Logo["WSOPTV Logo"]
            Search["Search Bar"]
            UserMenu["User Dropdown"]
        end

        subgraph Hero["Hero Section"]
            Featured["Featured Content<br/>- Background Image<br/>- Title<br/>- Play Button"]
        end

        subgraph Continue["Continue Watching"]
            C1["Card 1<br/>45%"]
            C2["Card 2<br/>20%"]
            C3["Card 3<br/>75%"]
        end

        subgraph WSOP["WSOP Series (156)"]
            W1["Event #1"]
            W2["Event #2"]
            W3["Main Event"]
            WMore["..."]
        end

        subgraph HCL["Hustler Casino Live (89)"]
            H1["S12E10"]
            H2["S12E09"]
            H3["S12E08"]
            HMore["..."]
        end

        subgraph GG["GGMillions (45)"]
            G1["Super HR"]
            G2["High Roller"]
            G3["Main"]
            GMore["..."]
        end
    end

    Header --> Hero
    Hero --> Continue
    Continue --> WSOP
    WSOP --> HCL
    HCL --> GG
```

### 4.5 Video Player 상태

```mermaid
stateDiagram-v2
    [*] --> Loading: 페이지 진입

    Loading --> Ready: 메타데이터 로드
    Loading --> Error: 로드 실패

    Ready --> Playing: play()
    Playing --> Paused: pause()
    Paused --> Playing: play()

    Playing --> Buffering: 버퍼 부족
    Buffering --> Playing: 버퍼 충분

    Playing --> Ended: 재생 완료
    Paused --> Ended: 재생 완료

    Ended --> Playing: replay()

    Error --> [*]

    note right of Playing
        매 10초마다
        진행률 저장
    end note

    note right of Buffering
        로딩 인디케이터
        표시
    end note
```

---

## 5. API Specification

### 5.1 API 엔드포인트 맵

```mermaid
flowchart LR
    subgraph Auth["/auth"]
        AR["POST /register"]
        AL["POST /login"]
        AO["POST /logout"]
        AM["GET /me"]
        AA["POST /users/{id}/approve"]
    end

    subgraph Content["/content"]
        CL["GET /"]
        CG["GET /{id}"]
        CP["GET /{id}/progress"]
        CU["POST /{id}/progress"]
    end

    subgraph Catalog["/api/v1/catalog"]
        CAL["GET /"]
        CAS["GET /search"]
        CAST["GET /stats"]
        CAP["GET /projects"]
        CAY["GET /years"]
        CAG["GET /{id}"]
        CAPATCH["PATCH /{id}"]
        CAD["DELETE /{id}"]
        CAVIS["POST /{id}/visibility"]
        CASYNC["POST /sync"]
    end

    subgraph Title["/api/v1/title"]
        TG["POST /generate"]
        TB["POST /batch"]
    end

    subgraph Stream["/stream"]
        SG["GET /{id}"]
        SV["GET /{id}/video"]
        SS["POST /{id}/start"]
        SE["POST /{id}/end"]
        SB["GET /{id}/bandwidth"]
    end

    subgraph Admin["/admin"]
        AD["GET /dashboard"]
        AU["GET /users"]
        AUA["POST /users/{id}/approve"]
        AUS["POST /users/{id}/suspend"]
        AS["GET /system"]
        AST["GET /streams"]
    end

    subgraph Progress["/api/v1/progress"]
        PG["GET /{id}"]
        PS["POST /"]
        PC["POST /{id}/complete"]
    end
```

### 5.2 주요 API 스펙

| Category | Method | Endpoint | Request | Response | Auth |
|----------|--------|----------|---------|----------|------|
| **Auth** | POST | `/auth/register` | `{email, password}` | `{id, email, status}` | - |
| | POST | `/auth/login` | `{email, password}` | `{token, user_id}` | - |
| | GET | `/auth/me` | - | `{id, email, status, is_admin}` | Bearer |
| **Catalog** | GET | `/api/v1/catalog/` | `?project_code&year&skip&limit` | `{items[], total, skip, limit}` | - |
| | GET | `/api/v1/catalog/search` | `?q=keyword&limit` | `CatalogItem[]` | - |
| | GET | `/api/v1/catalog/{id}` | - | `CatalogItem` | - |
| | POST | `/api/v1/catalog/sync` | `{files: NASFile[]}` | `SyncResult` | Bearer |
| **Title** | POST | `/api/v1/title/generate` | `{filename}` | `{display_title, confidence}` | - |
| | POST | `/api/v1/title/batch` | `{filenames[]}` | `GeneratedTitle[]` | - |
| **Stream** | GET | `/stream/{id}` | - | `{url, content_type, length}` | Bearer |
| | GET | `/stream/{id}/video` | `Range: bytes=0-N` | `206 Partial Content` | - |
| | POST | `/stream/{id}/start` | - | `{allowed: bool}` | Bearer |
| **Progress** | GET | `/api/v1/progress/{id}` | `?token` | `{position, duration, percent}` | Token |
| | POST | `/api/v1/progress` | `{content_id, position, duration}` | `{status: "saved"}` | Token |
| **Admin** | GET | `/admin/dashboard` | - | `DashboardData` | Bearer + Admin |
| | GET | `/admin/users` | `?page&size` | `UserList` | Bearer + Admin |
| | POST | `/admin/users/{id}/approve` | - | `User` | Bearer + Admin |

---

## 6. Data Models

### 6.1 Entity Relationship

```mermaid
erDiagram
    User ||--o{ Session : has
    User ||--o{ WatchProgress : has
    User ||--o{ Stream : watches

    CatalogItem ||--o{ WatchProgress : tracked_by
    CatalogItem ||--o{ Stream : streamed_as
    CatalogItem ||--|| NASFile : maps_to

    User {
        uuid id PK
        string email UK
        string password_hash
        enum status "PENDING|ACTIVE|SUSPENDED"
        bool is_admin
        datetime created_at
        datetime updated_at
    }

    Session {
        uuid id PK
        uuid user_id FK
        string token UK
        datetime expires_at
        datetime created_at
    }

    CatalogItem {
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
        bool is_visible
        float confidence
        datetime created_at
        datetime updated_at
    }

    NASFile {
        uuid id PK
        string file_path UK
        string file_name
        bigint file_size_bytes
        string file_extension
        string file_category
        bool is_hidden_file
        datetime scanned_at
    }

    WatchProgress {
        uuid id PK
        uuid user_id FK
        uuid content_id FK
        int position_seconds
        int total_seconds
        float percentage
        datetime updated_at
    }

    Stream {
        uuid id PK
        uuid user_id FK
        uuid content_id FK
        datetime started_at
        datetime ended_at
        bigint bytes_transferred
    }
```

### 6.2 CatalogItem 상태 전이

```mermaid
stateDiagram-v2
    [*] --> Scanned: NAS 스캔

    Scanned --> Generated: Title Generator
    Generated --> Visible: 신뢰도 >= 50%
    Generated --> Hidden: 신뢰도 < 50%

    Hidden --> Visible: 관리자 수정
    Visible --> Hidden: 관리자 숨김

    Visible --> Deleted: 파일 삭제됨
    Hidden --> Deleted: 파일 삭제됨

    Deleted --> [*]

    note right of Generated
        display_title 생성
        confidence 계산
    end note

    note right of Hidden
        수동 검토 필요
    end note
```

---

## 7. Project Codes & Patterns

### 7.1 지원 프로젝트

```mermaid
pie title 프로젝트별 콘텐츠 비율 (예시)
    "WSOP" : 156
    "HCL" : 89
    "GGMillions" : 45
    "GOG" : 23
    "PAD" : 15
    "MPP" : 8
    "OTHER" : 12
```

| Code | Full Name | Pattern Priority | Example |
|------|-----------|------------------|---------|
| WSOP | World Series of Poker | High | `WSOP_2024_Event5_Day1.mp4` |
| HCL | Hustler Casino Live | High | `HCL_S12E05_HighStakes.mkv` |
| GGMILLIONS | GGPoker Millions | Medium | `GGMillions_2024_SuperHR.mp4` |
| GOG | Game of Gold | Medium | `GOG_S1E5_Elimination.mp4` |
| PAD | Poker After Dark | Medium | `PAD_S3E10_CashGame.mp4` |
| MPP | Mystery Poker Players | Low | `MPP_2024_Special.mp4` |
| OTHER | Unknown/Fallback | Lowest | `random_poker_video.mp4` |

### 7.2 Title Generator 패턴 매칭

```mermaid
flowchart TB
    Input["Input: filename"]

    subgraph Patterns["Pattern Registry"]
        P1["WSOP Patterns (6)"]
        P2["HCL Patterns (4)"]
        P3["GG Patterns (3)"]
        P4["Other Patterns (5)"]
    end

    subgraph Result["Generated Title"]
        Title["display_title"]
        Short["short_title"]
        Meta["metadata"]
        Conf["confidence"]
    end

    Input --> P1
    P1 -->|match| Result
    P1 -->|no match| P2
    P2 -->|match| Result
    P2 -->|no match| P3
    P3 -->|match| Result
    P3 -->|no match| P4
    P4 -->|match| Result
    P4 -->|no match| Fallback["Fallback<br/>confidence: 0.1"]

    Fallback --> Result
```

---

## 8. Non-Functional Requirements

### 8.1 성능 요구사항

```mermaid
xychart-beta
    title "Performance Targets (ms)"
    x-axis ["Initial Load", "Page Nav", "Search", "Stream Start", "API P95"]
    y-axis "Time (ms)" 0 --> 3000
    bar [3000, 500, 200, 2000, 200]
```

| Metric | Target | Current |
|--------|--------|---------|
| Initial Load (LCP) | < 3s | - |
| Page Navigation | < 500ms | - |
| Search Response | < 200ms | - |
| Stream Start | < 2s | - |
| API P95 | < 200ms | < 100ms (in-memory) |

### 8.2 확장성

```mermaid
flowchart LR
    subgraph Current["Current (v1)"]
        Single["Single Server"]
        NAS1["NAS 18TB"]
    end

    subgraph Future["Future (v2)"]
        LB["Load Balancer"]
        S1["Server 1"]
        S2["Server 2"]
        S3["Server N"]
        NAS2["NAS Cluster"]
        CDN["CDN<br/>(Optional)"]
    end

    LB --> S1
    LB --> S2
    LB --> S3
    S1 --> NAS2
    S2 --> NAS2
    S3 --> NAS2
    CDN --> LB
```

### 8.3 브라우저 지원

| Browser | Version | Notes |
|---------|---------|-------|
| Chrome | Latest 2 | Primary |
| Firefox | Latest 2 | Supported |
| Safari | Latest 2 | Supported |
| Edge | Latest 2 | Supported |

### 8.4 반응형 브레이크포인트

```mermaid
gantt
    title Responsive Breakpoints
    dateFormat X
    axisFormat %s

    section Layout
    Mobile           :0, 640
    Tablet           :640, 1024
    Desktop          :1024, 1920
    Large Desktop    :1920, 2560
```

| Device | Width | Grid Columns |
|--------|-------|--------------|
| Mobile | < 640px | 1-2 |
| Tablet | 640px - 1024px | 3-4 |
| Desktop | > 1024px | 5-6 |

---

## 9. Security

### 9.1 인증 플로우

```mermaid
flowchart TB
    subgraph Client
        Token["JWT Token<br/>(localStorage)"]
    end

    subgraph Server
        API["API Gateway"]
        Auth["Auth Block"]

        subgraph Validation
            V1["Token Present?"]
            V2["Token Valid?"]
            V3["Token Expired?"]
            V4["User Active?"]
            V5["Admin Required?"]
        end
    end

    Token --> API
    API --> V1
    V1 -->|No| Reject1["401 Unauthorized"]
    V1 -->|Yes| V2
    V2 -->|No| Reject2["401 Invalid Token"]
    V2 -->|Yes| V3
    V3 -->|Yes| Reject3["401 Token Expired"]
    V3 -->|No| V4
    V4 -->|No| Reject4["403 User Inactive"]
    V4 -->|Yes| V5
    V5 -->|Admin Req & Not Admin| Reject5["403 Admin Required"]
    V5 -->|OK| Allow["Request Allowed"]
```

### 9.2 보안 체크리스트

| Category | Requirement | Status |
|----------|-------------|--------|
| **Authentication** | JWT Token | Planned |
| | Token Expiry (24h) | Planned |
| | Refresh Token | Planned |
| **Authorization** | Role-based (User/Admin) | Implemented |
| | Route Protection | Implemented |
| **Data** | Password Hashing (bcrypt) | Implemented |
| | SQL Injection Prevention | Implemented |
| | XSS Prevention | Planned |
| **Transport** | HTTPS | Planned |
| | CORS Policy | Implemented |
| **Rate Limiting** | Stream Limit (3/user) | Implemented |
| | Global Limit (20) | Implemented |

---

## 10. Tech Stack Summary

### 10.1 Frontend

```mermaid
flowchart LR
    subgraph Framework
        Next["Next.js 14<br/>App Router"]
    end

    subgraph UI
        Shadcn["shadcn/ui"]
        Tailwind["Tailwind CSS"]
        Radix["Radix UI"]
    end

    subgraph State
        Zustand["Zustand"]
        Query["TanStack Query"]
    end

    subgraph Forms
        RHF["React Hook Form"]
        Zod["Zod"]
    end

    subgraph Video
        Player["ReactPlayer"]
    end

    Next --> Shadcn
    Shadcn --> Radix
    Shadcn --> Tailwind
    Next --> State
    Next --> Forms
    Next --> Player
```

### 10.2 Backend

```mermaid
flowchart LR
    subgraph Core
        FastAPI["FastAPI<br/>Python 3.12"]
        Uvicorn["Uvicorn<br/>ASGI"]
    end

    subgraph Data
        SQLAlchemy["SQLAlchemy 2.0"]
        Asyncpg["asyncpg"]
        Pydantic["Pydantic 2.x"]
    end

    subgraph Infra
        Docker["Docker Compose"]
        Redis["Redis 7"]
        PostgreSQL["PostgreSQL 16"]
        MeiliSearch["MeiliSearch 1.6"]
    end

    FastAPI --> Uvicorn
    FastAPI --> Data
    Data --> Infra
```

### 10.3 Dependency Table

| Layer | Package | Version | Purpose |
|-------|---------|---------|---------|
| **Frontend** | next | 14.2.0 | React Framework |
| | react | 18.3.0 | UI Library |
| | @tanstack/react-query | 5.50.0 | Data Fetching |
| | zustand | 4.5.0 | State Management |
| | react-hook-form | 7.52.0 | Form Handling |
| | zod | 3.23.0 | Validation |
| | react-player | 2.16.0 | Video Player |
| | tailwindcss | 3.4.4 | Styling |
| **Backend** | fastapi | 0.115.0 | Web Framework |
| | uvicorn | 0.32.0 | ASGI Server |
| | sqlalchemy | 2.0.0 | ORM |
| | asyncpg | 0.30.0 | PostgreSQL Driver |
| | redis | 5.2.0 | Cache Client |
| | pydantic | 2.10.0 | Data Validation |
| | bcrypt | 4.2.0 | Password Hashing |
| **DevOps** | docker | - | Containerization |
| | postgresql | 16-alpine | Database |
| | redis | 7-alpine | Cache |
| | meilisearch | 1.6 | Search Engine |

---

## 11. Milestones

### 11.1 개발 로드맵

```mermaid
gantt
    title WSOPTV Development Roadmap
    dateFormat YYYY-MM-DD

    section Phase 1: Core
    Project Setup          :done, p1-1, 2024-12-01, 3d
    Auth Block             :done, p1-2, after p1-1, 5d
    Orchestration          :done, p1-3, after p1-2, 3d
    Content Block          :done, p1-4, after p1-3, 4d

    section Phase 2: Features
    Flat Catalog (F)       :done, p2-1, 2024-12-10, 3d
    Title Generator (G)    :done, p2-2, after p2-1, 3d
    Stream Block           :done, p2-3, after p2-2, 4d
    Search Block           :active, p2-4, after p2-3, 3d

    section Phase 3: Frontend
    UI Framework Setup     :p3-1, 2024-12-16, 2d
    Auth Pages             :p3-2, after p3-1, 3d
    Browse Page            :p3-3, after p3-2, 4d
    Video Player           :p3-4, after p3-3, 4d

    section Phase 4: Admin
    Admin Dashboard        :p4-1, after p3-4, 3d
    User Management        :p4-2, after p4-1, 2d
    Stream Monitor         :p4-3, after p4-2, 2d

    section Phase 5: Polish
    E2E Testing            :p5-1, after p4-3, 3d
    Performance Opt        :p5-2, after p5-1, 2d
    Documentation          :p5-3, after p5-2, 2d
```

### 11.2 Phase 상세

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| **Phase 1: Core** | Auth, Orchestration, Content | 2주 | - |
| **Phase 2: Features** | Catalog, Title, Stream, Search | 2주 | Phase 1 |
| **Phase 3: Frontend** | UI Setup, Auth, Browse, Player | 2주 | Phase 2 |
| **Phase 4: Admin** | Dashboard, Users, Streams | 1주 | Phase 3 |
| **Phase 5: Polish** | E2E, Performance, Docs | 1주 | Phase 4 |

---

## 12. Risk Assessment

### 12.1 위험 매트릭스

```mermaid
quadrantChart
    title Risk Assessment Matrix
    x-axis Low Impact --> High Impact
    y-axis Low Probability --> High Probability
    quadrant-1 Monitor
    quadrant-2 High Priority
    quadrant-3 Low Priority
    quadrant-4 Medium Priority

    "HTTP Range 호환성": [0.7, 0.6]
    "NAS 연결 실패": [0.8, 0.3]
    "동시 스트림 과부하": [0.6, 0.4]
    "진행률 동기화 지연": [0.3, 0.5]
    "제목 파싱 오류": [0.4, 0.6]
    "브라우저 비호환": [0.2, 0.3]
```

### 12.2 위험 대응

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| HTTP Range 호환성 | High | Medium | ReactPlayer + HLS fallback |
| NAS 연결 실패 | High | Low | SSD L2 캐시, 재시도 로직 |
| 동시 스트림 과부하 | Medium | Medium | Rate limiting, queue |
| 진행률 동기화 지연 | Low | Medium | Debouncing, localStorage backup |
| 제목 파싱 오류 | Medium | Medium | 수동 검토 UI, fallback |
| 브라우저 비호환 | Low | Low | Feature detection, polyfills |

---

## 13. Success Metrics

### 13.1 KPI

| Metric | Target | Measurement |
|--------|--------|-------------|
| **User Adoption** | 50+ active users | Weekly Active Users |
| **Content Engagement** | 70% completion rate | Average watch percentage |
| **System Reliability** | 99.5% uptime | Monthly availability |
| **Performance** | < 2s stream start | P95 latency |
| **Admin Efficiency** | < 24h approval time | Average approval time |

### 13.2 모니터링

```mermaid
flowchart LR
    subgraph Metrics["Metrics Collection"]
        API["API Latency"]
        Stream["Stream Health"]
        Cache["Cache Hit Rate"]
        Error["Error Rate"]
    end

    subgraph Dashboard["Admin Dashboard"]
        Users["Active Users"]
        Streams["Active Streams"]
        System["System Health"]
    end

    subgraph Alerts["Alerts"]
        Slack["Slack/Discord"]
        Email["Email"]
    end

    Metrics --> Dashboard
    Dashboard --> Alerts
```

---

## 14. Appendix

### A. Environment Variables

```env
# Backend
REDIS_URL=redis://localhost:6380/0
DATABASE_URL=postgresql://wsoptv:wsoptv@localhost:5434/wsoptv
MEILISEARCH_URL=http://localhost:7701
MEILISEARCH_API_KEY=masterKey
NAS_MOUNT_PATH=/mnt/nas
SSD_CACHE_PATH=/mnt/ssd

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8002
```

### B. Docker Ports

| Service | Internal | External | Description |
|---------|----------|----------|-------------|
| app | 8000 | 8002 | FastAPI Backend |
| redis | 6379 | 6380 | L1 Cache |
| postgres | 5432 | 5434 | Metadata Store |
| meilisearch | 7700 | 7701 | Search Engine |
| frontend | 3000 | 3000 | Next.js Dev |

### C. References

| Document | Location |
|----------|----------|
| Frontend UI PRD | `tasks/prds/0001-prd-frontend-ui.md` |
| Flat Catalog PRD | `tasks/prds/0002-prd-flat-catalog-title-generator.md` |
| Frontend README | `frontend/README.md` |
| Backend CLAUDE.md | `CLAUDE.md` |
| Block Docs | `docs/blocks/` |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2024-12-15 | Claude Code | Initial complete PRD with Mermaid diagrams |
