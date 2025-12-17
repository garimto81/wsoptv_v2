# Stream Agent Todo

**Block**: Stream (L2 - Auth, Cache, Content 의존)
**Agent**: stream-agent
**Wave**: 3 (Wave 2 완료 후)

---

## 컨텍스트 제한

```
✅ 수정 가능:
  - src/blocks/stream/**
  - tests/test_blocks/test_stream_block.py
  - docs/blocks/03-stream.md

❌ 수정 불가:
  - src/blocks/*/ (다른 블럭)
  - src/orchestration/ (읽기 전용)

🔗 의존성 (Mock으로 테스트):
  - auth.validate_token()
  - cache.get_stream_path()
  - cache.acquire_stream_slot()
  - cache.release_stream_slot()
  - content.get_metadata()
```

---

## 선행 조건

⏳ **Wave 2 완료 대기**:
- [ ] Auth Block 완료
- [ ] Cache Block 완료
- [ ] Content Block 완료

---

## Todo List

### TDD Red Phase
- [ ] R1: `tests/test_blocks/test_stream_block.py` 확장
  - [ ] test_get_stream_url
  - [ ] test_range_request_206
  - [ ] test_stream_from_cache_tier
  - [ ] test_concurrent_stream_limit
  - [ ] test_bandwidth_throttling
  - [ ] test_stream_started_event
  - [ ] test_stream_ended_event

### TDD Green Phase
- [ ] R2: `src/blocks/stream/models.py`
  - [ ] StreamInfo 모델 (url, content_type, content_length)
  - [ ] RangeRequest 모델 (start_byte, end_byte)
  - [ ] RangeResponse 모델 (status_code, content_length, content_range, data)
  - [ ] StreamSource 모델 (path, tier)
  - [ ] StreamSession 모델 (user_id, content_id, started_at)
  - [ ] BandwidthInfo 모델 (limit_mbps, current_mbps)

- [ ] R3: `src/blocks/stream/service.py`
  - [ ] get_stream_url(content_id, token) → StreamInfo
  - [ ] get_range(content_id, start, end) → RangeResponse
  - [ ] get_stream_source(content_id) → StreamSource
  - [ ] start_stream(user_id, content_id) → StreamResult
  - [ ] end_stream(user_id, content_id) → None
  - [ ] get_user_bandwidth(user_id) → BandwidthInfo

- [ ] R4: `src/blocks/stream/range_handler.py`
  - [ ] parse_range_header(header) → RangeRequest
  - [ ] build_range_response(request, file_path) → RangeResponse
  - [ ] stream_file_range(file_path, start, end) → AsyncGenerator

- [ ] R5: `src/blocks/stream/router.py`
  - [ ] GET /stream/{content_id} (스트리밍 URL)
  - [ ] GET /stream/{content_id}/video (실제 스트리밍, Range 지원)
  - [ ] POST /stream/{content_id}/start
  - [ ] POST /stream/{content_id}/end

- [ ] R6: 테스트 통과 확인 (Auth, Cache, Content Mock)
  - [ ] pytest tests/test_blocks/test_stream_block.py -v
  - [ ] 커버리지 80% 이상

### Refactor Phase
- [ ] R7: 코드 리팩토링
  - [ ] 대용량 파일 효율적 스트리밍
  - [ ] 청크 사이즈 최적화 (1MB)
  - [ ] 동시 스트리밍 최적화

- [ ] R8: 문서 업데이트
  - [ ] docs/blocks/03-stream.md API 섹션 업데이트

---

## 의존성 계약 (사용)

```python
# Auth Block API
auth.validate_token(token: str) -> TokenResult

# Cache Block API
cache.get_stream_path(content_id: str) -> Path
cache.acquire_stream_slot(user_id: str) -> tuple[bool, str]
cache.release_stream_slot(user_id: str) -> None

# Content Block API
content.get_metadata(content_id: str) -> ContentMeta
```

## 이벤트 발행 (Orchestration 통해)

```python
await bus.publish("stream.started", BlockMessage(
    payload={"user_id": user_id, "content_id": content_id}
))
await bus.publish("stream.ended", BlockMessage(
    payload={"user_id": user_id, "content_id": content_id, "duration": duration}
))
```

---

## HTTP Range Streaming 구조

```
Client Request:
  GET /stream/video123/video
  Range: bytes=0-1048575

Server Response:
  HTTP/1.1 206 Partial Content
  Content-Type: video/mp4
  Content-Length: 1048576
  Content-Range: bytes 0-1048575/104857600
  Accept-Ranges: bytes

  [1MB chunk data]
```

---

## 스트리밍 제한

| 항목 | 제한 |
|------|------|
| 사용자당 동시 스트림 | 3개 |
| 대역폭 제한 | 설정 가능 |
| 청크 사이즈 | 1MB |

---

## Progress: 0/8 (0%)
**Status**: ⏳ Blocked (Wave 2 대기)
