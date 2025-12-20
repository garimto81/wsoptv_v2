# WSOPTV - Technical Architecture PRD

**Version**: 2.0.0 | **Parent**: [00-master.md](./00-master.md) | **Updated**: 2025-12-20

---

## 1. System Overview

WSOPTV는 **9-Block 마이크로서비스 아키텍처**를 기반으로 설계된 VOD 스트리밍 플랫폼입니다.

### 1.1 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WSOPTV Platform Architecture                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐     │
│    │   Browser   │────────▶│  Frontend   │────────▶│   Backend   │     │
│    │   (User)    │         │  Next.js    │         │  FastAPI    │     │
│    └─────────────┘         └─────────────┘         └──────┬──────┘     │
│                                                           │             │
│                         ┌─────────────────────────────────┘             │
│                         │                                               │
│                         ▼                                               │
│         ┌───────────────────────────────────────────────────────────┐  │
│         │                 Orchestration Layer                        │  │
│         │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
│         │  │ MessageBus  │  │  Registry   │  │  Contracts  │        │  │
│         │  │ (Pub/Sub)   │  │  (Block)    │  │  (API)      │        │  │
│         │  └─────────────┘  └─────────────┘  └─────────────┘        │  │
│         └───────────────────────────────────────────────────────────┘  │
│                         │                                               │
│         ┌───────────────┼───────────────┬───────────────┐              │
│         │               │               │               │              │
│         ▼               ▼               ▼               ▼              │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐          │
│   │   Auth   │   │ Content  │   │  Stream  │   │  Cache   │          │
│   │  Block   │   │  Block   │   │  Block   │   │  Block   │          │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘          │
│         │               │               │               │              │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐          │
│   │  Search  │   │  Worker  │   │  Admin   │   │  Catalog │          │
│   │  Block   │   │  Block   │   │  Block   │   │  Block   │          │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | Next.js | 14 | App Router, SSR |
| **Frontend** | TypeScript | 5.x | Type Safety |
| **Frontend** | Tailwind CSS | 3.x | Styling |
| **Frontend** | shadcn/ui | latest | Component Library |
| **Backend** | FastAPI | 0.109+ | API Framework |
| **Backend** | Python | 3.12 | Runtime |
| **Database** | PostgreSQL | 16 | Primary Database |
| **Search** | MeiliSearch | 1.11 | Full-text Search |
| **Cache** | Redis | 7 | L1 Cache, Sessions |
| **Storage** | AWS S3 / NAS | - | Media Storage |

---

## 2. 9-Block Architecture

### 2.1 Block Hierarchy

```
Orchestration Layer: MessageBus (Pub/Sub) + BlockRegistry + Contracts

L0 (No dependencies):
├── auth            - 인증/인가
├── cache           - 4-Tier 캐싱
└── title_generator - 제목 생성

L1 (L0 dependencies):
├── content         - 콘텐츠 관리
├── search          - MeiliSearch 검색
├── worker          - 백그라운드 작업
└── flat_catalog    - Netflix형 카탈로그

L2 (Full dependencies):
├── stream          - HTTP Range 스트리밍
└── admin           - 관리자 대시보드
```

### 2.2 Block Overview

| Block ID | 이름 | 책임 | 의존성 |
|----------|------|------|--------|
| `auth` | Auth Block | 인증, 인가, 사용자 관리 | 없음 (L0) |
| `cache` | Cache Block | 4-Tier 캐시 시스템 관리 | 없음 (L0) |
| `title_generator` | Title Generator | 콘텐츠 제목 생성 | 없음 (L0) |
| `content` | Content Block | 콘텐츠 메타데이터 CRUD | auth, cache |
| `search` | Search Block | MeiliSearch 검색 | auth, content |
| `worker` | Worker Block | 썸네일 생성, 메타데이터 추출 | content, cache |
| `flat_catalog` | Catalog Block | Netflix형 카탈로그 | content |
| `stream` | Stream Block | HTTP Range 스트리밍 | auth, cache, content |
| `admin` | Admin Block | 관리자 대시보드 | 전체 |

### 2.3 Block 독립성 원칙

| 원칙 | 설명 |
|------|------|
| **블럭 독립성** | 각 블럭은 자체 PRD, 테스트, 서비스를 가짐 |
| **중앙 조율** | 오케스트레이션만 블럭 간 통신 중재 |
| **계약 기반** | 블럭 간 인터페이스는 명시적 계약으로 정의 |
| **장애 격리** | 한 블럭 실패가 다른 블럭에 전파되지 않음 |

### 2.4 블럭 간 통신 규칙

```python
# ❌ 금지: 다른 블럭 직접 import
from src.blocks.auth.service import AuthService  # NEVER

# ✅ 허용: 오케스트레이션 경유
from src.orchestration.message_bus import MessageBus

# 이벤트 발행
await message_bus.publish("content.updated", {"content_id": "123"})

# 이벤트 구독
@message_bus.subscribe("auth.user_created")
async def handle_user_created(event):
    ...
```

---

## 3. Orchestration Layer

### 3.1 MessageBus (Redis Pub/Sub)

블럭 간 이벤트 기반 통신을 관리합니다.

```python
class MessageBus:
    """Redis Pub/Sub 기반 메시지 버스"""

    async def publish(self, channel: str, message: dict) -> None:
        """이벤트 발행 (예: 'content.updated')"""
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str, handler: Callable) -> None:
        """이벤트 구독"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        async for message in pubsub.listen():
            await handler(message)
```

### 3.2 이벤트 채널 네이밍

| 채널 패턴 | 설명 | 예시 |
|-----------|------|------|
| `{block}.{event}` | 블럭 이벤트 | `content.updated` |
| `{block}.{action}.{result}` | 액션 결과 | `auth.login.success` |

### 3.3 BlockRegistry

블럭 등록 및 상태 관리를 담당합니다.

```python
class BlockRegistry:
    """블럭 레지스트리"""

    def register(self, block_id: str, block: Block) -> None:
        """블럭 등록"""
        self.blocks[block_id] = block

    def get_block(self, block_id: str) -> Block:
        """블럭 조회"""
        return self.blocks.get(block_id)

    def health_check(self) -> dict[str, bool]:
        """전체 블럭 상태 확인"""
        return {bid: b.is_healthy() for bid, b in self.blocks.items()}
```

---

## 4. 4-Tier Cache System

### 4.1 Cache Hierarchy

```
Request → [L1: Redis] → [L2: SSD] → [L3: Rate Limiter] → [L4: Storage]
               │             │              │                  │
              hit           hit           pass               Response
               │             │              │
           Response      Response     [L4: NAS/S3]
```

### 4.2 Tier Details

| Tier | 저장소 | 용량 | TTL | 용도 |
|:----:|--------|------|-----|------|
| **L1** | Redis | 2GB | 10분~24시간 | 메타데이터, 세션 |
| **L2** | SSD | 500GB | LRU | Hot Content 캐싱 |
| **L3** | Rate Limiter | - | 실시간 | 동시 접속 제한 |
| **L4** | NAS/S3 | 17.96TB | 영구 | 원본 콘텐츠 |

### 4.3 L1: Redis Cache

```python
# 캐시 키 패턴
Key Patterns:
├── "content:{id}"           # 콘텐츠 메타데이터 (TTL: 10분)
├── "home:rows"              # 홈페이지 Row (TTL: 5분)
├── "user:{id}:session"      # 사용자 세션 (TTL: 24시간)
├── "user:{id}:progress:{cid}" # 시청 진행률 (TTL: 7일)
├── "stream:active"          # 활성 스트림 카운트
└── "content:views:{id}:7d"  # 7일간 조회수
```

### 4.4 L2: SSD Hot Cache

```python
# Hot Content 기준
- 7일 내 5회 이상 조회 → 자동 캐싱
- LRU 정책으로 공간 관리
- 95% 도달 시 가장 오래된 콘텐츠 삭제

# 디렉토리 구조
/cache/hot/
├── content-001.mp4
├── content-002.mp4
└── ...
```

### 4.5 L3: Rate Limiter

| 제한 유형 | 값 | 설명 |
|----------|---|------|
| 전체 동시 스트림 | 100개 | 서버 전체 제한 |
| 사용자당 동시 스트림 | 3개 | 개별 사용자 제한 |
| 대기열 크기 | 50 | 대기 중인 요청 |

---

## 5. API Design

### 5.1 API 구조

```
/api
├── /auth
│   ├── POST   /register     # 회원가입
│   ├── POST   /login        # 로그인
│   ├── POST   /logout       # 로그아웃
│   └── POST   /refresh      # 토큰 갱신
│
├── /contents
│   ├── GET    /             # 콘텐츠 목록
│   ├── GET    /{id}         # 콘텐츠 상세
│   └── GET    /{id}/hands   # Best Hands 목록
│
├── /home
│   └── GET    /             # 홈페이지 Row 데이터
│
├── /stream
│   ├── GET    /{id}         # 비디오 스트리밍
│   └── POST   /{id}/progress # 시청 진행률 저장
│
├── /search
│   └── GET    /             # 검색
│
└── /admin
    ├── GET    /dashboard    # 대시보드
    ├── GET    /users        # 사용자 관리
    └── GET    /contents     # 콘텐츠 관리
```

### 5.2 인증

| 항목 | 값 |
|------|---|
| 방식 | JWT (Access + Refresh) |
| Access Token TTL | 15분 |
| Refresh Token TTL | 7일 |
| 저장소 | Redis (블랙리스트) |

### 5.3 에러 응답

```json
{
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "Access token has expired",
    "details": {}
  }
}
```

---

## 6. Database Schema

### 6.1 Core Tables

```sql
-- 사용자
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    subscription_status VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 콘텐츠
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    duration_seconds INTEGER,
    file_path VARCHAR(1000) NOT NULL,
    thumbnail_path VARCHAR(1000),
    series_id UUID REFERENCES series(id),
    event_type VARCHAR(50),
    year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 시청 진행률
CREATE TABLE watch_progress (
    user_id UUID REFERENCES users(id),
    content_id UUID REFERENCES contents(id),
    progress_seconds INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, content_id)
);

-- Best Hands
CREATE TABLE best_hands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES contents(id),
    hand_index INTEGER NOT NULL,
    start_seconds INTEGER NOT NULL,
    end_seconds INTEGER NOT NULL,
    category VARCHAR(50),
    title VARCHAR(200),
    players TEXT[],
    pot_size DECIMAL
);
```

---

## 7. Infrastructure

### 7.1 개발 환경

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    ports: ["5434:5432"]
    environment:
      POSTGRES_USER: wsoptv
      POSTGRES_PASSWORD: wsoptv
      POSTGRES_DB: wsoptv

  redis:
    image: redis:7
    ports: ["6380:6379"]

  meilisearch:
    image: getmeili/meilisearch:v1.11
    ports: ["7701:7700"]
```

### 7.2 환경 변수

```env
# Database
DATABASE_URL=postgresql://wsoptv:wsoptv@localhost:5434/wsoptv

# Cache
REDIS_URL=redis://localhost:6380/0

# Search
MEILISEARCH_URL=http://localhost:7701
MEILISEARCH_MASTER_KEY=your-master-key

# Storage
NAS_MOUNT_PATH=Z:\ARCHIVE        # 개발 환경
AWS_S3_BUCKET=wsoptv-media       # 프로덕션 환경

# Auth
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 8. Monitoring & Logging

### 8.1 헬스체크

```python
# /api/health
{
    "status": "healthy",
    "blocks": {
        "auth": "healthy",
        "content": "healthy",
        "stream": "healthy",
        "cache": "healthy",
        "search": "healthy",
        "admin": "healthy"
    },
    "dependencies": {
        "postgres": "connected",
        "redis": "connected",
        "meilisearch": "connected"
    }
}
```

### 8.2 메트릭

| 메트릭 | 설명 |
|--------|------|
| `cache_hit_rate` | L1/L2 캐시 히트율 |
| `active_streams` | 현재 활성 스트림 수 |
| `request_latency` | API 응답 시간 |
| `error_rate` | 에러 발생률 |

---

## 9. Security

### 9.1 인증/인가

| 항목 | 구현 |
|------|------|
| 비밀번호 | bcrypt 해싱 |
| 토큰 | JWT (HS256) |
| RBAC | user, admin 역할 |
| Rate Limiting | IP당 100 req/min |

### 9.2 OWASP 대응

| 취약점 | 대응 |
|--------|------|
| SQL Injection | SQLAlchemy ORM |
| XSS | CSP 헤더, 입력 검증 |
| CSRF | SameSite Cookie |
| 인증 우회 | JWT 검증, 블랙리스트 |

---

## Document Index

### 블록별 상세 PRD

| 문서 | 설명 |
|------|------|
| [05-blocks/auth.md](./05-blocks/auth.md) | Auth Block 상세 |
| [05-blocks/content.md](./05-blocks/content.md) | Content Block 상세 |
| [05-blocks/stream.md](./05-blocks/stream.md) | Stream Block 상세 |
| [05-blocks/cache.md](./05-blocks/cache.md) | Cache Block 상세 |
| [05-blocks/search.md](./05-blocks/search.md) | Search Block 상세 |
| [05-blocks/admin.md](./05-blocks/admin.md) | Admin Block 상세 |
| [05-blocks/worker.md](./05-blocks/worker.md) | Worker Block 상세 |

---

*이전: [03-content-strategy.md](./03-content-strategy.md) | 메인: [00-master.md](./00-master.md)*
