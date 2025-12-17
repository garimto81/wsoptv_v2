# Admin Agent Todo

**Block**: Admin (L2 - All Blocks 의존)
**Agent**: admin-agent
**Wave**: 3 (Wave 2 완료 후)

---

## 컨텍스트 제한

```
✅ 수정 가능:
  - src/blocks/admin/**
  - tests/test_blocks/test_admin_block.py
  - docs/blocks/05-admin.md

❌ 수정 불가:
  - src/blocks/*/ (다른 블럭)
  - src/orchestration/ (읽기 전용)

🔗 의존성 (Mock으로 테스트):
  - auth.validate_token()
  - auth.check_permission() (is_admin)
  - auth.approve_user()
  - 모든 블럭 이벤트 구독
```

---

## 선행 조건

⏳ **Wave 2 완료 대기**:
- [ ] Auth Block 완료
- [ ] Cache Block 완료
- [ ] Content Block 완료
- [ ] Search Block 완료
- [ ] Worker Block 완료

---

## Todo List

### TDD Red Phase
- [ ] D1: `tests/test_blocks/test_admin_block.py` 작성
  - [ ] test_dashboard_data
  - [ ] test_user_list
  - [ ] test_approve_user
  - [ ] test_system_stats
  - [ ] test_stream_monitoring
  - [ ] test_requires_admin_permission

### TDD Green Phase
- [ ] D2: `src/blocks/admin/models.py`
  - [ ] DashboardData 모델 (user_stats, content_stats, stream_stats)
  - [ ] UserStats 모델 (total, pending, active, suspended)
  - [ ] ContentStats 모델 (total, by_category, storage_used)
  - [ ] StreamStats 모델 (active_streams, peak_concurrent, bandwidth_used)
  - [ ] SystemHealth 모델 (blocks_status, redis_status, db_status)

- [ ] D3: `src/blocks/admin/service.py`
  - [ ] get_dashboard(token) → DashboardData
  - [ ] get_user_list(token, page, size) → UserList
  - [ ] approve_user(token, user_id) → User
  - [ ] suspend_user(token, user_id) → User
  - [ ] get_system_stats(token) → SystemHealth
  - [ ] get_active_streams(token) → list[StreamSession]

- [ ] D4: `src/blocks/admin/dashboard.py`
  - [ ] 실시간 통계 집계
  - [ ] 캐시 히트율 계산
  - [ ] 스트리밍 현황 조회

- [ ] D5: `src/blocks/admin/user_management.py`
  - [ ] 사용자 목록 조회
  - [ ] 사용자 승인/정지
  - [ ] 권한 관리

- [ ] D6: `src/blocks/admin/router.py`
  - [ ] GET /admin/dashboard
  - [ ] GET /admin/users
  - [ ] POST /admin/users/{id}/approve
  - [ ] POST /admin/users/{id}/suspend
  - [ ] GET /admin/system
  - [ ] GET /admin/streams

- [ ] D7: 테스트 통과 확인 (All Blocks Mock)
  - [ ] pytest tests/test_blocks/test_admin_block.py -v
  - [ ] 커버리지 80% 이상

### Refactor Phase
- [ ] D8: 코드 리팩토링
  - [ ] 실시간 WebSocket 업데이트
  - [ ] 통계 캐싱 최적화
  - [ ] 대시보드 성능 개선

- [ ] D9: 문서 업데이트
  - [ ] docs/blocks/05-admin.md API 섹션 업데이트

---

## 이벤트 구독 (모든 블럭 모니터링)

```python
# Auth Block 이벤트
@bus.subscribe("auth.user_registered")
async def on_user_registered(msg): ...

@bus.subscribe("auth.user_login")
async def on_user_login(msg): ...

# Content Block 이벤트
@bus.subscribe("content.viewed")
async def on_content_viewed(msg): ...

# Stream Block 이벤트
@bus.subscribe("stream.started")
async def on_stream_started(msg): ...

@bus.subscribe("stream.ended")
async def on_stream_ended(msg): ...

# Cache Block 이벤트
@bus.subscribe("cache.miss")
async def on_cache_miss(msg): ...

# Worker Block 이벤트
@bus.subscribe("worker.task_completed")
async def on_task_completed(msg): ...
```

---

## Admin 권한 체크

```python
async def require_admin(token: str):
    result = await auth.validate_token(token)
    if not result.valid:
        raise AuthError("Invalid token")

    user = await auth.get_user(result.user_id)
    if not user.is_admin:
        raise PermissionError("Admin permission required")
```

---

## 대시보드 데이터 구조

```json
{
  "user_stats": {
    "total": 150,
    "pending": 5,
    "active": 140,
    "suspended": 5
  },
  "content_stats": {
    "total": 500,
    "storage_used_gb": 18000,
    "by_category": {...}
  },
  "stream_stats": {
    "active_streams": 12,
    "peak_today": 25,
    "bandwidth_mbps": 240
  },
  "cache_stats": {
    "hit_rate": 0.85,
    "ssd_usage_gb": 450,
    "hot_contents": 120
  },
  "system_health": {
    "api": "healthy",
    "redis": "healthy",
    "postgres": "healthy",
    "meilisearch": "healthy"
  }
}
```

---

## Progress: 0/9 (0%)
**Status**: ⏳ Blocked (Wave 2 대기)
