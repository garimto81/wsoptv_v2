# PRD: Admin Block

**Version**: 1.0.0
**Block ID**: admin
**전담 에이전트**: admin-agent
**Last Updated**: 2025-12-11

---

## 1. Block Overview

### 1.1 책임 (Responsibilities)

Admin Block은 시스템 전체를 모니터링하고 관리하는 관리자 전용 기능을 제공합니다.

| 기능 영역 | 설명 |
|----------|------|
| **사용자 관리** | 가입 승인/거부, 사용자 목록 조회, 권한 관리 |
| **시스템 모니터링** | 실시간 스트림 현황, 캐시 상태, 리소스 사용량 |
| **대시보드** | 핵심 지표 시각화 (활성 스트림, 캐시 사용률, 대기 사용자) |
| **보안 관리** | 관리자 권한 검증 (is_admin=True), 감사 로그 |

### 1.2 접근 제어

- **필수 권한**: `is_admin=True` (사용자 테이블 플래그)
- **인증 방식**: JWT 토큰 기반 (auth.validate_token)
- **권한 검증**: 모든 API 엔드포인트에서 `auth.check_permission` 호출

### 1.3 비기능 요구사항

| 항목 | 요구사항 |
|------|---------|
| **성능** | 대시보드 로딩 < 2초, API 응답 < 500ms |
| **보안** | 모든 요청 감사 로그 기록, 비인가 접근 즉시 차단 |
| **가용성** | 99.9% uptime (시스템 관리 필수) |
| **확장성** | 동시 관리자 세션 최대 10개 |

---

## 2. Agent Rules

### 2.1 컨텍스트 제한

Admin Agent는 다음 컨텍스트에만 접근합니다:

```
wsoptv_v2/
├── src/admin/              # Admin Block 전용
│   ├── routes/             # API 라우터
│   ├── services/           # 비즈니스 로직
│   ├── models/             # 데이터 모델
│   └── templates/          # 대시보드 템플릿
├── src/shared/             # 공유 유틸리티 (읽기 전용)
│   ├── auth.py             # 인증/권한 검증
│   └── database.py         # DB 접근
└── tests/admin/            # Admin 테스트
```

### 2.2 금지 사항

- **다른 Block 수정 금지**: auth, stream, cache 등 다른 Block의 코드 직접 수정 불가
- **하드코딩된 권한 체크 금지**: 반드시 `auth.check_permission` 사용
- **민감 정보 로그 금지**: 사용자 비밀번호, 토큰 등 로그 기록 금지

### 2.3 의존성 관리

```python
# 허용 (계약 기반)
from shared.auth import validate_token, check_permission
from shared.contracts.cache import get_cache_stats
from shared.contracts.stream import get_active_streams

# 금지 (직접 구현 접근)
from cache.services.redis_client import RedisClient  # ❌
from stream.ffmpeg_manager import FFmpegManager      # ❌
```

---

## 3. API Endpoints

### 3.1 시스템 상태

#### `GET /api/admin/status`

**설명**: 전체 시스템 상태 조회 (CPU, 메모리, 스토리지, 네트워크)

**권한**: `is_admin=True`

**Request**:
```http
GET /api/admin/status HTTP/1.1
Authorization: Bearer <admin_jwt_token>
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-12-11T10:30:00Z",
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 68.5,
    "disk_ssd": {
      "total_gb": 500,
      "used_gb": 320,
      "usage_percent": 64.0
    },
    "disk_nas": {
      "total_gb": 8000,
      "used_gb": 4500,
      "usage_percent": 56.25,
      "accessible": true
    }
  },
  "services": {
    "fastapi": "running",
    "redis": "running",
    "ffmpeg": "running",
    "database": "running"
  }
}
```

**Error Responses**:
- `401 Unauthorized`: 토큰 없음/만료
- `403 Forbidden`: 관리자 권한 없음

---

### 3.2 사용자 관리

#### `GET /api/admin/users`

**설명**: 전체 사용자 목록 조회 (페이지네이션)

**권한**: `is_admin=True`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|-------|
| `page` | int | No | 페이지 번호 | 1 |
| `limit` | int | No | 페이지당 항목 수 | 20 |
| `status` | string | No | 필터: `pending`, `approved`, `rejected` | 전체 |

**Request**:
```http
GET /api/admin/users?page=1&limit=20&status=pending HTTP/1.1
Authorization: Bearer <admin_jwt_token>
```

**Response** (200 OK):
```json
{
  "total": 150,
  "page": 1,
  "limit": 20,
  "users": [
    {
      "id": "uuid-1234",
      "email": "user@example.com",
      "name": "홍길동",
      "status": "pending",
      "created_at": "2025-12-10T14:20:00Z",
      "last_login": null,
      "is_admin": false
    }
  ]
}
```

---

#### `GET /api/admin/users/pending`

**설명**: 승인 대기 중인 사용자만 조회

**권한**: `is_admin=True`

**Response** (200 OK):
```json
{
  "count": 5,
  "pending_users": [
    {
      "id": "uuid-5678",
      "email": "newuser@example.com",
      "name": "김철수",
      "requested_at": "2025-12-11T09:00:00Z",
      "signup_reason": "업무용 스트리밍 필요"
    }
  ]
}
```

---

#### `POST /api/admin/users/{user_id}/approve`

**설명**: 사용자 가입 승인

**권한**: `is_admin=True`

**Request**:
```http
POST /api/admin/users/uuid-5678/approve HTTP/1.1
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "admin_note": "업무 용도 확인 완료"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "user_id": "uuid-5678",
  "new_status": "approved",
  "approved_by": "admin-uuid-1234",
  "approved_at": "2025-12-11T10:35:00Z"
}
```

**Side Effects**:
- 사용자 상태: `pending` → `approved`
- 이벤트 발행: `user_approved` (이메일 알림 트리거)
- 감사 로그 기록: `admin-uuid-1234 approved user-uuid-5678`

---

#### `POST /api/admin/users/{user_id}/reject`

**설명**: 사용자 가입 거부

**Request**:
```http
POST /api/admin/users/uuid-5678/reject HTTP/1.1
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "reason": "업무 용도 불명확"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "user_id": "uuid-5678",
  "new_status": "rejected",
  "rejected_by": "admin-uuid-1234",
  "rejected_at": "2025-12-11T10:40:00Z"
}
```

**Side Effects**:
- 사용자 상태: `pending` → `rejected`
- 이벤트 발행: `user_rejected`
- 감사 로그 기록

---

### 3.3 스트리밍 모니터링

#### `GET /api/admin/streams`

**설명**: 현재 활성화된 모든 스트림 조회

**권한**: `is_admin=True`

**Response** (200 OK):
```json
{
  "active_count": 3,
  "streams": [
    {
      "stream_id": "stream-abc123",
      "user_id": "uuid-user1",
      "user_email": "user1@example.com",
      "source_type": "youtube",
      "source_url": "https://youtube.com/...",
      "start_time": "2025-12-11T08:00:00Z",
      "duration_seconds": 9000,
      "bandwidth_mbps": 5.2,
      "viewer_count": 1,
      "cache_status": "ssd"
    }
  ],
  "total_bandwidth_mbps": 15.6
}
```

**데이터 출처**: `stream.get_active_streams()` 계약 호출

---

### 3.4 캐시 관리

#### `GET /api/admin/cache`

**설명**: SSD/NAS 캐시 상태 조회

**권한**: `is_admin=True`

**Response** (200 OK):
```json
{
  "ssd": {
    "total_gb": 500,
    "used_gb": 320,
    "available_gb": 180,
    "usage_percent": 64.0,
    "cached_files": 45,
    "hit_rate": 0.87
  },
  "nas": {
    "total_gb": 8000,
    "used_gb": 4500,
    "available_gb": 3500,
    "usage_percent": 56.25,
    "accessible": true,
    "last_check": "2025-12-11T10:30:00Z"
  },
  "cache_policies": {
    "ttl_hours": 24,
    "max_file_size_gb": 10,
    "eviction_strategy": "LRU"
  }
}
```

**데이터 출처**: `cache.get_cache_stats()` 계약 호출

---

## 4. Data Models

### 4.1 SystemStatus

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class DiskInfo(BaseModel):
    total_gb: float = Field(..., description="전체 용량 (GB)")
    used_gb: float = Field(..., description="사용 중 용량 (GB)")
    usage_percent: float = Field(..., ge=0, le=100, description="사용률 (%)")
    accessible: bool = Field(default=True, description="접근 가능 여부 (NAS 전용)")

class SystemMetrics(BaseModel):
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU 사용률 (%)")
    memory_usage: float = Field(..., ge=0, le=100, description="메모리 사용률 (%)")
    disk_ssd: DiskInfo
    disk_nas: DiskInfo

class ServiceStatus(BaseModel):
    fastapi: Literal["running", "stopped", "error"]
    redis: Literal["running", "stopped", "error"]
    ffmpeg: Literal["running", "stopped", "error"]
    database: Literal["running", "stopped", "error"]

class SystemStatus(BaseModel):
    status: Literal["healthy", "degraded", "critical"]
    timestamp: datetime
    system: SystemMetrics
    services: ServiceStatus
```

---

### 4.2 UserListItem

```python
from enum import Enum

class UserStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class UserListItem(BaseModel):
    id: str = Field(..., description="사용자 UUID")
    email: str
    name: str
    status: UserStatus
    created_at: datetime
    last_login: datetime | None
    is_admin: bool = False
    approved_by: str | None = Field(None, description="승인한 관리자 ID")
    rejected_reason: str | None = None
```

---

### 4.3 StreamInfo

```python
class StreamInfo(BaseModel):
    stream_id: str
    user_id: str
    user_email: str
    source_type: Literal["youtube", "afreecatv", "chzzk", "file"]
    source_url: str
    start_time: datetime
    duration_seconds: int = Field(..., description="스트리밍 지속 시간 (초)")
    bandwidth_mbps: float = Field(..., description="현재 대역폭 (Mbps)")
    viewer_count: int = Field(default=1, description="시청자 수")
    cache_status: Literal["ssd", "nas", "none"] = Field(..., description="캐시 위치")
```

---

### 4.4 CacheStatus

```python
class CacheMetrics(BaseModel):
    total_gb: float
    used_gb: float
    available_gb: float
    usage_percent: float
    cached_files: int = Field(..., description="캐시된 파일 수")
    hit_rate: float = Field(..., ge=0, le=1, description="캐시 히트율 (0~1)")
    accessible: bool = Field(default=True, description="접근 가능 여부")
    last_check: datetime | None = None

class CachePolicies(BaseModel):
    ttl_hours: int = Field(default=24, description="캐시 TTL (시간)")
    max_file_size_gb: int = Field(default=10, description="최대 파일 크기 (GB)")
    eviction_strategy: Literal["LRU", "LFU", "FIFO"] = "LRU"

class CacheStatus(BaseModel):
    ssd: CacheMetrics
    nas: CacheMetrics
    cache_policies: CachePolicies
```

---

## 5. Provided Contracts

Admin Block이 다른 Block에 제공하는 계약:

### 5.1 `get_system_status() -> SystemStatus`

```python
# src/admin/services/monitoring.py
async def get_system_status() -> SystemStatus:
    """
    전체 시스템 상태 조회

    Returns:
        SystemStatus: CPU, 메모리, 디스크, 서비스 상태

    Raises:
        ServiceUnavailableError: 시스템 메트릭 수집 실패
    """
    pass
```

**사용 예시** (다른 Block에서):
```python
from shared.contracts.admin import get_system_status

status = await get_system_status()
if status.system.disk_ssd.usage_percent > 90:
    logger.warning("SSD 용량 부족")
```

---

### 5.2 `approve_user(user_id: str, admin_id: str) -> None`

```python
async def approve_user(user_id: str, admin_id: str) -> None:
    """
    사용자 가입 승인

    Args:
        user_id: 승인할 사용자 UUID
        admin_id: 승인하는 관리자 UUID

    Side Effects:
        - 사용자 상태 업데이트 (pending → approved)
        - user_approved 이벤트 발행
        - 감사 로그 기록

    Raises:
        UserNotFoundError: 사용자 없음
        InvalidStatusError: 이미 승인/거부된 사용자
    """
    pass
```

---

### 5.3 `reject_user(user_id: str, admin_id: str, reason: str) -> None`

```python
async def reject_user(user_id: str, admin_id: str, reason: str) -> None:
    """
    사용자 가입 거부

    Args:
        user_id: 거부할 사용자 UUID
        admin_id: 거부하는 관리자 UUID
        reason: 거부 사유

    Side Effects:
        - 사용자 상태 업데이트 (pending → rejected)
        - user_rejected 이벤트 발행
        - 감사 로그 기록
    """
    pass
```

---

## 6. Required Contracts

Admin Block이 의존하는 다른 Block의 계약:

### 6.1 Auth Block

```python
# src/shared/contracts/auth.py

async def validate_token(token: str) -> TokenPayload:
    """
    JWT 토큰 검증

    Returns:
        TokenPayload: user_id, email, is_admin 포함

    Raises:
        InvalidTokenError: 토큰 만료/위조
    """
    pass

async def check_permission(user_id: str, required_permission: str) -> bool:
    """
    사용자 권한 확인

    Args:
        required_permission: "admin", "stream", "cache" 등

    Returns:
        bool: 권한 보유 여부
    """
    pass
```

**사용 예시**:
```python
@router.get("/api/admin/status")
async def get_status(token: str = Depends(oauth2_scheme)):
    payload = await validate_token(token)
    if not await check_permission(payload.user_id, "admin"):
        raise HTTPException(status_code=403, detail="관리자 권한 필요")

    return await get_system_status()
```

---

### 6.2 Cache Block

```python
# src/shared/contracts/cache.py

async def get_cache_stats() -> CacheStats:
    """
    SSD/NAS 캐시 통계 조회

    Returns:
        CacheStats: 용량, 히트율, 파일 수 등
    """
    pass
```

---

### 6.3 Stream Block

```python
# src/shared/contracts/stream.py

async def get_active_streams() -> list[ActiveStream]:
    """
    현재 활성 스트림 목록 조회

    Returns:
        list[ActiveStream]: 스트림 ID, 사용자, 대역폭 등
    """
    pass
```

---

## 7. Events Published

Admin Block이 발행하는 이벤트:

### 7.1 `user_approved`

**트리거**: `POST /api/admin/users/{id}/approve` 성공 시

**Payload**:
```json
{
  "event_type": "user_approved",
  "timestamp": "2025-12-11T10:35:00Z",
  "data": {
    "user_id": "uuid-5678",
    "email": "newuser@example.com",
    "approved_by": "admin-uuid-1234",
    "approved_at": "2025-12-11T10:35:00Z"
  }
}
```

**구독자**:
- **Notification Service**: 사용자에게 승인 이메일 발송
- **Analytics Service**: 가입 승인율 통계

---

### 7.2 `user_rejected`

**트리거**: `POST /api/admin/users/{id}/reject` 성공 시

**Payload**:
```json
{
  "event_type": "user_rejected",
  "timestamp": "2025-12-11T10:40:00Z",
  "data": {
    "user_id": "uuid-5678",
    "email": "newuser@example.com",
    "rejected_by": "admin-uuid-1234",
    "reason": "업무 용도 불명확"
  }
}
```

**구독자**:
- **Notification Service**: 사용자에게 거부 이메일 발송 (사유 포함)

---

## 8. Dashboard Metrics

### 8.1 실시간 지표

관리자 대시보드에 표시되는 핵심 메트릭:

| 메트릭 | 데이터 소스 | 업데이트 주기 |
|--------|-----------|--------------|
| **활성 스트림 수** | `stream.get_active_streams()` | 10초 |
| **SSD 캐시 사용률** | `cache.get_cache_stats().ssd.usage_percent` | 30초 |
| **NAS 상태** | `cache.get_cache_stats().nas.accessible` | 60초 |
| **승인 대기 사용자** | `GET /api/admin/users/pending` | 60초 |
| **총 대역폭** | `Σ(active_streams.bandwidth_mbps)` | 10초 |
| **서비스 상태** | `get_system_status().services` | 30초 |

### 8.2 대시보드 레이아웃

```
┌─────────────────────────────────────────────────────────┐
│  System Overview                        Admin Dashboard │
├─────────────────────────────────────────────────────────┤
│  [활성 스트림: 3개]  [SSD: 64%]  [대기 사용자: 5명]     │
├─────────────────────────────────────────────────────────┤
│  Active Streams                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ User      │ Source │ Duration │ Bandwidth │ Cache │   │
│  │ user1@... │ YT     │ 02:30:00 │ 5.2 Mbps  │ SSD   │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  Pending Approvals                                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │ newuser@example.com  │ [승인] [거부]              │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  Storage Status                                          │
│  SSD: [████████████░░░░] 64% (320/500 GB)              │
│  NAS: [██████████░░░░░░] 56% (4.5/8 TB) ✓ Online       │
└─────────────────────────────────────────────────────────┘
```

### 8.3 알림 임계값

자동 알림 트리거 조건:

| 조건 | 알림 레벨 | 액션 |
|------|----------|------|
| SSD 사용률 > 90% | Warning | 관리자 이메일 발송 |
| NAS 접근 불가 | Critical | 즉시 알림 + SMS |
| 활성 스트림 > 10개 | Info | 대역폭 모니터링 강화 |
| 승인 대기 > 20명 | Warning | 일일 리포트 |

---

## 9. Directory Structure

```
src/admin/
├── __init__.py
├── routes/
│   ├── __init__.py
│   ├── status.py              # GET /api/admin/status
│   ├── users.py               # 사용자 관리 엔드포인트
│   ├── streams.py             # GET /api/admin/streams
│   └── cache.py               # GET /api/admin/cache
├── services/
│   ├── __init__.py
│   ├── monitoring.py          # 시스템 모니터링 로직
│   ├── user_management.py     # 승인/거부 비즈니스 로직
│   └── audit_logger.py        # 감사 로그 기록
├── models/
│   ├── __init__.py
│   ├── system_status.py       # SystemStatus, DiskInfo 등
│   ├── user_models.py         # UserListItem, UserStatus
│   ├── stream_models.py       # StreamInfo
│   └── cache_models.py        # CacheStatus, CacheMetrics
├── templates/
│   ├── dashboard.html         # 관리자 대시보드 UI
│   └── users.html             # 사용자 관리 페이지
└── utils/
    ├── metrics_collector.py   # CPU/메모리/디스크 수집
    └── permission_check.py    # 권한 검증 데코레이터

tests/admin/
├── __init__.py
├── test_routes/
│   ├── test_status.py         # /api/admin/status 테스트
│   ├── test_users.py          # 사용자 관리 테스트
│   └── test_cache.py          # 캐시 조회 테스트
├── test_services/
│   ├── test_monitoring.py     # 모니터링 로직 단위 테스트
│   └── test_user_management.py
├── test_permissions.py        # 권한 검증 테스트
└── fixtures/
    ├── mock_auth.py           # Mock auth.validate_token
    ├── mock_cache.py          # Mock cache.get_cache_stats
    └── mock_streams.py        # Mock stream.get_active_streams

docs/blocks/
└── 05-admin.md                # 이 문서
```

---

## 10. Testing Strategy

### 10.1 단위 테스트 (Unit Tests)

**대상**: 개별 함수/메서드 (계약 호출 Mock)

**도구**: `pytest`, `pytest-asyncio`, `unittest.mock`

**예시**:
```python
# tests/admin/test_services/test_user_management.py
import pytest
from unittest.mock import AsyncMock, patch
from src.admin.services.user_management import approve_user
from src.shared.exceptions import UserNotFoundError

@pytest.mark.asyncio
@patch("src.admin.services.user_management.db_session")
@patch("src.admin.services.user_management.publish_event")
async def test_approve_user_success(mock_publish, mock_db):
    # Given
    user_id = "uuid-1234"
    admin_id = "admin-5678"
    mock_db.query.return_value.filter.return_value.first.return_value = {
        "id": user_id,
        "status": "pending"
    }

    # When
    await approve_user(user_id, admin_id)

    # Then
    mock_db.commit.assert_called_once()
    mock_publish.assert_called_once_with("user_approved", {
        "user_id": user_id,
        "approved_by": admin_id
    })

@pytest.mark.asyncio
async def test_approve_user_not_found():
    # Given
    user_id = "invalid-uuid"

    # When/Then
    with pytest.raises(UserNotFoundError):
        await approve_user(user_id, "admin-5678")
```

**커버리지 목표**: 90% 이상 (branch coverage)

---

### 10.2 통합 테스트 (Integration Tests)

**대상**: API 엔드포인트 + 실제 계약 호출

**도구**: `httpx.AsyncClient`, `pytest-asyncio`

**예시**:
```python
# tests/admin/test_routes/test_users.py
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_approve_user_endpoint(admin_token, test_user):
    # Given
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {admin_token}"}

        # When
        response = await client.post(
            f"/api/admin/users/{test_user.id}/approve",
            headers=headers,
            json={"admin_note": "테스트 승인"}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["new_status"] == "approved"
        assert data["user_id"] == test_user.id

@pytest.mark.asyncio
async def test_approve_user_forbidden_non_admin(user_token):
    # Given
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {user_token}"}  # 일반 사용자

        # When
        response = await client.post(
            "/api/admin/users/uuid-1234/approve",
            headers=headers
        )

        # Then
        assert response.status_code == 403
        assert "관리자 권한 필요" in response.json()["detail"]
```

---

### 10.3 권한 검증 테스트 (Permission Tests)

**목적**: 모든 Admin 엔드포인트가 `is_admin=True` 검증하는지 확인

```python
# tests/admin/test_permissions.py
import pytest
from httpx import AsyncClient

ADMIN_ENDPOINTS = [
    ("GET", "/api/admin/status"),
    ("GET", "/api/admin/users"),
    ("GET", "/api/admin/streams"),
    ("POST", "/api/admin/users/uuid-1234/approve"),
]

@pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
@pytest.mark.asyncio
async def test_all_endpoints_require_admin(method, path, user_token):
    """모든 Admin 엔드포인트는 일반 사용자 접근 차단"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {user_token}"}

        if method == "GET":
            response = await client.get(path, headers=headers)
        else:
            response = await client.post(path, headers=headers, json={})

        assert response.status_code == 403

@pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
@pytest.mark.asyncio
async def test_all_endpoints_allow_admin(method, path, admin_token):
    """모든 Admin 엔드포인트는 관리자 접근 허용"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {admin_token}"}

        if method == "GET":
            response = await client.get(path, headers=headers)
        else:
            response = await client.post(path, headers=headers, json={})

        assert response.status_code in [200, 201, 404]  # 403 아님
```

---

### 10.4 E2E 테스트 (End-to-End)

**시나리오**: 실제 사용자 승인 플로우

```python
# tests/admin/test_e2e_approval.py
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_user_approval_workflow():
    """
    시나리오:
    1. 신규 사용자 가입 (pending 상태)
    2. 관리자가 승인 대기 목록 조회
    3. 관리자가 승인
    4. 사용자가 스트림 생성 가능 확인
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. 신규 사용자 생성
        signup_response = await client.post("/api/auth/signup", json={
            "email": "newuser@test.com",
            "password": "password123",
            "name": "테스트 유저"
        })
        user_id = signup_response.json()["user_id"]

        # 2. 관리자가 대기 목록 조회
        admin_token = await get_admin_token()
        pending_response = await client.get(
            "/api/admin/users/pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert user_id in [u["id"] for u in pending_response.json()["pending_users"]]

        # 3. 승인
        approve_response = await client.post(
            f"/api/admin/users/{user_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"admin_note": "E2E 테스트"}
        )
        assert approve_response.status_code == 200

        # 4. 사용자가 스트림 생성 가능 확인
        user_token = await get_user_token("newuser@test.com", "password123")
        stream_response = await client.post(
            "/api/stream/create",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"url": "https://youtube.com/..."}
        )
        assert stream_response.status_code == 201  # 승인 후 스트림 생성 가능
```

---

### 10.5 성능 테스트 (Performance)

**목표**: 대시보드 로딩 < 2초, API 응답 < 500ms

```python
# tests/admin/test_performance.py
import pytest
import time

@pytest.mark.performance
@pytest.mark.asyncio
async def test_dashboard_load_time(admin_token):
    """대시보드 데이터 로딩 시간 측정"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {admin_token}"}

        start = time.time()

        # 병렬 요청 시뮬레이션
        status_task = client.get("/api/admin/status", headers=headers)
        users_task = client.get("/api/admin/users", headers=headers)
        streams_task = client.get("/api/admin/streams", headers=headers)
        cache_task = client.get("/api/admin/cache", headers=headers)

        await asyncio.gather(status_task, users_task, streams_task, cache_task)

        elapsed = time.time() - start

        assert elapsed < 2.0, f"대시보드 로딩 시간 초과: {elapsed:.2f}초"

@pytest.mark.performance
@pytest.mark.asyncio
async def test_approve_user_latency(admin_token):
    """사용자 승인 응답 시간 측정"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {admin_token}"}

        start = time.time()
        response = await client.post(
            "/api/admin/users/uuid-test/approve",
            headers=headers,
            json={"admin_note": "성능 테스트"}
        )
        elapsed = time.time() - start

        assert elapsed < 0.5, f"승인 응답 시간 초과: {elapsed:.2f}초"
```

---

### 10.6 보안 테스트 (Security)

**검증 항목**:
- 토큰 없이 접근 차단
- 만료된 토큰 거부
- 일반 사용자 권한 상승 차단
- SQL Injection 방어
- XSS 방어 (대시보드 템플릿)

```python
# tests/admin/test_security.py
@pytest.mark.security
@pytest.mark.asyncio
async def test_no_token_access():
    """토큰 없이 Admin 엔드포인트 접근 차단"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/admin/status")
        assert response.status_code == 401

@pytest.mark.security
@pytest.mark.asyncio
async def test_expired_token_rejected(expired_admin_token):
    """만료된 토큰 거부"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {expired_admin_token}"}
        response = await client.get("/api/admin/status", headers=headers)
        assert response.status_code == 401

@pytest.mark.security
@pytest.mark.asyncio
async def test_sql_injection_prevention(admin_token):
    """SQL Injection 시도 차단"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {admin_token}"}
        malicious_user_id = "1'; DROP TABLE users; --"

        response = await client.post(
            f"/api/admin/users/{malicious_user_id}/approve",
            headers=headers
        )

        # UserNotFoundError 또는 400 (SQL 실행 안 됨)
        assert response.status_code in [404, 400]
```

---

### 10.7 테스트 실행 전략

```bash
# 1. 빠른 피드백 (CI 파이프라인)
pytest tests/admin/test_routes/ -v --maxfail=1

# 2. 전체 테스트 (릴리스 전)
pytest tests/admin/ -v --cov=src/admin --cov-report=html

# 3. 성능 테스트만
pytest tests/admin/ -m performance -v

# 4. 보안 테스트만
pytest tests/admin/ -m security -v

# 5. E2E 테스트 (야간 빌드)
pytest tests/admin/ -m e2e -v --timeout=300
```

---

### 10.8 테스트 픽스처

```python
# tests/admin/conftest.py
import pytest
from datetime import datetime, timedelta
import jwt

@pytest.fixture
def admin_token():
    """관리자 JWT 토큰 생성"""
    payload = {
        "user_id": "admin-uuid-1234",
        "email": "admin@wsoptv.com",
        "is_admin": True,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, "secret_key", algorithm="HS256")

@pytest.fixture
def user_token():
    """일반 사용자 JWT 토큰 생성"""
    payload = {
        "user_id": "user-uuid-5678",
        "email": "user@example.com",
        "is_admin": False,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, "secret_key", algorithm="HS256")

@pytest.fixture
def test_user(db_session):
    """테스트용 pending 사용자 생성"""
    user = User(
        id="uuid-test-9999",
        email="test@example.com",
        name="테스트 유저",
        status="pending",
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    return user
```

---

## 11. 구현 우선순위

### Phase 1: 핵심 기능 (Week 1-2)
1. 사용자 승인/거부 API (`/api/admin/users/{id}/approve`, `/reject`)
2. 승인 대기 목록 조회 (`/api/admin/users/pending`)
3. 권한 검증 미들웨어 (`auth.check_permission` 통합)
4. 감사 로그 기록

### Phase 2: 모니터링 (Week 3)
5. 시스템 상태 API (`/api/admin/status`)
6. 활성 스트림 조회 (`/api/admin/streams`)
7. 캐시 상태 조회 (`/api/admin/cache`)

### Phase 3: 대시보드 (Week 4)
8. 관리자 대시보드 UI (HTML 템플릿)
9. 실시간 메트릭 업데이트 (WebSocket 또는 폴링)
10. 알림 시스템 (임계값 알림)

### Phase 4: 고급 기능 (Week 5+)
11. 사용자 검색/필터링
12. 감사 로그 조회 API
13. 시스템 설정 변경 (캐시 정책 등)

---

## 12. 보안 고려사항

### 12.1 인증/인가
- **모든 엔드포인트**: `is_admin=True` 검증 필수
- **토큰 저장**: HTTP-only 쿠키 사용 (XSS 방어)
- **CSRF 방어**: 상태 변경 요청에 CSRF 토큰 필수

### 12.2 감사 로그
- **기록 항목**: 사용자 ID, 액션, 타임스탬프, IP 주소
- **보관 기간**: 최소 1년
- **접근 제어**: 관리자만 조회 가능

### 12.3 민감 정보 보호
- **로그**: 비밀번호, 토큰 등 민감 정보 마스킹
- **응답**: 사용자 비밀번호 해시 노출 금지

---

## 13. 모니터링 & 알림

### 13.1 Prometheus Metrics

```python
# src/admin/utils/metrics.py
from prometheus_client import Counter, Gauge, Histogram

# 사용자 승인/거부 카운터
user_approval_count = Counter("admin_user_approvals_total", "Total user approvals")
user_rejection_count = Counter("admin_user_rejections_total", "Total user rejections")

# 시스템 리소스 게이지
ssd_usage_percent = Gauge("admin_ssd_usage_percent", "SSD usage percentage")
nas_accessible = Gauge("admin_nas_accessible", "NAS accessibility (0 or 1)")

# API 응답 시간 히스토그램
api_latency = Histogram("admin_api_latency_seconds", "API latency", ["endpoint"])
```

### 13.2 Grafana 대시보드

**패널 구성**:
1. 활성 스트림 수 (시계열)
2. SSD/NAS 사용률 (게이지)
3. 사용자 승인율 (파이 차트)
4. API 응답 시간 (히트맵)

---

## 14. 에러 처리

### 14.1 커스텀 예외

```python
# src/admin/exceptions.py
class AdminError(Exception):
    """Admin Block 기본 예외"""
    pass

class UserNotFoundError(AdminError):
    """사용자 없음"""
    pass

class InvalidStatusError(AdminError):
    """잘못된 사용자 상태 (이미 승인/거부됨)"""
    pass

class PermissionDeniedError(AdminError):
    """관리자 권한 없음"""
    pass

class SystemUnavailableError(AdminError):
    """시스템 메트릭 수집 실패"""
    pass
```

### 14.2 에러 응답 형식

```json
{
  "error": "UserNotFoundError",
  "message": "사용자를 찾을 수 없습니다",
  "detail": {
    "user_id": "uuid-invalid"
  },
  "timestamp": "2025-12-11T10:50:00Z"
}
```

---

## 15. 성능 최적화

### 15.1 캐싱 전략
- **시스템 상태**: Redis 캐시 (TTL: 30초)
- **활성 스트림**: Redis 캐시 (TTL: 10초)
- **사용자 목록**: DB 인덱스 최적화 (email, status)

### 15.2 쿼리 최적화
```sql
-- 승인 대기 사용자 조회 최적화
CREATE INDEX idx_users_status ON users(status) WHERE status = 'pending';

-- 감사 로그 조회 최적화
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
```

---

## 16. 배포 체크리스트

- [ ] 환경 변수 설정 (`ADMIN_EMAIL`, `LOG_LEVEL`)
- [ ] 데이터베이스 마이그레이션 (`alembic upgrade head`)
- [ ] Redis 연결 확인
- [ ] 관리자 계정 초기 생성 (`is_admin=True`)
- [ ] 대시보드 접근 테스트 (https://wsoptv.com/admin)
- [ ] 프로덕션 로그 레벨 설정 (`INFO`)
- [ ] Prometheus/Grafana 메트릭 수집 확인

---

## 17. 참조 문서

- **Auth Block PRD**: `docs/blocks/01-auth.md`
- **Stream Block PRD**: `docs/blocks/02-stream.md`
- **Cache Block PRD**: `docs/blocks/03-cache.md`
- **전역 아키텍처**: `docs/ARCHITECTURE.md`
- **계약 가이드라인**: `docs/CONTRACT_GUIDELINES.md`

---

**문서 버전**: 1.0.0
**최종 업데이트**: 2025-12-11
**작성자**: Claude Code (admin-agent)
**승인자**: TBD
