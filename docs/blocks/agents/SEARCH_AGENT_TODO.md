# Search Agent Todo

**Block**: Search (L1 - Auth 의존)
**Agent**: search-agent
**Wave**: 2 (Wave 1 완료 후)

---

## 컨텍스트 제한

```
✅ 수정 가능:
  - src/blocks/search/**
  - tests/test_blocks/test_search_block.py
  - docs/blocks/06-search.md

❌ 수정 불가:
  - src/blocks/*/ (다른 블럭)
  - src/orchestration/ (읽기 전용)

🔗 의존성 (Mock으로 테스트):
  - auth.validate_token()
```

---

## 선행 조건

⏳ **Wave 1 완료 대기**:
- [ ] Auth Block 완료

---

## Todo List

### TDD Red Phase
- [ ] S1: `tests/test_blocks/test_search_block.py` 작성
  - [ ] test_search_by_keyword
  - [ ] test_search_with_filters
  - [ ] test_search_pagination
  - [ ] test_meilisearch_fallback_to_postgres
  - [ ] test_index_content
  - [ ] test_remove_from_index

### TDD Green Phase
- [ ] S2: `src/blocks/search/models.py`
  - [ ] SearchQuery 모델 (keyword, filters, page, size)
  - [ ] SearchResult 모델 (items, total, took_ms)
  - [ ] SearchItem 모델 (id, title, score, highlights)

- [ ] S3: `src/blocks/search/service.py`
  - [ ] search(query: SearchQuery, token) → SearchResult
  - [ ] index_content(content: Content) → None
  - [ ] remove_from_index(content_id) → None
  - [ ] reindex_all() → int (indexed count)

- [ ] S4: `src/blocks/search/fallback.py`
  - [ ] PostgreSQL LIKE 검색 (MeiliSearch 장애 시)
  - [ ] Circuit Breaker 패턴

- [ ] S5: `src/blocks/search/router.py`
  - [ ] GET /search?q={keyword}&page={page}&size={size}
  - [ ] POST /search/reindex (admin only)

- [ ] S6: 테스트 통과 확인 (Auth Mock)
  - [ ] pytest tests/test_blocks/test_search_block.py -v
  - [ ] 커버리지 80% 이상

### Refactor Phase
- [ ] S7: 코드 리팩토링
  - [ ] MeiliSearch 연결 풀링
  - [ ] 인덱스 최적화
  - [ ] Fallback 성능 개선

- [ ] S8: 문서 업데이트
  - [ ] docs/blocks/06-search.md API 섹션 업데이트

---

## 이벤트 구독 (Orchestration 통해)

```python
# Content Block 이벤트 구독
@bus.subscribe("content.added")
async def on_content_added(msg: BlockMessage):
    await search_service.index_content(msg.payload)

@bus.subscribe("content.updated")
async def on_content_updated(msg: BlockMessage):
    await search_service.index_content(msg.payload)

@bus.subscribe("content.deleted")
async def on_content_deleted(msg: BlockMessage):
    await search_service.remove_from_index(msg.payload["content_id"])
```

## 제공 API (Contract)

```python
# 다른 블럭이 호출할 수 있는 API
search(query: SearchQuery) -> SearchResult
```

---

## MeiliSearch + Fallback 구조

```
Request → MeiliSearch
              │
         Circuit Breaker
              │
         ┌────┴────┐
         │ 정상    │ 장애
         ▼         ▼
    MeiliSearch  PostgreSQL
     Results     LIKE Query
```

---

## Progress: 0/8 (0%)
**Status**: ⏳ Blocked (Wave 1 대기)
