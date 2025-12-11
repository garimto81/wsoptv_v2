# PRD: Orchestration Layer

**Version**: 1.0.0
**Date**: 2025-12-11
**Block**: Orchestration (Master)
**Status**: Draft

---

## 1. Overview

오케스트레이션 레이어는 모든 블럭을 조율하는 **마스터 컨트롤러**입니다.
각 블럭은 독립적으로 동작하지만, 오케스트레이션을 통해 상호 정보를 교환합니다.

### 1.1 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **블럭 독립성** | 각 블럭은 자체 PRD, 테스트, 에이전트를 가짐 |
| **중앙 조율** | 오케스트레이션만 블럭 간 통신 중재 |
| **계약 기반** | 블럭 간 인터페이스는 명시적 계약으로 정의 |
| **장애 격리** | 한 블럭 실패가 다른 블럭에 전파되지 않음 |

### 1.2 문제 해결 목표

```
[기존 문제]
Claude 1개 → 전체 코드베이스 → 컨텍스트 폭발 → 망각 → 코드 오염

[해결책]
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                       │
│                   (컨텍스트 최소화)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  Auth   │  │ Content │  │ Stream  │  │  Admin  │       │
│  │  Block  │  │  Block  │  │  Block  │  │  Block  │       │
│  │         │  │         │  │         │  │         │       │
│  │ Agent A │  │ Agent B │  │ Agent C │  │ Agent D │       │
│  │ PRD-A   │  │ PRD-B   │  │ PRD-C   │  │ PRD-D   │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│       │            │            │            │              │
│       └────────────┴─────┬──────┴────────────┘              │
│                          │                                   │
│                    [Message Bus]                             │
│                          │                                   │
│                   Orchestration                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘

→ 각 에이전트는 자기 블럭만 집중 → 컨텍스트 유지 → 오염 방지
```

---

## 2. Architecture

### 2.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WSOPTV Block Architecture                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                      ┌─────────────────────┐                            │
│                      │    Orchestrator     │                            │
│                      │  ┌───────────────┐  │                            │
│                      │  │ Message Bus   │  │                            │
│                      │  │ (Redis Pub/Sub)│  │                            │
│                      │  └───────────────┘  │                            │
│                      │  ┌───────────────┐  │                            │
│                      │  │ Block Registry│  │                            │
│                      │  └───────────────┘  │                            │
│                      │  ┌───────────────┐  │                            │
│                      │  │ Health Monitor│  │                            │
│                      │  └───────────────┘  │                            │
│                      └──────────┬──────────┘                            │
│                                 │                                        │
│         ┌───────────┬───────────┼───────────┬───────────┐              │
│         │           │           │           │           │              │
│         ▼           ▼           ▼           ▼           ▼              │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │   Auth   │ │ Content  │ │  Stream  │ │  Cache   │ │  Admin   │   │
│   │  Block   │ │  Block   │ │  Block   │ │  Block   │ │  Block   │   │
│   ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤   │
│   │ Agent    │ │ Agent    │ │ Agent    │ │ Agent    │ │ Agent    │   │
│   │ PRD      │ │ PRD      │ │ PRD      │ │ PRD      │ │ PRD      │   │
│   │ Tests    │ │ Tests    │ │ Tests    │ │ Tests    │ │ Tests    │   │
│   │ API      │ │ API      │ │ API      │ │ API      │ │ API      │   │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Block List

| Block ID | 이름 | 책임 | 전담 에이전트 |
|----------|------|------|---------------|
| `auth` | Auth Block | 인증, 인가, 사용자 관리 | `auth-agent` |
| `content` | Content Block | 콘텐츠 CRUD, 카탈로그 | `content-agent` |
| `stream` | Stream Block | 비디오 스트리밍, Range 처리 | `stream-agent` |
| `cache` | Cache Block | 4-Tier 캐시 관리 | `cache-agent` |
| `admin` | Admin Block | 관리자 대시보드, 모니터링 | `admin-agent` |
| `search` | Search Block | MeiliSearch 연동, 검색 | `search-agent` |
| `worker` | Worker Block | 백그라운드 작업 (썸네일 등) | `worker-agent` |

---

## 3. Orchestrator Components

### 3.1 Message Bus

블럭 간 통신을 위한 Redis Pub/Sub 기반 메시지 버스:

```python
# app/orchestration/message_bus.py

class MessageBus:
    """블럭 간 메시지 전달"""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.subscribers: dict[str, list[Callable]] = {}

    async def publish(self, channel: str, message: BlockMessage):
        """메시지 발행"""
        await self.redis.publish(
            f"block:{channel}",
            message.model_dump_json()
        )

    async def subscribe(self, channel: str, handler: Callable):
        """메시지 구독"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"block:{channel}")

        async for msg in pubsub.listen():
            if msg["type"] == "message":
                data = BlockMessage.model_validate_json(msg["data"])
                await handler(data)

class BlockMessage(BaseModel):
    """블럭 간 메시지 형식"""
    source_block: str          # 발신 블럭
    target_block: str | None   # 수신 블럭 (None = broadcast)
    event_type: str            # 이벤트 타입
    payload: dict              # 데이터
    correlation_id: str        # 추적 ID
    timestamp: datetime
```

### 3.2 Block Registry

블럭 등록 및 상태 관리:

```python
# app/orchestration/registry.py

class BlockRegistry:
    """블럭 등록 및 상태 관리"""

    def __init__(self):
        self.blocks: dict[str, BlockInfo] = {}

    def register(self, block: BlockInfo):
        """블럭 등록"""
        self.blocks[block.id] = block
        logger.info(f"Block registered: {block.id}")

    def get_block(self, block_id: str) -> BlockInfo | None:
        return self.blocks.get(block_id)

    def get_all_blocks(self) -> list[BlockInfo]:
        return list(self.blocks.values())

    def is_healthy(self, block_id: str) -> bool:
        block = self.blocks.get(block_id)
        return block and block.status == BlockStatus.HEALTHY

class BlockInfo(BaseModel):
    id: str                    # 블럭 ID
    name: str                  # 블럭 이름
    version: str               # 버전
    status: BlockStatus        # 상태
    endpoints: list[str]       # 제공 엔드포인트
    dependencies: list[str]    # 의존 블럭
    health_url: str            # 헬스체크 URL

class BlockStatus(str, Enum):
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"
```

### 3.3 Health Monitor

블럭 헬스체크 및 장애 감지:

```python
# app/orchestration/health.py

class HealthMonitor:
    """블럭 헬스체크"""

    def __init__(self, registry: BlockRegistry, bus: MessageBus):
        self.registry = registry
        self.bus = bus
        self.check_interval = 30  # 초

    async def start(self):
        """헬스체크 루프 시작"""
        while True:
            await self._check_all_blocks()
            await asyncio.sleep(self.check_interval)

    async def _check_all_blocks(self):
        for block in self.registry.get_all_blocks():
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(block.health_url, timeout=5)
                    if resp.status_code == 200:
                        block.status = BlockStatus.HEALTHY
                    else:
                        block.status = BlockStatus.DEGRADED
            except Exception:
                block.status = BlockStatus.UNHEALTHY
                await self._notify_failure(block)

    async def _notify_failure(self, block: BlockInfo):
        """장애 알림"""
        await self.bus.publish("system", BlockMessage(
            source_block="orchestrator",
            target_block=None,
            event_type="block_unhealthy",
            payload={"block_id": block.id},
            correlation_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow()
        ))
```

---

## 4. Block Communication Patterns

### 4.1 Request-Response (동기)

```python
# Auth Block → Stream Block: 사용자 검증 요청

# Stream Block 내부
async def start_stream(content_id: str, token: str):
    # Auth Block에 검증 요청
    user = await orchestrator.request(
        target="auth",
        action="validate_token",
        payload={"token": token}
    )

    if not user:
        raise AuthError("Invalid token")

    # 스트리밍 시작
    ...
```

### 4.2 Event Publishing (비동기)

```python
# Content Block → 이벤트 발행 (구독자 모름)

async def add_content(content: Content):
    # 콘텐츠 저장
    await db.add(content)

    # 이벤트 발행 (Search, Cache 블럭이 구독 중)
    await orchestrator.publish(
        event="content_added",
        payload={"content_id": content.id, "title": content.title}
    )
```

### 4.3 Event Subscription

```python
# Search Block: content_added 이벤트 구독

@orchestrator.subscribe("content_added")
async def on_content_added(event: BlockMessage):
    # MeiliSearch 인덱스 업데이트
    await meilisearch.index("contents").add_documents([
        {
            "id": event.payload["content_id"],
            "title": event.payload["title"]
        }
    ])
```

---

## 5. Block Interface Contracts

### 5.1 Auth Block API

```python
# 다른 블럭이 Auth Block에 요청할 수 있는 API

class AuthBlockAPI:
    """Auth Block 인터페이스 계약"""

    async def validate_token(self, token: str) -> User | None:
        """토큰 검증 → 사용자 반환"""
        ...

    async def get_user(self, user_id: str) -> User | None:
        """사용자 ID로 조회"""
        ...

    async def check_permission(self, user_id: str, resource: str) -> bool:
        """권한 확인"""
        ...
```

### 5.2 Cache Block API

```python
class CacheBlockAPI:
    """Cache Block 인터페이스 계약"""

    async def get(self, key: str) -> Any | None:
        """캐시 조회"""
        ...

    async def set(self, key: str, value: Any, ttl: int = 600):
        """캐시 저장"""
        ...

    async def get_stream_path(self, content_id: str) -> Path:
        """스트리밍용 파일 경로 (SSD or NAS)"""
        ...

    async def acquire_stream_slot(self, user_id: str) -> tuple[bool, str]:
        """스트림 슬롯 획득"""
        ...
```

### 5.3 Contract Versioning

```python
# 계약 버전 관리

class ContractVersion:
    AUTH_V1 = "auth:v1"      # 현재 버전
    AUTH_V2 = "auth:v2"      # 다음 버전 (하위 호환)

    CACHE_V1 = "cache:v1"
    STREAM_V1 = "stream:v1"

# 블럭 등록 시 지원 계약 명시
block_info = BlockInfo(
    id="auth",
    contracts=["auth:v1", "auth:v2"]  # 두 버전 모두 지원
)
```

---

## 6. Error Handling & Fallback

### 6.1 Circuit Breaker

```python
# 블럭 장애 시 Circuit Breaker 패턴

class CircuitBreaker:
    def __init__(self, block_id: str, failure_threshold: int = 5):
        self.block_id = block_id
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.state = CircuitState.CLOSED
        self.last_failure = None

    async def call(self, func: Callable, fallback: Callable = None):
        if self.state == CircuitState.OPEN:
            if self._should_try_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                return await fallback() if fallback else None

        try:
            result = await func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            if fallback:
                return await fallback()
            raise
```

### 6.2 Fallback Strategies

| 블럭 장애 | Fallback 전략 |
|----------|--------------|
| Auth 장애 | 캐시된 세션 사용 (읽기 전용 모드) |
| Cache 장애 | DB 직접 조회 (성능 저하) |
| Search 장애 | PostgreSQL LIKE 검색 |
| Stream 장애 | 에러 메시지 반환 |
| Worker 장애 | 작업 큐에 보관, 복구 후 재처리 |

---

## 7. Development Workflow

### 7.1 블럭 개발 시 에이전트 규칙

```markdown
## Auth Block 전담 에이전트 규칙

1. **컨텍스트 제한**
   - `api/app/blocks/auth/` 디렉토리만 수정
   - 다른 블럭 코드 읽기 금지 (인터페이스만 참조)

2. **수정 가능 파일**
   - `api/app/blocks/auth/**/*`
   - `tests/blocks/auth/**/*`
   - `docs/blocks/01-auth.md`

3. **수정 불가 파일**
   - `api/app/blocks/*/` (다른 블럭)
   - `api/app/orchestration/` (오케스트레이터)

4. **통신 규칙**
   - 다른 블럭 호출 시 반드시 오케스트레이터 경유
   - 직접 import 금지
```

### 7.2 블럭 테스트 독립성

```python
# 각 블럭은 Mock으로 다른 블럭 대체

# tests/blocks/stream/test_stream_service.py

@pytest.fixture
def mock_auth_block():
    """Auth Block Mock"""
    mock = AsyncMock()
    mock.validate_token.return_value = User(id="user-1", status="active")
    return mock

@pytest.fixture
def mock_cache_block():
    """Cache Block Mock"""
    mock = AsyncMock()
    mock.get_stream_path.return_value = Path("/cache/content-1.mp4")
    mock.acquire_stream_slot.return_value = (True, "OK")
    return mock

async def test_start_stream(mock_auth_block, mock_cache_block):
    """스트림 시작 테스트 - 다른 블럭은 Mock"""
    stream_service = StreamService(
        auth=mock_auth_block,
        cache=mock_cache_block
    )

    result = await stream_service.start("content-1", "token-abc")

    assert result.status == "streaming"
    mock_auth_block.validate_token.assert_called_once_with("token-abc")
    mock_cache_block.acquire_stream_slot.assert_called_once()
```

---

## 8. Directory Structure

```
api/app/
├── orchestration/           # 오케스트레이션 레이어
│   ├── __init__.py
│   ├── orchestrator.py      # 메인 오케스트레이터
│   ├── message_bus.py       # 메시지 버스
│   ├── registry.py          # 블럭 레지스트리
│   ├── health.py            # 헬스 모니터
│   └── contracts/           # 블럭 간 계약
│       ├── auth.py
│       ├── cache.py
│       ├── stream.py
│       └── ...
│
├── blocks/                  # 블럭들
│   ├── auth/               # Auth Block
│   │   ├── __init__.py
│   │   ├── router.py       # API 엔드포인트
│   │   ├── service.py      # 비즈니스 로직
│   │   ├── models.py       # 데이터 모델
│   │   └── tests/          # 블럭 테스트
│   │
│   ├── content/            # Content Block
│   ├── stream/             # Stream Block
│   ├── cache/              # Cache Block
│   ├── admin/              # Admin Block
│   ├── search/             # Search Block
│   └── worker/             # Worker Block
│
└── main.py                  # 앱 진입점 (블럭 등록)

docs/blocks/
├── 00-orchestration.md     # 이 문서
├── 01-auth.md              # Auth Block PRD
├── 02-content.md           # Content Block PRD
├── 03-stream.md            # Stream Block PRD
├── 04-cache.md             # Cache Block PRD
├── 05-admin.md             # Admin Block PRD
├── 06-search.md            # Search Block PRD
└── 07-worker.md            # Worker Block PRD
```

---

## 9. Success Metrics

| Metric | Target | 측정 |
|--------|--------|------|
| 블럭 독립성 | 100% | 블럭 간 직접 import 0 |
| 에이전트 컨텍스트 | < 500줄 | 블럭당 코드 라인 |
| 장애 격리 | 100% | 한 블럭 장애 시 다른 블럭 정상 |
| 테스트 독립성 | 100% | Mock 없이 다른 블럭 호출 0 |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-11 | Claude Code | Initial draft |
