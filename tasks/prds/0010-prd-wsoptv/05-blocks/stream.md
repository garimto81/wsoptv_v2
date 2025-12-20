# Stream Block PRD

**Version**: 2.0.0 | **Block ID**: stream | **Level**: L2 (Depends on auth, cache, content)

---

## 1. Overview

Stream Block은 WSOPTV의 핵심 기능인 **비디오 스트리밍**을 담당합니다.

### 책임 범위

| 책임 영역 | 세부 기능 |
|----------|----------|
| **Direct Play** | 트랜스코딩 없이 원본 파일 직접 스트리밍 |
| **HTTP Range** | 206 Partial Content 지원 (Seek 기능) |
| **Rate Limiting** | 동시 스트림 제한 (서버/사용자당) |
| **Session** | 스트림 세션 추적 및 상태 관리 |
| **Hand Skip** | 핸드 건너뛰기 구간 정보 제공 |

### Non-Goals

- 트랜스코딩 (원본 H.264/AAC만)
- DRM 암호화
- 적응형 스트리밍 (HLS/DASH)
- 라이브 스트리밍 (VOD only)

---

## 2. API Endpoints

### 스트리밍

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/stream/{content_id}` | 비디오 스트리밍 |
| GET | `/api/stream/{content_id}/info` | 스트림 정보 (핸드 구간 포함) |

### 세션 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/stream/{content_id}/start` | 스트림 세션 시작 |
| POST | `/api/stream/{content_id}/end` | 스트림 세션 종료 |
| POST | `/api/stream/{content_id}/heartbeat` | 세션 유지 |

---

## 3. Streaming Flow

```
1. 클라이언트 요청
   GET /api/stream/{content_id}
   Headers: Range: bytes=0-1023, Authorization: Bearer ...

2. Rate Limit 확인
   전체: 100개, 사용자당: 3개

3. 인증 검증 (Auth Block)
   validate_token() → User

4. 파일 경로 획득 (Cache Block)
   get_stream_path() → SSD 또는 NAS 경로

5. Range 헤더 처리
   bytes=start-end → chunk 계산

6. 스트림 응답
   206 Partial Content + Content-Range 헤더
```

---

## 4. HTTP Range Streaming

### Request

```http
GET /api/stream/content-123 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Range: bytes=0-1023
```

### Response (206 Partial Content)

```http
HTTP/1.1 206 Partial Content
Content-Type: video/mp4
Content-Range: bytes 0-1023/157832094
Accept-Ranges: bytes
Content-Length: 1024

[비디오 데이터 1KB]
```

---

## 5. Rate Limiting

| 제한 유형 | 값 | 설명 |
|----------|---|------|
| 전체 동시 스트림 | 100개 | 서버 전체 제한 |
| 사용자당 동시 스트림 | 3개 | 개별 사용자 제한 |
| 세션 타임아웃 | 30분 | heartbeat 없으면 종료 |

### 에러 응답

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Maximum concurrent streams reached",
    "details": {
      "current": 3,
      "limit": 3
    }
  }
}
```

---

## 6. Hand Skip Integration

### Stream Info 응답

```json
{
  "content_id": "content-123",
  "duration_seconds": 8100,
  "hands": [
    {"index": 1, "start": 45, "end": 180, "is_best": false},
    {"index": 2, "start": 210, "end": 420, "is_best": true},
    ...
  ],
  "skip_zones": [
    {"start": 180, "end": 210},
    {"start": 420, "end": 480},
    ...
  ],
  "best_hands_count": 12,
  "action_duration": 3120
}
```

---

## 7. Events

### 발행 이벤트

| 채널 | 페이로드 | 설명 |
|------|----------|------|
| `stream.started` | `{content_id, user_id, session_id}` | 스트림 시작 |
| `stream.ended` | `{content_id, user_id, watch_duration}` | 스트림 종료 |
| `stream.error` | `{content_id, error_code}` | 스트림 에러 |

---

## 8. Contracts

### 의존 계약 (호출)

```python
# Auth Block
auth.validate_token(token) -> User

# Cache Block
cache.get_stream_path(content_id) -> str
cache.check_rate_limit(user_id) -> bool

# Content Block
content.get_file_path(content_id) -> str
content.get_best_hands(content_id) -> list[BestHand]
```

---

*Parent: [04-technical.md](../04-technical.md)*
