# PRD: Cache Block

**Version**: 1.0.0
**Date**: 2025-12-11
**Block ID**: cache
**전담 에이전트**: cache-agent
**Status**: Draft

---

## 1. Block Overview

Cache Block은 4-Tier 캐시 시스템을 관리하여 콘텐츠 전송 성능을 최적화하고 네트워크 대역폭을 효율적으로 관리합니다.

### 1.1 책임 범위

| 책임 | 설명 |
|------|------|
| **L1 캐시 관리** | Redis 기반 메타데이터 및 세션 캐싱 |
| **L2 캐시 관리** | SSD 500GB Hot Content 캐싱 (LRU) |
| **L3 Rate Limiting** | 동시 스트리밍 접속 제한 관리 |
| **L4 Storage 관리** | NAS SMB 3.0 원본 콘텐츠 저장소 |
| **Hot Content 판단** | 조회 패턴 분석 및 자동 캐싱 |

### 1.2 핵심 원칙

```
[캐싱 전략]
┌─────────────────────────────────────────────────────┐
│                   Cache Hierarchy                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  L1: Redis (메타데이터)                             │
│  ├─ 세션 데이터 (TTL: 1시간)                        │
│  ├─ 콘텐츠 메타데이터 (TTL: 10분)                   │
│  └─ Hot Content 조회수 카운터                       │
│                                                      │
│  L2: SSD 500GB (Hot Content)                        │
│  ├─ 7일 내 5회+ 조회 → 자동 캐싱                    │
│  ├─ LRU 정책으로 공간 관리                          │
│  └─ 95% 도달 시 가장 오래된 콘텐츠 삭제             │
│                                                      │
│  L3: Rate Limiter                                   │
│  ├─ 동시 스트리밍 제한 (기본: 100명)                │
│  ├─ 사용자별 슬롯 할당                              │
│  └─ 대기열 관리                                     │
│                                                      │
│  L4: NAS SMB 3.0 (원본)                             │
│  ├─ 모든 콘텐츠 원본 저장                           │
│  ├─ Cold Content 직접 스트리밍                      │
│  └─ Hot Content 소스                                │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 1.3 독립성 보장

- **독립 실행**: 다른 블럭 장애 시에도 캐시 기능 유지
- **자체 판단**: Hot Content 여부를 자체 로직으로 결정
- **이벤트 기반**: 다른 블럭과의 통신은 이벤트 Pub/Sub만 사용

---

## 2. Agent Rules

### 2.1 컨텍스트 제한

```markdown
## Cache Agent 작업 규칙

1. **수정 가능 파일**
   - `api/app/blocks/cache/**/*`
   - `tests/blocks/cache/**/*`
   - `docs/blocks/04-cache.md`

2. **수정 불가 파일**
   - `api/app/blocks/*/` (다른 블럭)
   - `api/app/orchestration/` (오케스트레이터만 수정 가능)

3. **통신 규칙**
   - 다른 블럭 호출 시 오케스트레이터 경유 필수
   - 다른 블럭 코드 직접 import 금지
   - 인터페이스 계약 (`app/orchestration/contracts/`) 만 참조

4. **테스트 규칙**
   - 다른 블럭은 Mock 객체로 대체
   - Redis, SSD, NAS 의존성도 Mock 제공
```

### 2.2 에이전트 책임

| 책임 | 설명 |
|------|------|
| **캐시 로직** | 4-Tier 캐시 전략 구현 |
| **Hot 판단** | 조회 패턴 분석 및 자동 캐싱 트리거 |
| **공간 관리** | SSD 공간 모니터링 및 LRU 삭제 |
| **Rate Limit** | 동시 접속 제한 및 슬롯 관리 |
| **모니터링** | 캐시 히트율, 공간 사용률 추적 |

---

## 3. 4-Tier Cache Details

### 3.1 L1: Redis Cache

**목적**: 빠른 메타데이터 조회 및 세션 관리

```python
# L1 캐시 구조

# 세션 데이터
Key: "session:{session_id}"
Value: {
    "user_id": "user-123",
    "token": "jwt-token",
    "started_at": "2025-12-11T10:00:00Z"
}
TTL: 3600 (1시간)

# 콘텐츠 메타데이터
Key: "content:meta:{content_id}"
Value: {
    "title": "영화 제목",
    "duration": 7200,
    "size": 5368709120,
    "location": "nas" | "ssd"
}
TTL: 600 (10분)

# Hot Content 조회수 카운터
Key: "content:views:{content_id}:7d"
Value: 15  # 7일 내 조회수
TTL: 604800 (7일)
```

**운영 규칙**:
- 메모리 한계: 최대 2GB
- Eviction Policy: `allkeys-lru`
- 백업: Redis RDB (1시간마다)

### 3.2 L2: SSD Cache (500GB)

**목적**: Hot Content 고속 스트리밍

```python
# SSD 캐시 구조

# 디렉토리 구조
/mnt/ssd_cache/
├── content-1.mp4     # Hot Content
├── content-5.mp4
├── content-8.mp4
└── .cache_meta.db    # SQLite 메타데이터

# SQLite 메타데이터
CREATE TABLE cached_content (
    content_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    cached_at TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP NOT NULL,
    access_count INTEGER DEFAULT 0,
    INDEX idx_last_accessed (last_accessed)
);
```

**Hot Content 기준**:
```python
# 7일 내 5회 이상 조회 시 Hot으로 판단
def is_hot_content(content_id: str) -> bool:
    view_count = redis.get(f"content:views:{content_id}:7d")
    return int(view_count or 0) >= 5
```

**공간 관리 (LRU)**:
```python
# SSD 공간 95% 도달 시 자동 삭제
async def cleanup_ssd_cache():
    usage = get_disk_usage("/mnt/ssd_cache")
    if usage.percent >= 95:
        # 가장 오래 전에 접근한 콘텐츠부터 삭제
        old_contents = db.query(
            "SELECT content_id FROM cached_content "
            "ORDER BY last_accessed ASC LIMIT 10"
        )
        for content in old_contents:
            await remove_from_cache(content.content_id)
```

**성능 목표**:
- 캐시 히트율: > 80%
- 읽기 속도: > 500 MB/s
- 응답 시간: < 5ms

### 3.3 L3: Rate Limiter

**목적**: 동시 스트리밍 접속 제한으로 네트워크 과부하 방지

```python
# Rate Limiter 구조

# Redis 슬롯 관리
Key: "stream:slots"
Type: ZSET (sorted set)
Value: {
    "user-1": 1733900000,  # (user_id: timestamp)
    "user-2": 1733900010,
    ...
}

# 동시 접속 제한
MAX_CONCURRENT_STREAMS = 100

# 대기열
Key: "stream:queue"
Type: LIST
Value: ["user-101", "user-102", ...]
```

**슬롯 획득 로직**:
```python
async def acquire_stream_slot(user_id: str) -> tuple[bool, str]:
    """
    스트림 슬롯 획득

    Returns:
        (success: bool, message: str)
    """
    current_count = redis.zcard("stream:slots")

    # 슬롯 여유 있음
    if current_count < MAX_CONCURRENT_STREAMS:
        redis.zadd("stream:slots", {user_id: time.time()})
        return (True, "Slot acquired")

    # 슬롯 없음 → 대기열 추가
    redis.rpush("stream:queue", user_id)
    queue_position = redis.llen("stream:queue")
    return (False, f"Queue position: {queue_position}")

async def release_stream_slot(user_id: str):
    """스트림 슬롯 반환"""
    redis.zrem("stream:slots", user_id)

    # 대기열에서 다음 사용자 슬롯 할당
    next_user = redis.lpop("stream:queue")
    if next_user:
        redis.zadd("stream:slots", {next_user: time.time()})
        await notify_slot_available(next_user)
```

**자동 정리**:
```python
# 60분 이상 활동 없는 슬롯 자동 해제
async def cleanup_stale_slots():
    while True:
        cutoff = time.time() - 3600  # 60분 전
        stale_users = redis.zrangebyscore(
            "stream:slots",
            "-inf",
            cutoff
        )
        for user_id in stale_users:
            await release_stream_slot(user_id)

        await asyncio.sleep(300)  # 5분마다 체크
```

### 3.4 L4: NAS SMB 3.0 Storage

**목적**: 모든 콘텐츠 원본 저장소

```python
# NAS 연결 설정
NAS_HOST = "//192.168.1.100/wsoptv"
NAS_MOUNT = "/mnt/nas"
NAS_USER = "wsoptv_service"
NAS_PROTOCOL = "SMB 3.0"

# 디렉토리 구조
/mnt/nas/
├── videos/
│   ├── content-1.mp4
│   ├── content-2.mp4
│   └── ...
├── thumbnails/
│   ├── content-1.jpg
│   └── ...
└── metadata/
    └── catalog.json
```

**마운트 관리**:
```python
async def ensure_nas_mounted() -> bool:
    """NAS 마운트 상태 확인 및 자동 재연결"""
    if not is_mounted("/mnt/nas"):
        try:
            await mount_nas()
            return True
        except Exception as e:
            logger.error(f"NAS mount failed: {e}")
            return False
    return True

async def get_content_from_nas(content_id: str) -> Path:
    """NAS에서 콘텐츠 경로 조회"""
    if not await ensure_nas_mounted():
        raise StorageUnavailableError("NAS not available")

    path = Path(f"/mnt/nas/videos/{content_id}.mp4")
    if not path.exists():
        raise ContentNotFoundError(f"Content {content_id} not found")

    return path
```

**장애 처리**:
```python
# NAS 장애 시 Fallback
async def get_content_path(content_id: str) -> Path:
    # 1. SSD 캐시 확인
    ssd_path = await get_from_ssd_cache(content_id)
    if ssd_path:
        return ssd_path

    # 2. NAS 시도
    try:
        nas_path = await get_content_from_nas(content_id)
        # Hot이면 백그라운드로 SSD에 복사
        if await is_hot_content(content_id):
            asyncio.create_task(copy_to_ssd_cache(content_id, nas_path))
        return nas_path
    except StorageUnavailableError:
        # 3. NAS 장애 → 이벤트 발행
        await publish_event("nas_unavailable", {"content_id": content_id})
        raise ContentUnavailableError("Storage temporarily unavailable")
```

---

## 4. Provided Contracts

Cache Block이 다른 블럭에 제공하는 API:

```python
# app/orchestration/contracts/cache.py

class CacheBlockAPI(Protocol):
    """Cache Block 인터페이스 계약"""

    async def get(self, key: str) -> Any | None:
        """
        캐시 조회 (L1 Redis)

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        ...

    async def set(self, key: str, value: Any, ttl: int = 600) -> None:
        """
        캐시 저장 (L1 Redis)

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: TTL (초, 기본 10분)
        """
        ...

    async def delete(self, key: str) -> None:
        """
        캐시 삭제

        Args:
            key: 삭제할 캐시 키
        """
        ...

    async def get_stream_path(self, content_id: str) -> Path:
        """
        스트리밍용 파일 경로 반환 (SSD 우선, 없으면 NAS)

        Args:
            content_id: 콘텐츠 ID

        Returns:
            파일 경로 (SSD 또는 NAS)

        Raises:
            ContentNotFoundError: 콘텐츠 없음
            StorageUnavailableError: 스토리지 장애
        """
        ...

    async def acquire_stream_slot(self, user_id: str) -> tuple[bool, str]:
        """
        스트림 슬롯 획득 (Rate Limiter)

        Args:
            user_id: 사용자 ID

        Returns:
            (success: bool, message: str)
            - success=True: 슬롯 획득 성공
            - success=False: 대기열 추가됨, message에 대기 순번
        """
        ...

    async def release_stream_slot(self, user_id: str) -> None:
        """
        스트림 슬롯 반환

        Args:
            user_id: 사용자 ID
        """
        ...

    async def is_hot_content(self, content_id: str) -> bool:
        """
        Hot Content 여부 확인

        Args:
            content_id: 콘텐츠 ID

        Returns:
            Hot이면 True (7일 내 5회+ 조회)
        """
        ...

    async def increment_view_count(self, content_id: str) -> int:
        """
        조회수 증가 (Hot Content 판단용)

        Args:
            content_id: 콘텐츠 ID

        Returns:
            현재 조회수 (7일 내)
        """
        ...

    async def get_cache_stats(self) -> dict:
        """
        캐시 통계 조회

        Returns:
            {
                "l1_hit_rate": 0.85,
                "l2_usage_percent": 78,
                "l3_active_streams": 45,
                "l4_status": "healthy"
            }
        """
        ...
```

---

## 5. Required Contracts

Cache Block은 독립적으로 동작하며, 다른 블럭의 API를 직접 호출하지 않습니다.

**의존성**: 없음

**참고**:
- Cache Block은 이벤트를 구독하여 간접적으로 정보를 수신합니다
- 다른 블럭과의 통신은 오케스트레이터를 통한 이벤트 Pub/Sub만 사용

---

## 6. Events Published

Cache Block이 발행하는 이벤트:

```python
# 이벤트 정의

class CacheEvent:
    """Cache Block 이벤트"""

    # 1. cache_hit
    CACHE_HIT = {
        "event_type": "cache_hit",
        "payload": {
            "content_id": "content-123",
            "tier": "l1" | "l2",  # 어느 tier에서 hit
            "latency_ms": 2.5
        }
    }

    # 2. cache_miss
    CACHE_MISS = {
        "event_type": "cache_miss",
        "payload": {
            "content_id": "content-456",
            "requested_tier": "l2",
            "fallback_tier": "l4"  # NAS로 폴백
        }
    }

    # 3. ssd_cache_full
    SSD_CACHE_FULL = {
        "event_type": "ssd_cache_full",
        "payload": {
            "usage_percent": 95,
            "total_gb": 500,
            "used_gb": 475,
            "cleanup_triggered": True,
            "removed_contents": ["content-10", "content-22"]
        }
    }

    # 4. nas_unavailable
    NAS_UNAVAILABLE = {
        "event_type": "nas_unavailable",
        "payload": {
            "error": "SMB connection timeout",
            "last_successful_check": "2025-12-11T10:30:00Z",
            "retry_in_seconds": 60
        }
    }

    # 5. hot_content_detected
    HOT_CONTENT_DETECTED = {
        "event_type": "hot_content_detected",
        "payload": {
            "content_id": "content-789",
            "view_count_7d": 12,
            "triggered_caching": True,
            "estimated_cache_time_seconds": 120
        }
    }

    # 6. rate_limit_exceeded
    RATE_LIMIT_EXCEEDED = {
        "event_type": "rate_limit_exceeded",
        "payload": {
            "current_streams": 100,
            "max_streams": 100,
            "queue_length": 5,
            "user_id": "user-999"
        }
    }
```

**이벤트 구독자**:
- `cache_hit`, `cache_miss` → Admin Block (모니터링)
- `ssd_cache_full` → Admin Block (알림), Worker Block (정리 작업)
- `nas_unavailable` → Admin Block (긴급 알림)
- `hot_content_detected` → Content Block (메타데이터 업데이트)
- `rate_limit_exceeded` → Admin Block (부하 모니터링)

---

## 7. Events Subscribed

Cache Block이 구독하는 이벤트:

```python
# 구독 이벤트

# 1. content_added (from Content Block)
@orchestrator.subscribe("content_added")
async def on_content_added(event: BlockMessage):
    """
    새 콘텐츠 추가 시
    - Redis 메타데이터 초기화
    - 조회수 카운터 생성
    """
    content_id = event.payload["content_id"]

    # L1 메타데이터 캐싱
    await cache.set(
        f"content:meta:{content_id}",
        {
            "title": event.payload["title"],
            "size": event.payload["size"],
            "location": "nas"  # 초기에는 항상 NAS
        },
        ttl=600
    )

    # 조회수 카운터 초기화
    await cache.set(f"content:views:{content_id}:7d", 0, ttl=604800)


# 2. stream_started (from Stream Block)
@orchestrator.subscribe("stream_started")
async def on_stream_started(event: BlockMessage):
    """
    스트림 시작 시
    - 조회수 증가
    - Hot Content 체크
    """
    content_id = event.payload["content_id"]

    # 조회수 증가
    view_count = await cache.increment_view_count(content_id)

    # Hot Content 판단 (5회 이상)
    if view_count >= 5:
        is_cached = await check_if_cached_in_ssd(content_id)
        if not is_cached:
            # SSD로 복사 (백그라운드)
            asyncio.create_task(cache_to_ssd(content_id))

            # 이벤트 발행
            await publish_event("hot_content_detected", {
                "content_id": content_id,
                "view_count_7d": view_count
            })


# 3. stream_ended (from Stream Block)
@orchestrator.subscribe("stream_ended")
async def on_stream_ended(event: BlockMessage):
    """
    스트림 종료 시
    - 슬롯 반환
    - SSD 캐시 last_accessed 업데이트
    """
    user_id = event.payload["user_id"]
    content_id = event.payload["content_id"]

    # 슬롯 반환
    await cache.release_stream_slot(user_id)

    # SSD 캐시 접근 시간 업데이트
    if await is_in_ssd_cache(content_id):
        await update_ssd_access_time(content_id)


# 4. content_deleted (from Content Block)
@orchestrator.subscribe("content_deleted")
async def on_content_deleted(event: BlockMessage):
    """
    콘텐츠 삭제 시
    - 모든 캐시 제거
    """
    content_id = event.payload["content_id"]

    # L1 캐시 삭제
    await cache.delete(f"content:meta:{content_id}")
    await cache.delete(f"content:views:{content_id}:7d")

    # L2 SSD 캐시 삭제
    await remove_from_ssd_cache(content_id)
```

---

## 8. Hot Content Logic

### 8.1 판단 기준

```python
# Hot Content 정의
HOT_CONTENT_THRESHOLD = 5      # 7일 내 조회수
HOT_CONTENT_WINDOW_DAYS = 7    # 평가 기간

async def is_hot_content(content_id: str) -> bool:
    """
    Hot Content 여부 판단

    기준: 7일 내 5회 이상 조회
    """
    key = f"content:views:{content_id}:7d"
    view_count = await redis.get(key)
    return int(view_count or 0) >= HOT_CONTENT_THRESHOLD
```

### 8.2 조회수 추적

```python
async def increment_view_count(content_id: str) -> int:
    """
    조회수 증가 및 Hot 판단

    Returns:
        현재 조회수 (7일 내)
    """
    key = f"content:views:{content_id}:7d"

    # 조회수 증가 (TTL 7일)
    view_count = await redis.incr(key)
    await redis.expire(key, 604800)  # 7일

    # Hot Content 체크
    if view_count == HOT_CONTENT_THRESHOLD:
        # 정확히 5회가 된 순간 캐싱 시작
        asyncio.create_task(cache_to_ssd(content_id))

        await publish_event("hot_content_detected", {
            "content_id": content_id,
            "view_count_7d": view_count,
            "triggered_caching": True
        })

    return view_count
```

### 8.3 SSD 캐싱 프로세스

```python
async def cache_to_ssd(content_id: str):
    """
    NAS → SSD 복사 (백그라운드)
    """
    logger.info(f"Starting SSD caching for {content_id}")

    try:
        # 1. 공간 확인
        if await get_ssd_usage_percent() >= 95:
            await cleanup_ssd_cache()

        # 2. NAS에서 파일 조회
        nas_path = await get_content_from_nas(content_id)

        # 3. SSD로 복사
        ssd_path = Path(f"/mnt/ssd_cache/{content_id}.mp4")
        await copy_file(nas_path, ssd_path)

        # 4. 메타데이터 업데이트
        await db.execute(
            "INSERT INTO cached_content VALUES (?, ?, ?, ?, ?, ?)",
            (content_id, str(ssd_path), ssd_path.stat().st_size,
             datetime.utcnow(), datetime.utcnow(), 0)
        )

        # 5. Redis 메타데이터 업데이트
        await cache.set(
            f"content:meta:{content_id}",
            {"location": "ssd", "path": str(ssd_path)},
            ttl=600
        )

        logger.info(f"SSD caching completed for {content_id}")

    except Exception as e:
        logger.error(f"SSD caching failed for {content_id}: {e}")
        await publish_event("cache_error", {
            "content_id": content_id,
            "error": str(e)
        })
```

### 8.4 Cold Content 처리

```python
async def get_stream_path(content_id: str) -> Path:
    """
    스트리밍 경로 반환 (Hot/Cold 자동 판단)
    """
    # 1. SSD 캐시 확인 (Hot Content)
    ssd_path = await get_from_ssd_cache(content_id)
    if ssd_path:
        # L2 Hit
        await publish_event("cache_hit", {
            "content_id": content_id,
            "tier": "l2"
        })
        return ssd_path

    # 2. NAS에서 직접 스트리밍 (Cold Content)
    nas_path = await get_content_from_nas(content_id)

    await publish_event("cache_miss", {
        "content_id": content_id,
        "requested_tier": "l2",
        "fallback_tier": "l4"
    })

    # 3. Hot 여부 확인 후 백그라운드 캐싱
    if await is_hot_content(content_id):
        asyncio.create_task(cache_to_ssd(content_id))

    return nas_path
```

---

## 9. Directory Structure

```
api/app/blocks/cache/
├── __init__.py
├── router.py                  # API 엔드포인트
├── service.py                 # 비즈니스 로직
├── models.py                  # 데이터 모델
├── config.py                  # 설정
├── l1_redis.py               # L1 Redis 캐시
├── l2_ssd.py                 # L2 SSD 캐시
├── l3_rate_limiter.py        # L3 Rate Limiter
├── l4_nas.py                 # L4 NAS 관리
├── hot_detector.py           # Hot Content 판단
├── events.py                 # 이벤트 핸들러
└── exceptions.py             # 예외 정의

tests/blocks/cache/
├── __init__.py
├── conftest.py               # Fixtures
├── test_l1_redis.py          # L1 테스트
├── test_l2_ssd.py            # L2 테스트
├── test_l3_rate_limiter.py   # L3 테스트
├── test_l4_nas.py            # L4 테스트
├── test_hot_detector.py      # Hot 판단 로직 테스트
├── test_integration.py       # 통합 테스트
└── mocks/
    ├── mock_redis.py
    ├── mock_filesystem.py
    └── mock_nas.py

docs/blocks/
└── 04-cache.md               # 이 문서
```

### 9.1 핵심 파일 구조

```python
# api/app/blocks/cache/service.py

class CacheService:
    """Cache Block 메인 서비스"""

    def __init__(
        self,
        redis: Redis,
        ssd_cache: SSDCache,
        rate_limiter: RateLimiter,
        nas: NASStorage
    ):
        self.l1 = RedisCache(redis)
        self.l2 = ssd_cache
        self.l3 = rate_limiter
        self.l4 = nas
        self.hot_detector = HotContentDetector(redis)

    async def get_stream_path(self, content_id: str) -> Path:
        """스트리밍 경로 반환 (계층 탐색)"""
        # L2 확인
        if path := await self.l2.get(content_id):
            return path
        # L4 폴백
        return await self.l4.get(content_id)

    async def acquire_stream_slot(self, user_id: str) -> tuple[bool, str]:
        """스트림 슬롯 획득"""
        return await self.l3.acquire(user_id)
```

```python
# api/app/blocks/cache/l2_ssd.py

class SSDCache:
    """L2 SSD 캐시 관리"""

    def __init__(self, cache_dir: Path, max_size_gb: int = 500):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_gb * 1024**3
        self.db = self._init_db()

    async def get(self, content_id: str) -> Path | None:
        """SSD 캐시 조회"""
        result = await self.db.fetchone(
            "SELECT file_path FROM cached_content WHERE content_id = ?",
            (content_id,)
        )
        if result and Path(result[0]).exists():
            await self._update_access_time(content_id)
            return Path(result[0])
        return None

    async def add(self, content_id: str, source_path: Path):
        """SSD에 콘텐츠 추가"""
        # 공간 확인
        await self._ensure_space(source_path.stat().st_size)

        # 복사
        dest = self.cache_dir / f"{content_id}.mp4"
        await copy_file(source_path, dest)

        # DB 등록
        await self.db.execute(
            "INSERT INTO cached_content VALUES (?, ?, ?, ?, ?, ?)",
            (content_id, str(dest), dest.stat().st_size,
             datetime.utcnow(), datetime.utcnow(), 0)
        )

    async def _ensure_space(self, required_bytes: int):
        """공간 확보 (LRU)"""
        current_usage = await self._get_usage_bytes()

        while current_usage + required_bytes > self.max_size_bytes:
            # 가장 오래된 콘텐츠 삭제
            oldest = await self.db.fetchone(
                "SELECT content_id FROM cached_content "
                "ORDER BY last_accessed ASC LIMIT 1"
            )
            if oldest:
                await self.remove(oldest[0])
                current_usage = await self._get_usage_bytes()
            else:
                break
```

```python
# api/app/blocks/cache/l3_rate_limiter.py

class RateLimiter:
    """L3 Rate Limiter"""

    def __init__(self, redis: Redis, max_streams: int = 100):
        self.redis = redis
        self.max_streams = max_streams
        self.slots_key = "stream:slots"
        self.queue_key = "stream:queue"

    async def acquire(self, user_id: str) -> tuple[bool, str]:
        """슬롯 획득"""
        current = await self.redis.zcard(self.slots_key)

        if current < self.max_streams:
            await self.redis.zadd(
                self.slots_key,
                {user_id: time.time()}
            )
            return (True, "Slot acquired")

        # 대기열 추가
        await self.redis.rpush(self.queue_key, user_id)
        position = await self.redis.llen(self.queue_key)
        return (False, f"Queue position: {position}")

    async def release(self, user_id: str):
        """슬롯 반환"""
        await self.redis.zrem(self.slots_key, user_id)

        # 대기열 처리
        next_user = await self.redis.lpop(self.queue_key)
        if next_user:
            await self.redis.zadd(
                self.slots_key,
                {next_user: time.time()}
            )
```

---

## 10. Testing Strategy

### 10.1 테스트 원칙

| 원칙 | 설명 |
|------|------|
| **독립성** | 다른 블럭은 Mock으로 대체 |
| **실제 캐시 Mock** | Redis, SSD, NAS도 Mock 제공 |
| **시나리오 기반** | 실제 사용 시나리오 재현 |
| **성능 테스트** | 캐시 히트율, 응답 시간 검증 |

### 10.2 Unit Tests

```python
# tests/blocks/cache/test_l2_ssd.py

@pytest.fixture
def mock_filesystem(tmp_path):
    """임시 파일시스템 Mock"""
    cache_dir = tmp_path / "ssd_cache"
    cache_dir.mkdir()
    return cache_dir

@pytest.fixture
def ssd_cache(mock_filesystem):
    return SSDCache(cache_dir=mock_filesystem, max_size_gb=1)

async def test_ssd_cache_add_and_get(ssd_cache, tmp_path):
    """SSD 캐시 추가 및 조회"""
    # Given: 테스트 파일 생성
    test_file = tmp_path / "test.mp4"
    test_file.write_bytes(b"x" * 1024)  # 1KB

    # When: SSD에 추가
    await ssd_cache.add("content-1", test_file)

    # Then: 조회 가능
    cached_path = await ssd_cache.get("content-1")
    assert cached_path is not None
    assert cached_path.exists()
    assert cached_path.stat().st_size == 1024

async def test_ssd_cache_lru_eviction(ssd_cache, tmp_path):
    """SSD 캐시 LRU 삭제"""
    # Given: 최대 용량 1GB, 800MB 파일 2개 추가
    file1 = tmp_path / "file1.mp4"
    file1.write_bytes(b"x" * (800 * 1024**2))  # 800MB
    await ssd_cache.add("content-1", file1)

    await asyncio.sleep(0.1)  # 시간 차이

    file2 = tmp_path / "file2.mp4"
    file2.write_bytes(b"x" * (800 * 1024**2))  # 800MB

    # When: 두 번째 파일 추가 (용량 초과)
    await ssd_cache.add("content-2", file2)

    # Then: 첫 번째 파일 자동 삭제됨 (LRU)
    assert await ssd_cache.get("content-1") is None
    assert await ssd_cache.get("content-2") is not None
```

```python
# tests/blocks/cache/test_l3_rate_limiter.py

@pytest.fixture
def mock_redis():
    """Redis Mock"""
    return FakeRedis()

@pytest.fixture
def rate_limiter(mock_redis):
    return RateLimiter(redis=mock_redis, max_streams=3)

async def test_acquire_slot_success(rate_limiter):
    """슬롯 획득 성공"""
    # When: 슬롯 요청
    success, msg = await rate_limiter.acquire("user-1")

    # Then: 성공
    assert success is True
    assert msg == "Slot acquired"

async def test_acquire_slot_queue(rate_limiter):
    """슬롯 초과 시 대기열"""
    # Given: 최대 슬롯 3개 모두 사용
    await rate_limiter.acquire("user-1")
    await rate_limiter.acquire("user-2")
    await rate_limiter.acquire("user-3")

    # When: 4번째 사용자 요청
    success, msg = await rate_limiter.acquire("user-4")

    # Then: 대기열 추가
    assert success is False
    assert "Queue position: 1" in msg

async def test_release_slot_dequeue(rate_limiter):
    """슬롯 반환 시 대기열 자동 처리"""
    # Given: 슬롯 3개 + 대기열 1명
    await rate_limiter.acquire("user-1")
    await rate_limiter.acquire("user-2")
    await rate_limiter.acquire("user-3")
    await rate_limiter.acquire("user-4")  # 대기열

    # When: user-1 슬롯 반환
    await rate_limiter.release("user-1")

    # Then: user-4 자동으로 슬롯 할당
    slots = await rate_limiter.redis.zrange("stream:slots", 0, -1)
    assert "user-4" in slots
```

```python
# tests/blocks/cache/test_hot_detector.py

async def test_hot_content_detection(mock_redis):
    """Hot Content 자동 감지"""
    detector = HotContentDetector(mock_redis)

    # Given: 조회수 4회
    for _ in range(4):
        await detector.increment_view_count("content-1")

    # When: 5번째 조회
    view_count = await detector.increment_view_count("content-1")

    # Then: Hot으로 판단
    assert view_count == 5
    assert await detector.is_hot_content("content-1") is True

async def test_view_count_ttl(mock_redis):
    """조회수 TTL 7일 확인"""
    detector = HotContentDetector(mock_redis)

    # When: 조회수 증가
    await detector.increment_view_count("content-1")

    # Then: TTL 7일 설정됨
    ttl = await mock_redis.ttl("content:views:content-1:7d")
    assert 604700 <= ttl <= 604800  # 7일 (약간 오차 허용)
```

### 10.3 Integration Tests

```python
# tests/blocks/cache/test_integration.py

async def test_full_cache_flow(cache_service, mock_redis, tmp_path):
    """전체 캐시 플로우 테스트"""
    # Given: NAS에 콘텐츠 존재
    nas_dir = tmp_path / "nas"
    nas_dir.mkdir()
    content_file = nas_dir / "content-1.mp4"
    content_file.write_bytes(b"x" * (100 * 1024**2))  # 100MB

    # When: 1회 스트리밍 (Cold)
    path1 = await cache_service.get_stream_path("content-1")

    # Then: NAS에서 직접 조회 (L4)
    assert path1 == content_file
    assert await cache_service.is_hot_content("content-1") is False

    # When: 5회 스트리밍 (Hot 기준)
    for _ in range(4):
        await cache_service.increment_view_count("content-1")
        await cache_service.get_stream_path("content-1")

    # 백그라운드 캐싱 완료 대기
    await asyncio.sleep(1)

    # Then: SSD에 캐싱됨 (L2)
    path2 = await cache_service.get_stream_path("content-1")
    assert "/ssd_cache/" in str(path2)
    assert await cache_service.is_hot_content("content-1") is True

async def test_rate_limiter_integration(cache_service):
    """Rate Limiter 통합 테스트"""
    # Given: 최대 슬롯 3개

    # When: 3명 동시 스트리밍
    slot1 = await cache_service.acquire_stream_slot("user-1")
    slot2 = await cache_service.acquire_stream_slot("user-2")
    slot3 = await cache_service.acquire_stream_slot("user-3")

    # Then: 모두 성공
    assert slot1[0] is True
    assert slot2[0] is True
    assert slot3[0] is True

    # When: 4번째 사용자 요청
    slot4 = await cache_service.acquire_stream_slot("user-4")

    # Then: 대기열 추가
    assert slot4[0] is False

    # When: user-1 종료
    await cache_service.release_stream_slot("user-1")

    # Then: user-4 자동 슬롯 할당 (이벤트 확인 필요)
```

### 10.4 Performance Tests

```python
# tests/blocks/cache/test_performance.py

import pytest
import time

async def test_l1_cache_latency(cache_service):
    """L1 Redis 캐시 응답 시간 < 5ms"""
    # Given: L1 캐시에 데이터 저장
    await cache_service.l1.set("test-key", {"data": "value"})

    # When: 100회 조회
    start = time.time()
    for _ in range(100):
        await cache_service.l1.get("test-key")
    elapsed = time.time() - start

    # Then: 평균 5ms 이하
    avg_latency = (elapsed / 100) * 1000  # ms
    assert avg_latency < 5, f"L1 latency {avg_latency}ms > 5ms"

async def test_cache_hit_rate(cache_service, tmp_path):
    """캐시 히트율 > 80%"""
    # Given: Hot Content 10개 (SSD에 캐싱됨)
    for i in range(10):
        content_id = f"content-{i}"
        # 5회 조회로 Hot 만들기
        for _ in range(5):
            await cache_service.increment_view_count(content_id)

    # 캐싱 완료 대기
    await asyncio.sleep(2)

    # When: 100회 랜덤 조회 (Hot Content 위주)
    hits = 0
    for _ in range(100):
        content_id = f"content-{random.randint(0, 9)}"  # Hot Content
        stats_before = await cache_service.get_cache_stats()
        await cache_service.get_stream_path(content_id)
        stats_after = await cache_service.get_cache_stats()

        if stats_after["l2_hits"] > stats_before["l2_hits"]:
            hits += 1

    # Then: 히트율 80% 이상
    hit_rate = hits / 100
    assert hit_rate >= 0.80, f"Hit rate {hit_rate} < 0.80"
```

### 10.5 Mocks

```python
# tests/blocks/cache/mocks/mock_redis.py

class FakeRedis:
    """Redis Mock (in-memory)"""

    def __init__(self):
        self.data: dict = {}
        self.ttls: dict = {}

    async def get(self, key: str) -> str | None:
        if key in self.data:
            if key in self.ttls and time.time() > self.ttls[key]:
                del self.data[key]
                del self.ttls[key]
                return None
            return self.data[key]
        return None

    async def set(self, key: str, value: str):
        self.data[key] = value

    async def expire(self, key: str, seconds: int):
        self.ttls[key] = time.time() + seconds

    async def incr(self, key: str) -> int:
        current = int(self.data.get(key, 0))
        self.data[key] = str(current + 1)
        return current + 1

    async def zadd(self, key: str, mapping: dict):
        if key not in self.data:
            self.data[key] = {}
        self.data[key].update(mapping)

    async def zcard(self, key: str) -> int:
        return len(self.data.get(key, {}))

    async def zrem(self, key: str, *members):
        if key in self.data:
            for member in members:
                self.data[key].pop(member, None)
```

```python
# tests/blocks/cache/mocks/mock_filesystem.py

class MockFilesystem:
    """파일시스템 Mock"""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.files: dict[str, bytes] = {}

    async def create_file(self, path: Path, content: bytes):
        """파일 생성"""
        self.files[str(path)] = content
        path.write_bytes(content)

    async def copy_file(self, src: Path, dest: Path):
        """파일 복사"""
        content = src.read_bytes()
        dest.write_bytes(content)
        self.files[str(dest)] = content

    def get_usage_percent(self, path: Path) -> float:
        """디스크 사용률 Mock"""
        total_size = sum(len(c) for c in self.files.values())
        max_size = 500 * 1024**3  # 500GB
        return (total_size / max_size) * 100
```

### 10.6 Test Coverage

```bash
# 테스트 실행
pytest tests/blocks/cache/ -v --cov=api/app/blocks/cache

# 커버리지 목표
# - 라인 커버리지: > 90%
# - 브랜치 커버리지: > 85%
# - 핵심 로직: 100%
```

**필수 테스트 시나리오**:
- [ ] L1 Redis 캐시 CRUD
- [ ] L2 SSD LRU 삭제
- [ ] L3 Rate Limiter 슬롯 획득/반환
- [ ] L4 NAS 연결 실패 처리
- [ ] Hot Content 자동 감지
- [ ] 조회수 카운터 TTL
- [ ] 계층 간 폴백 (L2 → L4)
- [ ] 이벤트 발행/구독
- [ ] 성능 목표 달성 (< 5ms, > 80% hit rate)
- [ ] Circuit Breaker (NAS 장애 시)

---

## 11. Monitoring & Metrics

### 11.1 핵심 지표

```python
# 모니터링 메트릭

class CacheMetrics:
    """Cache Block 메트릭"""

    # L1 Redis
    l1_hit_rate: float          # 캐시 히트율 (목표: > 0.85)
    l1_memory_usage_mb: int     # 메모리 사용량
    l1_evictions: int           # 삭제된 키 수

    # L2 SSD
    l2_hit_rate: float          # 캐시 히트율 (목표: > 0.80)
    l2_usage_percent: float     # 디스크 사용률
    l2_cached_content_count: int  # 캐싱된 콘텐츠 수
    l2_avg_access_time_ms: float  # 평균 접근 시간

    # L3 Rate Limiter
    l3_active_streams: int      # 현재 스트리밍 수
    l3_queue_length: int        # 대기열 길이
    l3_rejected_requests: int   # 거부된 요청 수

    # L4 NAS
    l4_status: str              # "healthy" | "degraded" | "unavailable"
    l4_response_time_ms: float  # 평균 응답 시간
    l4_error_count: int         # 에러 발생 횟수

    # Hot Content
    hot_content_count: int      # Hot Content 수
    auto_cache_triggered: int   # 자동 캐싱 트리거 횟수
```

### 11.2 알림 규칙

| 조건 | 알림 레벨 | 액션 |
|------|----------|------|
| SSD 사용률 > 95% | WARNING | 자동 정리 트리거 |
| L2 히트율 < 70% | WARNING | Hot 기준 재검토 |
| 동시 스트림 > 90% | INFO | 부하 모니터링 |
| NAS 연결 실패 | CRITICAL | 긴급 알림 |
| Rate Limit 대기열 > 20 | WARNING | 용량 증설 검토 |

---

## 12. Deployment

### 12.1 Dependencies

```toml
# pyproject.toml

[tool.poetry.dependencies]
redis = "^5.0.0"              # L1 캐시
aiofiles = "^23.2.1"          # 비동기 파일 I/O
psutil = "^5.9.0"             # 디스크 사용률 모니터링
asyncpg = "^0.29.0"           # L2 메타데이터 DB
pysmb = "^1.2.9"              # SMB 3.0 클라이언트
```

### 12.2 Environment Variables

```bash
# Cache Block 환경 변수

# L1 Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_MEMORY=2gb

# L2 SSD
SSD_CACHE_DIR=/mnt/ssd_cache
SSD_MAX_SIZE_GB=500

# L3 Rate Limiter
MAX_CONCURRENT_STREAMS=100
STREAM_SLOT_TIMEOUT=3600  # 60분

# L4 NAS
NAS_HOST=//192.168.1.100/wsoptv
NAS_MOUNT=/mnt/nas
NAS_USER=wsoptv_service
NAS_PASSWORD=***
NAS_PROTOCOL=3.0  # SMB 3.0

# Hot Content
HOT_CONTENT_THRESHOLD=5
HOT_CONTENT_WINDOW_DAYS=7
```

### 12.3 Health Check

```python
# Health check endpoint

@router.get("/health")
async def health_check():
    """Cache Block 헬스체크"""
    return {
        "status": "healthy",
        "checks": {
            "l1_redis": await check_redis_connection(),
            "l2_ssd": await check_ssd_writable(),
            "l3_rate_limiter": "ok",
            "l4_nas": await check_nas_mounted()
        },
        "metrics": await cache_service.get_cache_stats()
    }
```

---

## Success Metrics

| Metric | Target | 측정 방법 |
|--------|--------|----------|
| L1 히트율 | > 85% | Redis INFO stats |
| L2 히트율 | > 80% | SSD 조회 성공률 |
| L1 응답 시간 | < 5ms | Latency 측정 |
| L2 응답 시간 | < 50ms | SSD I/O 시간 |
| SSD 공간 효율 | 70-95% | 디스크 사용률 |
| Hot Content 정확도 | > 90% | 실제 재조회율 |
| Rate Limit 준수 | 100% | 동시 스트림 <= MAX |
| NAS Uptime | > 99.9% | 연결 성공률 |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-11 | Claude Code | Initial draft |
