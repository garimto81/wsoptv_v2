# Cache Agent Todo

**Block**: Cache (L0 - 무의존)
**Agent**: cache-agent
**Wave**: 1 (병렬 시작 가능)

---

## 컨텍스트 제한

```
✅ 수정 가능:
  - src/blocks/cache/**
  - tests/test_blocks/test_cache_block.py
  - docs/blocks/04-cache.md

❌ 수정 불가:
  - src/blocks/*/ (다른 블럭)
  - src/orchestration/ (읽기 전용)
```

---

## Todo List

### TDD Red Phase
- [ ] C1: `tests/test_blocks/test_cache_block.py` 확장
  - [ ] test_cache_get_set
  - [ ] test_cache_miss
  - [ ] test_cache_tier_hierarchy
  - [ ] test_hot_content_detection
  - [ ] test_cache_invalidation
  - [ ] test_ssd_cache_promotion

### TDD Green Phase
- [ ] C2: `src/blocks/cache/models.py`
  - [ ] CacheTier Enum (L1_REDIS, L2_SSD, L3_LIMITER, L4_NAS)
  - [ ] CacheEntry 모델 (key, value, tier, ttl, created_at)
  - [ ] StreamSlot 모델 (user_id, content_id, acquired_at)
  - [ ] HotContent 모델 (content_id, view_count, last_viewed)

- [ ] C3: `src/blocks/cache/service.py`
  - [ ] get(key) → Any | None
  - [ ] set(key, value, ttl, tier) → None
  - [ ] get_with_tier(key) → tuple[Any, CacheTier]
  - [ ] invalidate(key) → None
  - [ ] record_access(content_id) → None
  - [ ] is_hot_content(content_id) → bool
  - [ ] mark_as_hot(content_id, file_path) → None
  - [ ] get_content_tier(content_id) → CacheTier
  - [ ] get_stream_path(content_id) → Path
  - [ ] acquire_stream_slot(user_id) → tuple[bool, str]
  - [ ] release_stream_slot(user_id) → None

- [ ] C4: `src/blocks/cache/tiers/l1_redis.py`
  - [ ] Redis 연동
  - [ ] TTL 관리 (기본 600초)

- [ ] C5: `src/blocks/cache/tiers/l2_ssd.py`
  - [ ] SSD 캐시 경로 관리 (500GB)
  - [ ] Hot content 파일 관리

- [ ] C6: `src/blocks/cache/tiers/l3_limiter.py`
  - [ ] Rate Limiter (사용자당 대역폭)
  - [ ] 동시 스트리밍 제한 (사용자당 3개)

- [ ] C7: `src/blocks/cache/tiers/l4_nas.py`
  - [ ] NAS SMB 3.0 연결
  - [ ] 파일 경로 조회

- [ ] C8: 테스트 통과 확인
  - [ ] pytest tests/test_blocks/test_cache_block.py -v
  - [ ] 커버리지 80% 이상

### Refactor Phase
- [ ] C9: 코드 리팩토링
  - [ ] Tier간 자동 승격/강등 로직
  - [ ] LRU 캐시 정책
  - [ ] Hot content 자동 감지 (7일 내 5회)

- [ ] C10: 문서 업데이트
  - [ ] docs/blocks/04-cache.md API 섹션 업데이트
  - [ ] 4-Tier 아키텍처 다이어그램

---

## 이벤트 발행 (Orchestration 통해)

```python
await bus.publish("cache.miss", BlockMessage(payload={"key": key}))
await bus.publish("cache.evicted", BlockMessage(payload={"key": key}))
await bus.publish("cache.ssd_promoted", BlockMessage(payload={"content_id": id}))
```

## 제공 API (Contract)

```python
# 다른 블럭이 호출할 수 있는 API
get(key: str) -> Any | None
set(key: str, value: Any, ttl: int) -> None
get_stream_path(content_id: str) -> Path
acquire_stream_slot(user_id: str) -> tuple[bool, str]
release_stream_slot(user_id: str) -> None
```

---

## 4-Tier 캐시 구조

```
┌─────────────┐
│  L1: Redis  │  ← 메타데이터, 세션 (TTL: 600s)
├─────────────┤
│  L2: SSD    │  ← Hot content (500GB)
├─────────────┤
│ L3: Limiter │  ← Rate limit, 동시 스트리밍 제한
├─────────────┤
│  L4: NAS    │  ← Cold content (18TB)
└─────────────┘
```

**Hot Content 기준**: 7일 내 5회 이상 조회 → SSD 승격

---

## Progress: 0/10 (0%)
