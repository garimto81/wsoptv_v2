# Content Agent Todo

**Block**: Content (L1 - Auth, Cache 의존)
**Agent**: content-agent
**Wave**: 2 (Wave 1 완료 후)

---

## 컨텍스트 제한

```
✅ 수정 가능:
  - src/blocks/content/**
  - tests/test_blocks/test_content_block.py
  - docs/blocks/02-content.md

❌ 수정 불가:
  - src/blocks/*/ (다른 블럭)
  - src/orchestration/ (읽기 전용)

🔗 의존성 (Mock으로 테스트):
  - auth.validate_token()
  - auth.check_permission()
  - cache.get()
  - cache.set()
```

---

## 선행 조건

⏳ **Wave 1 완료 대기**:
- [ ] Auth Block 완료
- [ ] Cache Block 완료

---

## Todo List

### TDD Red Phase
- [ ] T1: `tests/test_blocks/test_content_block.py` 확장
  - [ ] test_get_content
  - [ ] test_get_catalog
  - [ ] test_update_watch_progress
  - [ ] test_content_metadata
  - [ ] test_requires_auth_validation
  - [ ] test_uses_cache_for_metadata

### TDD Green Phase
- [ ] T2: `src/blocks/content/models.py`
  - [ ] Content 모델 (id, title, duration, file_size, codec, resolution, path)
  - [ ] ContentMeta 모델 (light version for API)
  - [ ] Catalog 모델 (items, total, page, size)
  - [ ] WatchProgress 모델 (user_id, content_id, position, percentage)

- [ ] T3: `src/blocks/content/service.py`
  - [ ] get_content(content_id, token) → Content
  - [ ] get_catalog(page, size) → Catalog
  - [ ] update_progress(user_id, content_id, position, total) → None
  - [ ] get_progress(user_id, content_id) → WatchProgress
  - [ ] get_metadata(content_id) → ContentMeta

- [ ] T4: `src/blocks/content/router.py`
  - [ ] GET /content/{id}
  - [ ] GET /content (catalog)
  - [ ] POST /content/{id}/progress
  - [ ] GET /content/{id}/progress

- [ ] T5: 테스트 통과 확인 (Auth, Cache Mock)
  - [ ] pytest tests/test_blocks/test_content_block.py -v
  - [ ] 커버리지 80% 이상

### Refactor Phase
- [ ] T6: 코드 리팩토링
  - [ ] 캐시 전략 최적화
  - [ ] 페이지네이션 최적화

- [ ] T7: 문서 업데이트
  - [ ] docs/blocks/02-content.md API 섹션 업데이트

---

## 의존성 계약 (사용)

```python
# Auth Block API (Mock으로 테스트)
auth.validate_token(token: str) -> TokenResult
auth.check_permission(user_id: str, resource: str) -> bool

# Cache Block API (Mock으로 테스트)
cache.get(key: str) -> Any | None
cache.set(key: str, value: Any, ttl: int) -> None
```

## 이벤트 발행 (Orchestration 통해)

```python
await bus.publish("content.added", BlockMessage(...))
await bus.publish("content.viewed", BlockMessage(...))
await bus.publish("content.progress_updated", BlockMessage(...))
```

## 제공 API (Contract)

```python
# 다른 블럭이 호출할 수 있는 API
get_metadata(content_id: str) -> ContentMeta
get_content(content_id: str) -> Content
```

---

## Progress: 0/7 (0%)
**Status**: ⏳ Blocked (Wave 1 대기)
