# 01. System Architecture

*← [README](./README.md) | [02-blocks.md](./02-blocks.md) →*

---

## 1. High-Level Architecture

### 1.1 System Overview

```mermaid
flowchart TB
    subgraph Client["Client Tier"]
        Browser["Web Browser<br/>━━━━━━━━━━━━━━━━━━━━<br/>Next.js 14<br/>React 18<br/>TypeScript"]
    end

    subgraph API["API Gateway"]
        FastAPI["FastAPI Server<br/>━━━━━━━━━━━━━━━━━━━━<br/>Port 8002<br/>ASGI (Uvicorn)<br/>CORS Enabled"]
    end

    subgraph Orchestration["Orchestration Layer"]
        MessageBus["MessageBus<br/>━━━━━━━━━━━━━━━━━━━━<br/>Pub/Sub Pattern<br/>Async Handlers<br/>Singleton"]
        Registry["BlockRegistry<br/>━━━━━━━━━━━━━━━━━━━━<br/>Lifecycle Mgmt<br/>Dependency Order<br/>Health Check"]
        Contract["Contract<br/>━━━━━━━━━━━━━━━━━━━━<br/>Version Compat<br/>Schema Validation<br/>provides/requires"]
    end

    subgraph Blocks["Block Layer (9 Blocks)"]
        subgraph L0["Wave 1 (L0) - No Dependencies"]
            Auth["auth"]
            Cache["cache"]
            TitleGen["title_generator"]
        end

        subgraph L1["Wave 2 (L1) - L0 Dependencies"]
            Content["content"]
            Search["search"]
            Worker["worker"]
            Catalog["flat_catalog"]
        end

        subgraph L2["Wave 3 (L2) - Full Dependencies"]
            Stream["stream"]
            Admin["admin"]
        end
    end

    subgraph Infrastructure["Infrastructure Tier (Docker)"]
        Redis["Redis 7<br/>━━━━━━━━━━━━━━━━━━━━<br/>Port: 6380<br/>L1 Cache<br/>512MB maxmemory"]
        PostgreSQL["PostgreSQL 16<br/>━━━━━━━━━━━━━━━━━━━━<br/>Port: 5434<br/>Metadata Store<br/>Alpine"]
        MeiliSearch["MeiliSearch v1.6<br/>━━━━━━━━━━━━━━━━━━━━<br/>Port: 7701<br/>Full-text Search<br/>Development Mode"]
    end

    subgraph Storage["Storage Tier"]
        NAS["NAS Server<br/>━━━━━━━━━━━━━━━━━━━━<br/>SMB: 10.10.100.122<br/>Windows: Z:\\ARCHIVE<br/>18TB+ Archive"]
        SSD["SSD Cache<br/>━━━━━━━━━━━━━━━━━━━━<br/>500GB Capacity<br/>LRU Policy<br/>Hot Content"]
    end

    Browser --> FastAPI
    FastAPI --> Orchestration
    Orchestration --> Blocks

    L0 --> Redis
    L1 --> PostgreSQL
    L1 --> MeiliSearch
    L2 --> NAS
    L2 --> SSD

    MessageBus -.-> L0
    MessageBus -.-> L1
    MessageBus -.-> L2
```

### 1.2 Layer Responsibilities

| Layer | Responsibility | Components |
|-------|---------------|------------|
| **Client** | UI 렌더링, 사용자 인터랙션 | Next.js, React, Tailwind |
| **API Gateway** | 라우팅, CORS, 인증 | FastAPI, Uvicorn |
| **Orchestration** | 블럭 조율, 메시징, 의존성 | MessageBus, Registry, Contract |
| **Block** | 비즈니스 로직, 도메인 처리 | 9개 독립 블럭 |
| **Infrastructure** | 데이터 저장, 캐싱, 검색 | Redis, PostgreSQL, MeiliSearch |
| **Storage** | 원본 파일 저장, 핫 캐싱 | NAS, SSD |

---

## 2. Network Topology

### 2.1 Development Environment

```mermaid
flowchart LR
    subgraph Internet["Internet"]
        User["👤 User<br/>Browser"]
    end

    subgraph LocalMachine["Local Machine (Windows)"]
        subgraph Docker["Docker Desktop"]
            Redis["redis<br/>━━━━━━━━━━<br/>6380:6379"]
            PG["postgres<br/>━━━━━━━━━━<br/>5434:5432"]
            Meili["meilisearch<br/>━━━━━━━━━━<br/>7701:7700"]
        end

        subgraph LocalDev["Local Development"]
            Frontend["next dev<br/>━━━━━━━━━━<br/>3000"]
            Backend["uvicorn<br/>━━━━━━━━━━<br/>8002"]
        end
    end

    subgraph NetworkDrive["Network Storage"]
        NAS["NAS<br/>━━━━━━━━━━<br/>Z:\\ARCHIVE<br/>SMB Mount"]
    end

    User --> Frontend
    Frontend --> Backend
    Backend --> Docker
    Backend --> NAS
```

### 2.2 Port Mapping

| Service | Container Port | Host Port | Protocol |
|---------|---------------|-----------|----------|
| FastAPI Backend | 8000 | 8002 | HTTP |
| Redis | 6379 | 6380 | TCP |
| PostgreSQL | 5432 | 5434 | TCP |
| MeiliSearch | 7700 | 7701 | HTTP |
| Next.js Frontend | 3000 | 3000 | HTTP |

### 2.3 Docker Network

```mermaid
flowchart TB
    subgraph DockerNetwork["wsoptv-v2-network (bridge)"]
        direction LR
        Redis["redis<br/>wsoptv-v2-redis"]
        PG["postgres<br/>wsoptv-v2-postgres"]
        Meili["meilisearch<br/>wsoptv-v2-meilisearch"]
    end

    subgraph HostNetwork["Host Network"]
        Backend["Backend (8002)"]
        Frontend["Frontend (3000)"]
    end

    Backend --> Redis
    Backend --> PG
    Backend --> Meili
    Frontend --> Backend
```

---

## 3. Data Flow Patterns

### 3.1 Request-Response Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Block
    participant DB

    Client->>FastAPI: HTTP Request
    FastAPI->>FastAPI: Route matching
    FastAPI->>FastAPI: Auth middleware
    FastAPI->>Block: Service call
    Block->>DB: Query
    DB-->>Block: Result
    Block-->>FastAPI: Response model
    FastAPI-->>Client: JSON Response
```

### 3.2 Event-Driven Flow (MessageBus)

```mermaid
sequenceDiagram
    participant BlockA as Block A (Publisher)
    participant Bus as MessageBus
    participant BlockB as Block B (Subscriber)
    participant BlockC as Block C (Subscriber)

    Note over BlockA,BlockC: Asynchronous Event Flow

    BlockA->>Bus: publish("event.type", message)
    Bus->>Bus: Find subscribers

    par Parallel Delivery
        Bus->>BlockB: handler(message)
        BlockB-->>Bus: ACK
    and
        Bus->>BlockC: handler(message)
        BlockC-->>Bus: ACK
    end

    Note over Bus: Error Isolation per Handler
```

### 3.3 Request-Response via MessageBus

```mermaid
sequenceDiagram
    participant Requester
    participant Bus as MessageBus
    participant Handler

    Requester->>Bus: request_response(channel, msg, timeout=5s)
    Bus->>Handler: handler(request)

    alt Success
        Handler->>Bus: publish(channel.response.{correlation_id}, response)
        Bus-->>Requester: response
    else Timeout
        Bus-->>Requester: None
    end
```

---

## 4. Caching Architecture

### 4.1 4-Tier Cache System

```mermaid
flowchart TB
    subgraph Request["Client Request"]
        User["👤 User"]
    end

    subgraph L1["L1: Redis (Metadata Cache)"]
        Redis["Redis 7<br/>━━━━━━━━━━━━━━━━━━━━<br/>Session: 24h TTL<br/>Metadata: 10min TTL<br/>Search: 5min TTL"]
    end

    subgraph L2["L2: SSD (Hot Content Cache)"]
        SSD["Local SSD<br/>━━━━━━━━━━━━━━━━━━━━<br/>Capacity: 500GB<br/>Policy: LRU Eviction<br/>Threshold: 5+ views/7days"]
    end

    subgraph L3["L3: Rate Limiter"]
        Limiter["Token Bucket<br/>━━━━━━━━━━━━━━━━━━━━<br/>Global: 20 concurrent<br/>Per User: 3 concurrent<br/>Refill: on stream end"]
    end

    subgraph L4["L4: NAS (Origin)"]
        NAS["NAS Server<br/>━━━━━━━━━━━━━━━━━━━━<br/>18TB+ Archive<br/>SMB Protocol<br/>Windows: Z:\\ARCHIVE"]
    end

    User --> Redis
    Redis -->|"Cache Miss"| SSD
    SSD -->|"Cache Miss"| Limiter
    Limiter -->|"Rate OK"| NAS

    NAS -.->|"Hot Content"| SSD
    SSD -.->|"Metadata"| Redis

    style L1 fill:#e3f2fd
    style L2 fill:#fff3e0
    style L3 fill:#fce4ec
    style L4 fill:#e8f5e9
```

### 4.2 Cache Key Patterns

| Cache Type | Key Pattern | TTL | Example |
|------------|-------------|-----|---------|
| **Session** | `session:{user_id}` | 24h | `session:550e8400-e29b-41d4-a716-446655440000` |
| **Catalog Item** | `catalog:{item_id}` | 10min | `catalog:item-123` |
| **Search Results** | `search:{hash(query)}` | 5min | `search:a1b2c3d4` |
| **Progress** | `progress:{user_id}:{item_id}` | 1h | `progress:u1:i1` |
| **Dashboard Stats** | `stats:dashboard` | 1min | `stats:dashboard` |
| **SSD Chunk** | `hot:{item_id}:chunk:{n}` | 7d | `hot:i1:chunk:0` |

---

## 5. Technology Decisions

### 5.1 Frontend Stack

| Technology | Version | Rationale |
|------------|---------|-----------|
| **Next.js** | 14.2.0 | App Router, SSR/SSG, 최적화된 빌드 |
| **React** | 18.3.0 | Concurrent features, Suspense |
| **TypeScript** | 5.5.0 | 타입 안정성, IDE 지원 |
| **Tailwind CSS** | 3.4.4 | Utility-first, 빠른 스타일링 |
| **shadcn/ui** | - | Accessible, 커스터마이징 용이 |
| **Zustand** | 4.5.0 | 경량 상태 관리 |
| **TanStack Query** | 5.50.0 | 서버 상태 캐싱/동기화 |
| **React Player** | 2.16.0 | HTTP Range 지원 |

### 5.2 Backend Stack

| Technology | Version | Rationale |
|------------|---------|-----------|
| **FastAPI** | 0.115.0 | 비동기, 타입 힌트, OpenAPI 자동 생성 |
| **Python** | 3.12 | 최신 기능, 성능 개선 |
| **Uvicorn** | 0.32.0 | ASGI 서버, 고성능 |
| **SQLAlchemy** | 2.0.0 | ORM, 비동기 지원 |
| **asyncpg** | 0.30.0 | PostgreSQL async driver |
| **Pydantic** | 2.10.0 | 데이터 검증, 직렬화 |
| **bcrypt** | 4.2.0 | 패스워드 해싱 |
| **redis-py** | 5.2.0 | Redis 클라이언트 |

### 5.3 Infrastructure

| Technology | Version | Rationale |
|------------|---------|-----------|
| **PostgreSQL** | 16-alpine | 메타데이터, 사용자, 진행률 저장 |
| **Redis** | 7-alpine | 세션, 캐시, Rate limiting |
| **MeiliSearch** | 1.6 | 전문 검색, 자동완성 |
| **Docker Compose** | - | 개발 환경 일관성 |

---

## 6. Scalability Considerations

### 6.1 Current vs Future

```mermaid
flowchart LR
    subgraph Current["Current (v1)"]
        Single["Single Server<br/>━━━━━━━━━━━━━━━━<br/>FastAPI 1 instance<br/>Docker Infra<br/>NAS 18TB"]
    end

    subgraph Future["Future (v2)"]
        LB["Load Balancer"]
        S1["Server 1"]
        S2["Server 2"]
        S3["Server N"]
        NASCluster["NAS Cluster"]
        CDN["CDN (Optional)"]
    end

    LB --> S1
    LB --> S2
    LB --> S3
    S1 --> NASCluster
    S2 --> NASCluster
    S3 --> NASCluster
    CDN --> LB
```

### 6.2 Scaling Strategy

| Component | Horizontal | Vertical | Notes |
|-----------|------------|----------|-------|
| **FastAPI** | ✅ Stateless | ✅ | Load balancer required |
| **Redis** | ⚠️ Cluster | ✅ | Session affinity needed |
| **PostgreSQL** | ⚠️ Replica | ✅ | Read replicas for queries |
| **MeiliSearch** | ⚠️ Sharding | ✅ | Single instance sufficient |
| **NAS** | ✅ | ✅ | Multiple mount points |

---

## Related Files

| File | Purpose |
|------|---------|
| `src/main.py` | FastAPI 앱, 블럭 등록, 라우터 |
| `src/orchestration/message_bus.py` | Pub/Sub 메시지 버스 |
| `src/orchestration/registry.py` | 블럭 등록/의존성 관리 |
| `docker-compose.yml` | 인프라 서비스 정의 |

---

*← [README](./README.md) | [02-blocks.md](./02-blocks.md) →*
