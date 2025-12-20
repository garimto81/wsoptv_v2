# Cache Block PRD

**Version**: 2.0.0 | **Block ID**: cache | **Level**: L0 (No dependencies)

---

## 1. Overview

Cache Block은 **4-Tier 캐시 시스템**을 관리하여 콘텐츠 전송 성능을 최적화합니다.

### 책임 범위

| 책임 영역 | 세부 기능 |
|----------|----------|
| **L1 관리** | Redis 기반 메타데이터/세션 캐싱 |
| **L2 관리** | SSD 500GB Hot Content 캐싱 (LRU) |
| **L3 관리** | 동시 스트리밍 Rate Limiting |
| **L4 연동** | NAS/S3 원본 콘텐츠 접근 |
| **Hot 판단** | 조회 패턴 분석 및 자동 캐싱 |

---

## 2. 4-Tier Cache Hierarchy

```
Request → [L1: Redis] → [L2: SSD] → [L3: Rate Limit] → [L4: Storage]
               │             │              │                  │
              hit           hit           pass               Response
```

### Tier Details

| Tier | 저장소 | 용량 | TTL | 용도 |
|:----:|--------|------|-----|------|
| **L1** | Redis | 2GB | 10분~24시간 | 메타데이터, 세션 |
| **L2** | SSD | 500GB | LRU | Hot Content |
| **L3** | Rate Limiter | - | 실시간 | 동시 접속 제한 |
| **L4** | NAS/S3 | 17.96TB | 영구 | 원본 콘텐츠 |

---

## 3. L1: Redis Cache

### 키 패턴

| 키 패턴 | TTL | 용도 |
|--------|-----|------|
| `content:{id}` | 10분 | 콘텐츠 메타데이터 |
| `home:rows` | 5분 | 홈페이지 Row |
| `user:{id}:session` | 24시간 | 사용자 세션 |
| `user:{id}:progress:{cid}` | 7일 | 시청 진행률 |
| `stream:active` | 실시간 | 활성 스트림 카운트 |
| `content:views:{id}:7d` | 7일 | 7일간 조회수 |

### 운영 규칙

- 메모리 한계: 2GB
- Eviction: `allkeys-lru`
- 백업: RDB (1시간마다)

---

## 4. L2: SSD Hot Cache

### Hot Content 기준

```python
# 자동 캐싱 조건
- 7일 내 5회 이상 조회 → SSD로 복사
- LRU 정책으로 공간 관리
- 95% 도달 시 가장 오래된 콘텐츠 삭제
```

### 디렉토리 구조

```
/cache/hot/
├── content-001.mp4
├── content-002.mp4
└── ...

/cache/thumbnails/
├── content-001.jpg
├── content-002.jpg
└── ...
```

---

## 5. L3: Rate Limiter

### 제한 설정

| 제한 유형 | 값 | 설명 |
|----------|---|------|
| 전체 동시 스트림 | 100개 | 서버 전체 |
| 사용자당 동시 스트림 | 3개 | 개별 사용자 |
| 대기열 크기 | 50 | 대기 중인 요청 |

### Sliding Window Algorithm

```python
class RateLimiter:
    async def acquire_slot(self, user_id: str) -> bool:
        """스트림 슬롯 획득"""
        global_count = await self.redis.get("stream:active")
        user_count = await self.redis.get(f"stream:user:{user_id}")

        if global_count >= 100 or user_count >= 3:
            return False

        await self.redis.incr("stream:active")
        await self.redis.incr(f"stream:user:{user_id}")
        return True

    async def release_slot(self, user_id: str) -> None:
        """스트림 슬롯 해제"""
        await self.redis.decr("stream:active")
        await self.redis.decr(f"stream:user:{user_id}")
```

---

## 6. API Endpoints

### 캐시 관리 (Admin)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/cache/stats` | 캐시 통계 |
| POST | `/api/admin/cache/clear` | 캐시 클리어 |
| POST | `/api/admin/cache/warm/{id}` | 수동 캐시 워밍 |

---

## 7. Contracts

### 제공 계약

```python
class CacheContract:
    async def get(key: str) -> Any | None:
        """L1 캐시 조회"""

    async def set(key: str, value: Any, ttl: int) -> None:
        """L1 캐시 저장"""

    async def get_stream_path(content_id: str) -> str:
        """스트림 파일 경로 (L2 우선, L4 폴백)"""

    async def is_hot(content_id: str) -> bool:
        """Hot Content 여부 확인"""

    async def acquire_stream_slot(user_id: str) -> bool:
        """스트림 슬롯 획득"""

    async def release_stream_slot(user_id: str) -> None:
        """스트림 슬롯 해제"""
```

---

## 8. Events

### 발행 이벤트

| 채널 | 페이로드 | 설명 |
|------|----------|------|
| `cache.content_cached` | `{content_id}` | L2에 캐싱됨 |
| `cache.content_evicted` | `{content_id}` | L2에서 삭제됨 |
| `cache.ssd_threshold` | `{usage_percent}` | SSD 사용량 경고 |

---

## 9. Monitoring

### 메트릭

| 메트릭 | 설명 |
|--------|------|
| `cache.l1.hit_rate` | Redis 히트율 |
| `cache.l2.hit_rate` | SSD 히트율 |
| `cache.l2.usage_percent` | SSD 사용률 |
| `cache.active_streams` | 활성 스트림 수 |

---

*Parent: [04-technical.md](../04-technical.md)*
