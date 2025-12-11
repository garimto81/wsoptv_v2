# Worker Agent Todo

**Block**: Worker (L1 - Cache 의존)
**Agent**: worker-agent
**Wave**: 2 (Wave 1 완료 후)

---

## 컨텍스트 제한

```
✅ 수정 가능:
  - src/blocks/worker/**
  - tests/test_blocks/test_worker_block.py
  - docs/blocks/07-worker.md

❌ 수정 불가:
  - src/blocks/*/ (다른 블럭)
  - src/orchestration/ (읽기 전용)

🔗 의존성 (Mock으로 테스트):
  - cache.get_stream_path()
  - cache.set()
```

---

## 선행 조건

⏳ **Wave 1 완료 대기**:
- [ ] Cache Block 완료

---

## Todo List

### TDD Red Phase
- [ ] W1: `tests/test_blocks/test_worker_block.py` 작성
  - [ ] test_enqueue_task
  - [ ] test_process_thumbnail_task
  - [ ] test_process_cache_warm_task
  - [ ] test_process_nas_scan_task
  - [ ] test_task_priority
  - [ ] test_task_retry_on_failure

### TDD Green Phase
- [ ] W2: `src/blocks/worker/models.py`
  - [ ] Task 모델 (id, type, payload, priority, status, retries)
  - [ ] TaskType Enum (THUMBNAIL, CACHE_WARM, NAS_SCAN)
  - [ ] TaskStatus Enum (pending, processing, completed, failed)
  - [ ] TaskResult 모델 (success, message, data)

- [ ] W3: `src/blocks/worker/service.py`
  - [ ] enqueue(task_type, payload, priority) → Task
  - [ ] process_next() → TaskResult
  - [ ] get_queue_status() → dict
  - [ ] retry_failed_tasks() → int

- [ ] W4: `src/blocks/worker/workers/thumbnail.py`
  - [ ] ThumbnailWorker 클래스
  - [ ] FFmpeg 연동 (스크린샷 추출)
  - [ ] 3개 썸네일 생성 (25%, 50%, 75% 지점)

- [ ] W5: `src/blocks/worker/workers/cache_warmer.py`
  - [ ] CacheWarmerWorker 클래스
  - [ ] NAS → SSD 파일 복사
  - [ ] Hot content 자동 감지

- [ ] W6: `src/blocks/worker/workers/nas_scanner.py`
  - [ ] NASScannerWorker 클래스
  - [ ] NAS 디렉토리 스캔
  - [ ] 새 콘텐츠 자동 등록

- [ ] W7: 테스트 통과 확인 (Cache Mock)
  - [ ] pytest tests/test_blocks/test_worker_block.py -v
  - [ ] 커버리지 80% 이상

### Refactor Phase
- [ ] W8: 코드 리팩토링
  - [ ] Redis Queue 최적화
  - [ ] Worker 동시성 제어
  - [ ] Dead letter queue

- [ ] W9: 문서 업데이트
  - [ ] docs/blocks/07-worker.md API 섹션 업데이트

---

## 이벤트 구독 (Orchestration 통해)

```python
# Cache Block 이벤트 구독
@bus.subscribe("cache.miss")
async def on_cache_miss(msg: BlockMessage):
    # 캐시 워밍 작업 큐잉
    await worker_service.enqueue(TaskType.CACHE_WARM, msg.payload)

# Content Block 이벤트 구독
@bus.subscribe("content.added")
async def on_content_added(msg: BlockMessage):
    # 썸네일 생성 작업 큐잉
    await worker_service.enqueue(TaskType.THUMBNAIL, msg.payload)
```

## 이벤트 발행

```python
await bus.publish("worker.task_completed", BlockMessage(...))
await bus.publish("worker.task_failed", BlockMessage(...))
```

---

## Worker 아키텍처

```
┌─────────────────────────────────────────┐
│             Redis Queue                  │
│  ┌─────────┬─────────┬─────────┐       │
│  │ HIGH    │ NORMAL  │ LOW     │       │
│  │ Priority│ Priority│ Priority│       │
│  └────┬────┴────┬────┴────┬────┘       │
└───────┼─────────┼─────────┼─────────────┘
        │         │         │
        ▼         ▼         ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Thumbnail│ │ Cache   │ │  NAS    │
   │ Worker  │ │ Warmer  │ │ Scanner │
   └─────────┘ └─────────┘ └─────────┘
```

---

## Progress: 0/9 (0%)
**Status**: ⏳ Blocked (Wave 1 대기)
