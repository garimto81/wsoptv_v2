# PRD: Stream Block

**Version**: 1.0.0
**Date**: 2025-12-11
**Block ID**: stream
**전담 에이전트**: stream-agent
**Status**: Draft

---

## 1. Block Overview

Stream Block은 WSOPTV의 핵심 기능인 **비디오 스트리밍**을 담당하는 블럭입니다.

### 1.1 책임 (Responsibilities)

| 책임 | 설명 |
|------|------|
| **Direct Play** | 트랜스코딩 없이 원본 파일 직접 스트리밍 |
| **HTTP Range Streaming** | 206 Partial Content 지원 (Seek 기능) |
| **Rate Limiting** | 동시 스트림 제한 (서버/사용자당) |
| **Session Management** | 스트림 세션 추적 및 상태 관리 |
| **Progress Tracking** | 시청 진행률 저장 및 조회 |

### 1.2 핵심 기능

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Stream Block Flow                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 클라이언트 요청                                                  │
│     GET /api/stream/{content_id}                                    │
│     Headers: Range: bytes=0-1023, Authorization: Bearer ...        │
│                    │                                                 │
│                    ▼                                                 │
│  2. Rate Limit 확인                                                 │
│     전체: 20개, 사용자당: 3개                                        │
│                    │                                                 │
│                    ▼                                                 │
│  3. 인증 검증 (Auth Block)                                          │
│     validate_token() → User                                         │
│                    │                                                 │
│                    ▼                                                 │
│  4. 파일 경로 획득 (Cache Block)                                    │
│     get_stream_path() → SSD or NAS 경로                            │
│                    │                                                 │
│                    ▼                                                 │
│  5. Range 헤더 처리                                                 │
│     bytes=start-end → chunk 계산                                    │
│                    │                                                 │
│                    ▼                                                 │
│  6. 스트림 응답                                                      │
│     206 Partial Content + Content-Range 헤더                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Non-Goals (제외 범위)

- **트랜스코딩**: 원본 파일만 스트리밍 (H.264/AAC 필수)
- **DRM**: 암호화/보호 없음 (프라이빗 플랫폼)
- **적응형 스트리밍**: HLS/DASH 미지원 (단일 비트레이트)
- **라이브 스트리밍**: VOD만 지원

---

## 2. Agent Rules

Stream Block 전담 에이전트는 다음 규칙을 엄격히 준수해야 합니다.

### 2.1 컨텍스트 제한

| 규칙 | 설명 |
|------|------|
| **읽기 가능 파일** | `api/app/blocks/stream/`, `docs/blocks/03-stream.md` |
| **수정 가능 파일** | `api/app/blocks/stream/**/*`, `tests/blocks/stream/**/*` |
| **수정 불가 파일** | `api/app/blocks/auth/`, `api/app/blocks/cache/` (다른 블럭) |
| **오케스트레이터** | 읽기 전용 (`api/app/orchestration/contracts/`) |

### 2.2 블럭 간 통신 규칙

```python
# ❌ 금지: 다른 블럭 직접 import
from api.app.blocks.auth.service import AuthService  # NEVER
from api.app.blocks.cache.service import CacheService  # NEVER

# ✅ 허용: 오케스트레이터 경유
from api.app.orchestration.contracts.auth import AuthBlockAPI
from api.app.orchestration.contracts.cache import CacheBlockAPI

class StreamService:
    def __init__(self, orchestrator: Orchestrator):
        self.auth: AuthBlockAPI = orchestrator.get_block("auth")
        self.cache: CacheBlockAPI = orchestrator.get_block("cache")

    async def start_stream(self, content_id: str, token: str):
        # Auth Block 호출 (오케스트레이터 경유)
        user = await self.auth.validate_token(token)

        # Cache Block 호출 (오케스트레이터 경유)
        file_path = await self.cache.get_stream_path(content_id)
```

### 2.3 에이전트 지침

**에이전트는 다음만 수행:**

1. Stream Block 내부 코드 작성/수정
2. Stream Block 테스트 작성
3. 이 PRD 문서 업데이트
4. `docs/blocks/03-stream.md` 관리

**에이전트는 절대 수행 금지:**

1. Auth/Cache/Content 블럭 수정
2. 오케스트레이터 코드 수정 (contract 제외)
3. 다른 블럭 직접 import

---

## 3. API Endpoints

### 3.1 GET /api/stream/{content_id}

비디오 스트리밍 (HTTP Range 지원)

**Request**:
```http
GET /api/stream/content-123 HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Range: bytes=0-1023
```

**Response (206 Partial Content)**:
```http
HTTP/1.1 206 Partial Content
Content-Type: video/mp4
Content-Range: bytes 0-1023/157832094
Accept-Ranges: bytes
Content-Length: 1024

[비디오 데이터 1KB]
```

**Response (200 Full Content, Range 없을 때)**:
```http
HTTP/1.1 200 OK
Content-Type: video/mp4
Accept-Ranges: bytes
Content-Length: 157832094

[전체 비디오 데이터]
```

**Error Responses**:

| Status | Code | Message |
|--------|------|---------|
| 401 | `AUTH_INVALID_TOKEN` | "인증 토큰이 유효하지 않습니다." |
| 403 | `AUTH_USER_PENDING` | "승인 대기 중인 계정입니다." |
| 404 | `CONTENT_NOT_FOUND` | "콘텐츠를 찾을 수 없습니다." |
| 429 | `STREAM_RATE_LIMITED` | "서버 동시 접속 한도 초과입니다." |
| 503 | `STREAM_FILE_UNAVAILABLE` | "파일을 찾을 수 없습니다. (NAS 연결 확인)" |

### 3.2 GET /api/stream/{content_id}/info

스트림 정보 조회 (메타데이터)

**Request**:
```http
GET /api/stream/content-123/info HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response (200)**:
```json
{
  "content_id": "content-123",
  "duration": 7320.5,
  "file_size": 157832094,
  "mime_type": "video/mp4",
  "codecs": {
    "video": "H.264",
    "audio": "AAC"
  },
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "bitrate": 8500000,
  "source": "ssd",
  "cache_hit": true
}
```

### 3.3 PUT /api/progress/{content_id}

시청 진행률 저장

**Request**:
```json
{
  "position": 1234.5,
  "duration": 7320.5
}
```

**Response (200)**:
```json
{
  "success": true,
  "progress_percent": 17
}
```

### 3.4 GET /api/progress/{content_id}

시청 진행률 조회

**Response (200)**:
```json
{
  "content_id": "content-123",
  "position": 1234.5,
  "duration": 7320.5,
  "progress_percent": 17,
  "updated_at": "2025-12-11T10:30:00Z"
}
```

---

## 4. Data Models

### 4.1 StreamSession

스트리밍 세션 정보

```python
from datetime import datetime
from pydantic import BaseModel

class StreamSession(BaseModel):
    """스트림 세션"""
    session_id: str              # 세션 ID (UUID)
    user_id: str                 # 사용자 ID
    content_id: str              # 콘텐츠 ID
    started_at: datetime         # 시작 시간
    last_activity: datetime      # 마지막 활동
    status: StreamStatus         # 세션 상태
    source: str                  # "ssd" | "nas"
    bytes_transferred: int       # 전송된 바이트

class StreamStatus(str, Enum):
    STREAMING = "streaming"      # 스트리밍 중
    PAUSED = "paused"            # 일시정지
    STOPPED = "stopped"          # 종료
    ERROR = "error"              # 오류
```

### 4.2 WatchProgress

시청 진행률

```python
class WatchProgress(BaseModel):
    """시청 진행률"""
    user_id: str                 # 사용자 ID
    content_id: str              # 콘텐츠 ID
    position: float              # 현재 위치 (초)
    duration: float              # 전체 길이 (초)
    progress_percent: int        # 진행률 (0-100)
    updated_at: datetime         # 업데이트 시간
```

### 4.3 StreamMetrics

스트림 메트릭 (모니터링용)

```python
class StreamMetrics(BaseModel):
    """스트림 메트릭"""
    active_streams: int          # 현재 활성 스트림 수
    total_streams_today: int     # 오늘 총 스트림 수
    bandwidth_mbps: float        # 현재 대역폭 (Mbps)
    cache_hit_rate: float        # 캐시 히트율 (0.0-1.0)
    avg_session_duration: float  # 평균 세션 시간 (초)
```

---

## 5. Provided Contracts

Stream Block이 다른 블럭에게 제공하는 인터페이스

### 5.1 StreamBlockAPI

```python
# api/app/orchestration/contracts/stream.py

from abc import ABC, abstractmethod
from pathlib import Path

class StreamBlockAPI(ABC):
    """Stream Block 인터페이스 계약"""

    @abstractmethod
    async def start_stream(
        self,
        content_id: str,
        user_id: str
    ) -> StreamSession:
        """
        스트림 시작

        Args:
            content_id: 콘텐츠 ID
            user_id: 사용자 ID

        Returns:
            StreamSession: 세션 정보

        Raises:
            StreamRateLimitError: Rate Limit 초과
            ContentNotFoundError: 콘텐츠 없음
        """
        pass

    @abstractmethod
    async def stop_stream(self, session_id: str) -> None:
        """
        스트림 종료

        Args:
            session_id: 세션 ID
        """
        pass

    @abstractmethod
    async def get_stream_metrics(self) -> StreamMetrics:
        """
        스트림 메트릭 조회

        Returns:
            StreamMetrics: 메트릭 정보
        """
        pass

    @abstractmethod
    async def get_progress(
        self,
        user_id: str,
        content_id: str
    ) -> WatchProgress | None:
        """
        시청 진행률 조회

        Args:
            user_id: 사용자 ID
            content_id: 콘텐츠 ID

        Returns:
            WatchProgress | None: 진행률 (없으면 None)
        """
        pass

    @abstractmethod
    async def update_progress(
        self,
        user_id: str,
        content_id: str,
        position: float,
        duration: float
    ) -> WatchProgress:
        """
        시청 진행률 업데이트

        Args:
            user_id: 사용자 ID
            content_id: 콘텐츠 ID
            position: 현재 위치 (초)
            duration: 전체 길이 (초)

        Returns:
            WatchProgress: 업데이트된 진행률
        """
        pass
```

---

## 6. Required Contracts

Stream Block이 다른 블럭에 의존하는 인터페이스

### 6.1 AuthBlockAPI

```python
# Stream Block이 Auth Block에 요청하는 API

async def validate_token(self, token: str) -> User | None:
    """
    토큰 검증

    Args:
        token: JWT 토큰

    Returns:
        User | None: 사용자 정보 (유효하지 않으면 None)
    """
    pass
```

**사용 예시**:
```python
user = await self.auth.validate_token(token)
if not user:
    raise HTTPException(401, "Invalid token")
```

### 6.2 CacheBlockAPI

```python
# Stream Block이 Cache Block에 요청하는 API

async def get_stream_path(
    self,
    content_id: str
) -> tuple[Path, str]:
    """
    스트리밍용 파일 경로 획득

    Args:
        content_id: 콘텐츠 ID

    Returns:
        tuple[Path, str]: (파일 경로, 소스 타입 "ssd"|"nas")

    Raises:
        FileNotFoundError: 파일 없음
    """
    pass

async def acquire_stream_slot(self, user_id: str) -> tuple[bool, str]:
    """
    스트림 슬롯 획득 (Rate Limiting)

    Args:
        user_id: 사용자 ID

    Returns:
        tuple[bool, str]: (허용 여부, 메시지)
    """
    pass

async def release_stream_slot(self, user_id: str) -> None:
    """
    스트림 슬롯 반환

    Args:
        user_id: 사용자 ID
    """
    pass
```

**사용 예시**:
```python
# Rate Limit 확인
allowed, msg = await self.cache.acquire_stream_slot(user.id)
if not allowed:
    raise HTTPException(429, msg)

# 파일 경로 획득
file_path, source = await self.cache.get_stream_path(content_id)

# 스트리밍 완료 후 슬롯 반환
await self.cache.release_stream_slot(user.id)
```

### 6.3 ContentBlockAPI

```python
# Stream Block이 Content Block에 요청하는 API

async def get_content(self, content_id: str) -> Content | None:
    """
    콘텐츠 메타데이터 조회

    Args:
        content_id: 콘텐츠 ID

    Returns:
        Content | None: 콘텐츠 정보 (없으면 None)
    """
    pass
```

**사용 예시**:
```python
content = await self.content.get_content(content_id)
if not content:
    raise HTTPException(404, "Content not found")
```

---

## 7. Events Published

Stream Block이 발행하는 이벤트

### 7.1 stream_started

스트림 시작 시 발행

```python
await orchestrator.publish(
    event="stream_started",
    payload={
        "session_id": "session-123",
        "user_id": "user-456",
        "content_id": "content-789",
        "source": "ssd",
        "timestamp": "2025-12-11T10:30:00Z"
    }
)
```

**구독자**: Admin Block (모니터링)

### 7.2 stream_stopped

스트림 종료 시 발행

```python
await orchestrator.publish(
    event="stream_stopped",
    payload={
        "session_id": "session-123",
        "user_id": "user-456",
        "content_id": "content-789",
        "duration_seconds": 1234.5,
        "bytes_transferred": 45678912,
        "timestamp": "2025-12-11T11:00:00Z"
    }
)
```

**구독자**: Admin Block (통계), Worker Block (시청 기록)

### 7.3 stream_error

스트림 오류 시 발행

```python
await orchestrator.publish(
    event="stream_error",
    payload={
        "session_id": "session-123",
        "user_id": "user-456",
        "content_id": "content-789",
        "error_code": "STREAM_FILE_UNAVAILABLE",
        "error_message": "파일을 찾을 수 없습니다.",
        "timestamp": "2025-12-11T10:35:00Z"
    }
)
```

**구독자**: Admin Block (알림), Worker Block (에러 로깅)

---

## 8. HTTP Range Streaming 상세

### 8.1 Range Request 처리

```python
# api/app/blocks/stream/service.py

from fastapi import Request
from fastapi.responses import StreamingResponse
from pathlib import Path

class StreamService:
    async def stream_video(
        self,
        content_id: str,
        request: Request,
        user_id: str
    ) -> StreamingResponse:
        """
        비디오 스트리밍 (Range 지원)
        """
        # 1. 파일 경로 획득
        file_path, source = await self.cache.get_stream_path(content_id)
        file_size = file_path.stat().st_size

        # 2. Range 헤더 파싱
        range_header = request.headers.get("range")

        if range_header:
            # Partial Content (206)
            start, end = self._parse_range(range_header, file_size)
            return StreamingResponse(
                self._stream_chunk(file_path, start, end),
                status_code=206,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Type": "video/mp4",
                    "Content-Length": str(end - start + 1)
                }
            )
        else:
            # Full Content (200)
            return StreamingResponse(
                self._stream_full(file_path),
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Type": "video/mp4",
                    "Content-Length": str(file_size)
                }
            )

    def _parse_range(self, range_header: str, file_size: int) -> tuple[int, int]:
        """
        Range 헤더 파싱

        Examples:
            "bytes=0-1023" → (0, 1023)
            "bytes=0-" → (0, file_size-1)
            "bytes=-500" → (file_size-500, file_size-1)
        """
        range_str = range_header.replace("bytes=", "")

        if range_str.startswith("-"):
            # Last N bytes
            suffix_length = int(range_str[1:])
            start = max(0, file_size - suffix_length)
            end = file_size - 1
        else:
            parts = range_str.split("-")
            start = int(parts[0])
            end = int(parts[1]) if parts[1] else file_size - 1

        # 범위 검증
        start = max(0, start)
        end = min(end, file_size - 1)

        return start, end

    async def _stream_chunk(
        self,
        file_path: Path,
        start: int,
        end: int
    ):
        """
        파일 청크 스트리밍
        """
        chunk_size = 64 * 1024  # 64KB

        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = end - start + 1

            while remaining > 0:
                read_size = min(chunk_size, remaining)
                data = f.read(read_size)

                if not data:
                    break

                remaining -= len(data)
                yield data

    async def _stream_full(self, file_path: Path):
        """
        전체 파일 스트리밍
        """
        chunk_size = 1024 * 1024  # 1MB

        with open(file_path, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data
```

### 8.2 HTTP Range 헤더 예시

| Range 헤더 | 의미 | 응답 범위 (파일 크기 10000) |
|-----------|------|---------------------------|
| `bytes=0-1023` | 처음 1KB | 0-1023 (1024 bytes) |
| `bytes=0-` | 처음부터 끝까지 | 0-9999 (10000 bytes) |
| `bytes=-500` | 마지막 500 bytes | 9500-9999 (500 bytes) |
| `bytes=5000-5999` | 중간 1KB | 5000-5999 (1000 bytes) |
| (없음) | 전체 | 0-9999 (200 OK, 전체) |

### 8.3 브라우저 Seek 동작

```
사용자가 비디오 플레이어에서 50% 위치로 Seek

  1. 브라우저가 자동으로 Range 요청 생성
     GET /api/stream/content-123
     Range: bytes=78916047-78981582  (50% 위치)

  2. 서버가 206 응답
     Content-Range: bytes 78916047-78981582/157832094
     [해당 위치의 비디오 데이터]

  3. 브라우저가 즉시 재생 (버퍼링 최소화)
```

---

## 9. Directory Structure

```
api/app/blocks/stream/
├── __init__.py
├── router.py               # FastAPI 라우터
│   ├── GET /api/stream/{content_id}
│   ├── GET /api/stream/{content_id}/info
│   ├── PUT /api/progress/{content_id}
│   └── GET /api/progress/{content_id}
│
├── service.py              # 비즈니스 로직
│   ├── StreamService
│   │   ├── stream_video()
│   │   ├── get_stream_info()
│   │   ├── start_session()
│   │   └── stop_session()
│   ├── ProgressService
│   │   ├── get_progress()
│   │   └── update_progress()
│   └── RangeParser
│       └── parse_range()
│
├── models.py               # 데이터 모델
│   ├── StreamSession
│   ├── StreamStatus
│   ├── WatchProgress
│   └── StreamMetrics
│
├── errors.py               # 커스텀 예외
│   ├── StreamRateLimitError
│   ├── StreamFileUnavailableError
│   └── StreamSessionNotFoundError
│
└── tests/                  # 테스트
    ├── conftest.py         # 픽스처
    ├── test_router.py      # 엔드포인트 테스트
    ├── test_service.py     # 서비스 테스트
    └── test_range.py       # Range 파싱 테스트
```

---

## 10. Testing Strategy

### 10.1 테스트 범위

| 레벨 | 범위 | 비율 |
|------|------|------|
| **Unit** | Range 파싱, 세션 관리 | 70% |
| **Integration** | API 엔드포인트 + Mock 블럭 | 20% |
| **E2E** | 실제 파일 스트리밍 | 10% |

### 10.2 Unit Tests

```python
# tests/blocks/stream/test_range.py

import pytest
from api.app.blocks.stream.service import RangeParser

class TestRangeParser:
    def test_parse_full_range(self):
        """전체 범위 파싱"""
        start, end = RangeParser.parse("bytes=0-1023", file_size=10000)
        assert start == 0
        assert end == 1023

    def test_parse_open_end_range(self):
        """끝 생략 범위 파싱"""
        start, end = RangeParser.parse("bytes=5000-", file_size=10000)
        assert start == 5000
        assert end == 9999

    def test_parse_suffix_range(self):
        """마지막 N bytes 파싱"""
        start, end = RangeParser.parse("bytes=-500", file_size=10000)
        assert start == 9500
        assert end == 9999

    def test_parse_invalid_range_clamped(self):
        """범위 초과 시 클램핑"""
        start, end = RangeParser.parse("bytes=0-99999", file_size=10000)
        assert start == 0
        assert end == 9999
```

### 10.3 Integration Tests

```python
# tests/blocks/stream/test_router.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

@pytest.fixture
def mock_auth_block():
    """Auth Block Mock"""
    mock = AsyncMock()
    mock.validate_token.return_value = User(
        id="user-1",
        username="testuser",
        status="active"
    )
    return mock

@pytest.fixture
def mock_cache_block(tmp_path):
    """Cache Block Mock"""
    # 테스트용 비디오 파일 생성 (1MB)
    test_file = tmp_path / "test_video.mp4"
    test_file.write_bytes(b"\x00" * 1024 * 1024)

    mock = AsyncMock()
    mock.get_stream_path.return_value = (test_file, "ssd")
    mock.acquire_stream_slot.return_value = (True, "OK")
    return mock

async def test_stream_full_content(client: TestClient, mock_auth_block, mock_cache_block):
    """전체 콘텐츠 스트리밍 (Range 없음)"""
    response = client.get(
        "/api/stream/content-1",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "video/mp4"
    assert response.headers["Accept-Ranges"] == "bytes"
    assert int(response.headers["Content-Length"]) == 1024 * 1024

async def test_stream_partial_content(client: TestClient, mock_auth_block, mock_cache_block):
    """부분 콘텐츠 스트리밍 (Range 있음)"""
    response = client.get(
        "/api/stream/content-1",
        headers={
            "Authorization": "Bearer test-token",
            "Range": "bytes=0-1023"
        }
    )

    assert response.status_code == 206
    assert response.headers["Content-Range"] == "bytes 0-1023/1048576"
    assert int(response.headers["Content-Length"]) == 1024

async def test_stream_rate_limited(client: TestClient, mock_auth_block):
    """Rate Limit 초과 시 429 응답"""
    mock_cache_block = AsyncMock()
    mock_cache_block.acquire_stream_slot.return_value = (False, "동시 재생 3개 초과")

    response = client.get(
        "/api/stream/content-1",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "STREAM_RATE_LIMITED"

async def test_stream_invalid_token(client: TestClient):
    """유효하지 않은 토큰 시 401 응답"""
    mock_auth_block = AsyncMock()
    mock_auth_block.validate_token.return_value = None

    response = client.get(
        "/api/stream/content-1",
        headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401
```

### 10.4 E2E Tests (Playwright)

```typescript
// web/tests/e2e/stream.spec.ts

import { test, expect } from '@playwright/test';

test('비디오 재생 및 Seek', async ({ page }) => {
  // 로그인
  await page.goto('/login');
  await page.fill('[name="username"]', 'testuser');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  // 비디오 페이지 이동
  await page.goto('/watch/content-1');

  // 비디오 플레이어 로드 대기
  const video = await page.locator('video');
  await expect(video).toBeVisible();

  // 자동 재생 확인
  await page.waitForTimeout(2000);
  const currentTime = await video.evaluate((v: HTMLVideoElement) => v.currentTime);
  expect(currentTime).toBeGreaterThan(0);

  // Seek 50%
  await video.evaluate((v: HTMLVideoElement) => {
    v.currentTime = v.duration * 0.5;
  });
  await page.waitForTimeout(1000);

  // Seek 후 재생 확인
  const newTime = await video.evaluate((v: HTMLVideoElement) => v.currentTime);
  expect(newTime).toBeGreaterThan(currentTime);
});

test('동시 재생 3개 제한', async ({ browser }) => {
  const contexts = await Promise.all([
    browser.newContext(),
    browser.newContext(),
    browser.newContext(),
    browser.newContext()
  ]);

  // 각 탭에서 로그인
  for (const ctx of contexts) {
    const page = await ctx.newPage();
    // ... 로그인 로직
  }

  // 3개는 성공
  const pages = await Promise.all(contexts.slice(0, 3).map(c => c.pages()[0]));
  for (const page of pages) {
    await page.goto('/watch/content-1');
    await expect(page.locator('video')).toBeVisible();
  }

  // 4번째는 실패 (429)
  const page4 = await contexts[3].newPage();
  await page4.goto('/watch/content-1');
  await expect(page4.locator('.error-message')).toContainText('동시 재생 3개 초과');
});
```

### 10.5 테스트 커버리지 목표

| 영역 | 목표 |
|------|------|
| **Range 파싱** | 100% |
| **세션 관리** | 90%+ |
| **API 엔드포인트** | 85%+ |
| **에러 핸들링** | 90%+ |
| **전체** | 85%+ |

### 10.6 테스트 실행

```bash
# Unit + Integration 테스트
pytest api/tests/blocks/stream/ -v --cov=api/app/blocks/stream

# E2E 테스트
npm run test:e2e -- stream.spec.ts

# 전체 테스트
pytest api/tests/ -v
npm run test:e2e
```

---

## 11. Performance Considerations

### 11.1 성능 목표

| Metric | Target | 측정 방법 |
|--------|--------|----------|
| **스트림 시작 지연** | < 2초 | API 응답 시간 |
| **Seek 지연** | < 500ms | Range 요청 응답 시간 |
| **동시 스트림** | 20개 | Rate Limiter |
| **대역폭** | 1Gbps (≈125MB/s) | NAS 제한 |
| **메모리 사용** | < 100MB/스트림 | 청크 스트리밍 |

### 11.2 최적화 전략

| 전략 | 방법 | 효과 |
|------|------|------|
| **청크 스트리밍** | 64KB 청크로 전송 | 메모리 효율 |
| **SSD 캐싱** | 자주 본 영상 SSD 복사 | NAS 부하 분산 |
| **Rate Limiting** | 동시 20개 제한 | 안정성 보장 |
| **Range 지원** | 206 Partial Content | Seek 최적화 |

### 11.3 병목 지점 및 해결

| 병목 | 원인 | 해결 |
|------|------|------|
| **NAS 대역폭** | 1Gbps 공유 | SSD 캐싱 (L2) |
| **동시 접속** | 무제한 시 과부하 | Rate Limiter (L3) |
| **Seek 지연** | 전체 파일 다운로드 | HTTP Range |
| **메모리 폭발** | 전체 파일 로드 | 청크 스트리밍 |

---

## 12. Monitoring & Metrics

### 12.1 수집 메트릭

| Metric | 타입 | 수집 방법 | 알림 임계값 |
|--------|------|----------|------------|
| `stream_active_count` | Gauge | Redis `stream:active` | > 18 (90%) |
| `stream_total` | Counter | 세션 시작 시 | - |
| `stream_errors` | Counter | 에러 발생 시 | > 10/분 |
| `stream_bandwidth_mbps` | Gauge | 바이트 전송량 집계 | > 800 Mbps |
| `stream_cache_hit_rate` | Gauge | SSD vs NAS 비율 | < 40% |
| `stream_avg_duration` | Histogram | 세션 종료 시 | - |

### 12.2 로그 포맷

```json
{
  "timestamp": "2025-12-11T10:30:00.123Z",
  "level": "INFO",
  "service": "stream",
  "action": "stream_started",
  "user_id": "user-123",
  "content_id": "content-456",
  "session_id": "session-789",
  "source": "ssd",
  "cache_hit": true,
  "file_size": 157832094
}
```

### 12.3 알림 조건

| 조건 | 임계값 | 우선순위 |
|------|--------|---------|
| 활성 스트림 한도 | 18/20 (90%) | P1 |
| 에러율 급증 | 10회/분 | P0 |
| 캐시 히트율 저하 | < 40% | P2 |
| 파일 없음 에러 | 1회 | P0 |

---

## 13. Security Considerations

### 13.1 보안 규칙

| 규칙 | 구현 |
|------|------|
| **인증 필수** | 모든 스트림 요청에 JWT 검증 |
| **사용자별 제한** | 동시 3개 스트림 (개인 무단 공유 방지) |
| **경로 검증** | 파일 경로 traversal 방지 |
| **Rate Limiting** | 서버 과부하 방지 |

### 13.2 보안 검증 체크리스트

- [ ] JWT 토큰 검증 (Auth Block 경유)
- [ ] 파일 경로 정규화 (`Path.resolve()`)
- [ ] Range 헤더 검증 (음수, 초과 방지)
- [ ] 사용자별 Rate Limit 적용
- [ ] 전역 Rate Limit 적용
- [ ] 에러 메시지에 민감 정보 노출 금지

---

## 14. Migration & Rollout

### 14.1 Phase 1: 기본 스트리밍 (Week 1)

- [ ] StreamService 구현
- [ ] Range 파싱 로직
- [ ] `/api/stream/{content_id}` 엔드포인트
- [ ] Unit 테스트 (Range 파싱)
- [ ] Integration 테스트 (Mock 블럭)

### 14.2 Phase 2: 진행률 추적 (Week 2)

- [ ] WatchProgress 모델
- [ ] ProgressService 구현
- [ ] `/api/progress/{content_id}` 엔드포인트
- [ ] DB 스키마 마이그레이션
- [ ] 테스트

### 14.3 Phase 3: Rate Limiting (Week 3)

- [ ] Cache Block과 연동
- [ ] `acquire_stream_slot()` 호출
- [ ] 429 에러 핸들링
- [ ] E2E 테스트 (동시 3개 제한)

### 14.4 Phase 4: 모니터링 (Week 4)

- [ ] 이벤트 발행 (`stream_started`, `stream_stopped`)
- [ ] 메트릭 수집
- [ ] 대시보드 연동 (Admin Block)
- [ ] 알림 설정

---

## 15. Success Metrics

| Metric | Target | 측정 |
|--------|--------|------|
| 스트림 시작 성공률 | > 99% | 에러율 < 1% |
| Seek 응답 시간 | < 500ms | Range 요청 P99 |
| 동시 스트림 | 20개 | Rate Limiter |
| 캐시 히트율 | > 60% | SSD vs NAS |
| 테스트 커버리지 | > 85% | pytest --cov |

---

## 16. Known Limitations

| 제약 | 설명 | 해결 계획 |
|------|------|----------|
| **단일 비트레이트** | 적응형 스트리밍 미지원 | v2.0 (HLS 추가) |
| **NAS 대역폭** | 1Gbps 공유 제한 | SSD 캐싱으로 완화 |
| **트랜스코딩 없음** | 원본 파일만 재생 | 클라이언트 코덱 필수 |
| **동시 20개** | 하드웨어 제약 | 서버 증설 시 확장 |

---

## 17. Future Enhancements

| 기능 | 우선순위 | 버전 |
|------|---------|------|
| **HLS 적응형 스트리밍** | P2 | v2.0 |
| **클립/북마크 기능** | P3 | v2.1 |
| **동시 시청 (Watch Party)** | P4 | v3.0 |
| **트랜스코딩 (저속 회선)** | P3 | v2.2 |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-11 | Claude Code | Initial draft |
