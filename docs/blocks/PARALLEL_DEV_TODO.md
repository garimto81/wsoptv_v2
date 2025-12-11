# 블럭 병렬 개발 Todo

**Version**: 1.0.0
**Date**: 2025-12-11
**Orchestration**: 전담 에이전트별 독립 Todo

---

## 블럭 의존성 순서

```
Layer 0 (무의존):  Auth, Cache
          ↓
Layer 1 (L0 의존): Content, Search, Worker
          ↓
Layer 2 (L1 의존): Stream, Admin
```

---

## 병렬 개발 전략

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration (이미 완료)                 │
│              Message Bus, Registry, Contract                │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
  ┌──────────┐               ┌──────────┐
  │  Auth    │               │  Cache   │     ← Wave 1 (병렬)
  │  Agent   │               │  Agent   │
  └────┬─────┘               └────┬─────┘
       │                          │
       └──────────┬───────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐ ┌─────────┐  ┌─────────┐
│ Content │ │ Search  │  │ Worker  │  ← Wave 2 (병렬)
│ Agent   │ │ Agent   │  │ Agent   │
└────┬────┘ └─────────┘  └─────────┘
     │
     ├──────────────────────────────┐
     │                              │
     ▼                              ▼
┌──────────┐                 ┌──────────┐
│  Stream  │                 │  Admin   │   ← Wave 3 (병렬)
│  Agent   │                 │  Agent   │
└──────────┘                 └──────────┘
```

---

## Wave 1: 기반 블럭 (병렬 시작)

### Auth Agent Todo

| # | Task | Status | 의존성 |
|---|------|--------|--------|
| A1 | 🔴 `test_auth_service.py` 작성 (TDD Red) | pending | - |
| A2 | 🟢 `models.py` - User, Session 모델 | pending | A1 |
| A3 | 🟢 `service.py` - AuthService 구현 | pending | A2 |
| A4 | 🟢 `router.py` - API 엔드포인트 | pending | A3 |
| A5 | ✅ 테스트 통과 확인 (TDD Green) | pending | A4 |
| A6 | ♻️ 리팩토링 | pending | A5 |
| A7 | 📝 `docs/blocks/01-auth.md` 업데이트 | pending | A6 |

**컨텍스트 제한**:
```
수정 가능: src/blocks/auth/**, tests/test_blocks/test_auth_block.py
수정 불가: src/blocks/*/ (다른 블럭), src/orchestration/ (읽기 전용)
```

**이벤트 발행**:
- `auth.user_registered` → Search, Admin 구독
- `auth.user_login` → Admin 구독
- `auth.user_approved` → Content 접근 활성화

---

### Cache Agent Todo

| # | Task | Status | 의존성 |
|---|------|--------|--------|
| C1 | 🔴 `test_cache_service.py` 작성 (TDD Red) | pending | - |
| C2 | 🟢 `models.py` - CacheTier, CacheEntry 모델 | pending | C1 |
| C3 | 🟢 `service.py` - CacheService (4-Tier) | pending | C2 |
| C4 | 🟢 `tiers/l1_redis.py` - L1 Redis | pending | C3 |
| C5 | 🟢 `tiers/l2_ssd.py` - L2 SSD | pending | C3 |
| C6 | 🟢 `tiers/l3_limiter.py` - L3 Rate Limiter | pending | C3 |
| C7 | 🟢 `tiers/l4_nas.py` - L4 NAS | pending | C3 |
| C8 | ✅ 테스트 통과 확인 (TDD Green) | pending | C4-C7 |
| C9 | ♻️ 리팩토링 | pending | C8 |
| C10 | 📝 `docs/blocks/04-cache.md` 업데이트 | pending | C9 |

**컨텍스트 제한**:
```
수정 가능: src/blocks/cache/**, tests/test_blocks/test_cache_block.py
수정 불가: src/blocks/*/ (다른 블럭)
```

**이벤트 발행**:
- `cache.miss` → Worker (캐시 워밍 트리거)
- `cache.evicted` → Admin (모니터링)
- `cache.ssd_promoted` → Admin (통계)

---

## Wave 2: 콘텐츠 블럭 (Wave 1 완료 후)

### Content Agent Todo

| # | Task | Status | 의존성 |
|---|------|--------|--------|
| T1 | 🔴 `test_content_service.py` 작성 (TDD Red) | pending | Auth, Cache |
| T2 | 🟢 `models.py` - Content, Progress 모델 | pending | T1 |
| T3 | 🟢 `service.py` - ContentService 구현 | pending | T2 |
| T4 | 🟢 `router.py` - API 엔드포인트 | pending | T3 |
| T5 | ✅ 테스트 통과 확인 (Auth, Cache Mock) | pending | T4 |
| T6 | ♻️ 리팩토링 | pending | T5 |
| T7 | 📝 `docs/blocks/02-content.md` 업데이트 | pending | T6 |

**의존성 계약**:
```python
# Auth Block으로부터:
auth.validate_token(token) -> User | None
auth.check_permission(user_id, resource) -> bool

# Cache Block으로부터:
cache.get(key) -> Any | None
cache.set(key, value, ttl) -> None
```

**이벤트 발행**:
- `content.added` → Search (인덱싱), Cache (메타데이터)
- `content.viewed` → Cache (hot content 추적), Admin (통계)
- `content.progress_updated` → Admin (통계)

---

### Search Agent Todo

| # | Task | Status | 의존성 |
|---|------|--------|--------|
| S1 | 🔴 `test_search_service.py` 작성 (TDD Red) | pending | Auth |
| S2 | 🟢 `models.py` - SearchResult 모델 | pending | S1 |
| S3 | 🟢 `service.py` - SearchService (MeiliSearch) | pending | S2 |
| S4 | 🟢 `fallback.py` - PostgreSQL LIKE 폴백 | pending | S3 |
| S5 | 🟢 `router.py` - API 엔드포인트 | pending | S4 |
| S6 | ✅ 테스트 통과 확인 (Auth Mock) | pending | S5 |
| S7 | ♻️ 리팩토링 | pending | S6 |
| S8 | 📝 `docs/blocks/06-search.md` 업데이트 | pending | S7 |

**이벤트 구독**:
- `content.added` → 인덱스 추가
- `content.updated` → 인덱스 업데이트
- `content.deleted` → 인덱스 삭제

---

### Worker Agent Todo

| # | Task | Status | 의존성 |
|---|------|--------|--------|
| W1 | 🔴 `test_worker_service.py` 작성 (TDD Red) | pending | Cache |
| W2 | 🟢 `models.py` - Task, TaskQueue 모델 | pending | W1 |
| W3 | 🟢 `service.py` - WorkerService 구현 | pending | W2 |
| W4 | 🟢 `workers/thumbnail.py` - 썸네일 생성 | pending | W3 |
| W5 | 🟢 `workers/cache_warmer.py` - 캐시 워밍 | pending | W3 |
| W6 | 🟢 `workers/nas_scanner.py` - NAS 스캔 | pending | W3 |
| W7 | ✅ 테스트 통과 확인 (Cache Mock) | pending | W4-W6 |
| W8 | ♻️ 리팩토링 | pending | W7 |
| W9 | 📝 `docs/blocks/07-worker.md` 업데이트 | pending | W8 |

**이벤트 구독**:
- `cache.miss` → 캐시 워밍 작업 큐잉
- `content.added` → 썸네일 생성 큐잉

---

## Wave 3: 최종 블럭 (Wave 2 완료 후)

### Stream Agent Todo

| # | Task | Status | 의존성 |
|---|------|--------|--------|
| R1 | 🔴 `test_stream_service.py` 작성 (TDD Red) | pending | Auth, Cache, Content |
| R2 | 🟢 `models.py` - StreamInfo, Range 모델 | pending | R1 |
| R3 | 🟢 `service.py` - StreamService 구현 | pending | R2 |
| R4 | 🟢 `range_handler.py` - HTTP Range 처리 | pending | R3 |
| R5 | 🟢 `router.py` - 스트리밍 엔드포인트 | pending | R4 |
| R6 | ✅ 테스트 통과 확인 (Auth, Cache, Content Mock) | pending | R5 |
| R7 | ♻️ 리팩토링 | pending | R6 |
| R8 | 📝 `docs/blocks/03-stream.md` 업데이트 | pending | R7 |

**의존성 계약**:
```python
# Auth Block으로부터:
auth.validate_token(token) -> User | None

# Cache Block으로부터:
cache.get_stream_path(content_id) -> Path
cache.acquire_stream_slot(user_id) -> (bool, str)

# Content Block으로부터:
content.get_metadata(content_id) -> ContentMeta
```

**이벤트 발행**:
- `stream.started` → Admin (실시간 모니터링), Cache (접근 추적)
- `stream.ended` → Admin (통계), Content (진행률 저장)

---

### Admin Agent Todo

| # | Task | Status | 의존성 |
|---|------|--------|--------|
| D1 | 🔴 `test_admin_service.py` 작성 (TDD Red) | pending | Auth, All Blocks |
| D2 | 🟢 `models.py` - Dashboard, Stats 모델 | pending | D1 |
| D3 | 🟢 `service.py` - AdminService 구현 | pending | D2 |
| D4 | 🟢 `dashboard.py` - 대시보드 데이터 | pending | D3 |
| D5 | 🟢 `user_management.py` - 사용자 승인 | pending | D3 |
| D6 | 🟢 `router.py` - 관리자 API | pending | D4, D5 |
| D7 | ✅ 테스트 통과 확인 (All Blocks Mock) | pending | D6 |
| D8 | ♻️ 리팩토링 | pending | D7 |
| D9 | 📝 `docs/blocks/05-admin.md` 업데이트 | pending | D8 |

**이벤트 구독** (모든 블럭 모니터링):
- `auth.*` → 사용자 활동 통계
- `content.*` → 콘텐츠 통계
- `stream.*` → 실시간 스트리밍 모니터링
- `cache.*` → 캐시 히트율 모니터링
- `worker.*` → 작업 큐 상태

---

## 통합 테스트 Todo (모든 블럭 완료 후)

| # | Task | Status | 의존성 |
|---|------|--------|--------|
| I1 | 전체 블럭 통합 테스트 시나리오 작성 | pending | All Waves |
| I2 | E2E: 회원가입 → 승인 → 로그인 플로우 | pending | I1 |
| I3 | E2E: 콘텐츠 검색 → 상세 → 스트리밍 플로우 | pending | I1 |
| I4 | E2E: 관리자 대시보드 시나리오 | pending | I1 |
| I5 | 장애 격리 테스트 (한 블럭 다운 시) | pending | I1 |
| I6 | 성능 테스트 (동시 스트리밍 10명) | pending | I1 |
| I7 | 최종 검증 및 문서 업데이트 | pending | I2-I6 |

---

## 에이전트 호출 예시

```python
# Wave 1: 병렬 시작
Task(subagent_type="general-purpose", prompt="Auth Agent: Todo A1-A7 실행", description="Auth Block 개발")
Task(subagent_type="general-purpose", prompt="Cache Agent: Todo C1-C10 실행", description="Cache Block 개발")

# Wave 2: Wave 1 완료 후 병렬 시작
Task(subagent_type="general-purpose", prompt="Content Agent: Todo T1-T7 실행", description="Content Block 개발")
Task(subagent_type="general-purpose", prompt="Search Agent: Todo S1-S8 실행", description="Search Block 개발")
Task(subagent_type="general-purpose", prompt="Worker Agent: Todo W1-W9 실행", description="Worker Block 개발")

# Wave 3: Wave 2 완료 후 병렬 시작
Task(subagent_type="general-purpose", prompt="Stream Agent: Todo R1-R8 실행", description="Stream Block 개발")
Task(subagent_type="general-purpose", prompt="Admin Agent: Todo D1-D9 실행", description="Admin Block 개발")
```

---

## 진행 상황 추적

| Wave | 블럭 | Status | Progress |
|------|------|--------|----------|
| 0 | Orchestration | ✅ 완료 | 7/7 |
| 1 | Auth | ✅ 완료 | 7/7 |
| 1 | Cache | ✅ 완료 | 10/10 |
| 2 | Content | ✅ 완료 | 7/7 |
| 2 | Search | ✅ 완료 | 8/8 |
| 2 | Worker | ✅ 완료 | 9/9 |
| 3 | Stream | ✅ 완료 | 8/8 |
| 3 | Admin | ✅ 완료 | 9/9 |
| - | Integration | 🔄 진행 중 | 0/7 |

**Total**: 65/72 tasks (90%)

### 테스트 현황
- **전체 테스트**: 131개 PASSED
- **커버리지**: 82%
- **실행 시간**: 2.64s

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-11 | Claude Code | Initial parallel dev plan |
