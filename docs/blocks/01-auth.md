# PRD: Auth Block

**Version**: 1.0.0
**Block ID**: auth
**전담 에이전트**: auth-agent
**최종 수정일**: 2025-12-11

---

## 1. Block Overview

### 1.1 책임 (Responsibilities)

Auth Block은 wsoptv_v2 시스템의 **인증(Authentication)**, **인가(Authorization)**, **사용자 관리(User Management)** 전담 블럭입니다.

| 책임 영역 | 세부 기능 |
|----------|----------|
| **인증** | 회원가입, 로그인, 로그아웃, 토큰 발급/갱신 |
| **인가** | 권한 검증, 역할 기반 접근 제어 (RBAC) |
| **사용자 관리** | 사용자 정보 CRUD, 상태 관리, 프로필 관리 |
| **세션 관리** | JWT 기반 세션, 토큰 블랙리스트 관리 |

### 1.2 독립성 원칙 (Independence Principle)

```
[독립성 레벨: L0 - Zero Dependency]

Auth Block은 최하위 의존성 블럭으로, 다른 블럭에 의존하지 않음.
모든 블럭이 Auth Block의 인증/인가 서비스를 사용.
```

**핵심 원칙**:
- 다른 블럭의 DB 테이블에 직접 접근 금지
- 다른 블럭의 비즈니스 로직 호출 금지
- 외부 의존성 최소화 (bcrypt, PyJWT만 허용)

### 1.3 블럭 경계 (Block Boundaries)

| 경계 유형 | 설명 |
|----------|------|
| **IN** | 모든 블럭의 인증/인가 요청 수락 |
| **OUT** | 다른 블럭으로 데이터 전송 안 함 (이벤트만 발행) |
| **데이터 소유권** | users, sessions 테이블 전체 소유 |

---

## 2. Agent Rules

### 2.1 컨텍스트 제한 (Context Restrictions)

auth-agent는 **Auth Block 내부 파일만 수정 가능**합니다.

```
[Strict Rule: Context Boundary]

auth-agent는 api/app/blocks/auth/ 디렉토리 외부의 파일을 수정할 수 없음.
다른 블럭 수정이 필요하면 오케스트레이터에게 요청해야 함.
```

### 2.2 수정 가능 파일 목록 (Editable Files)

```
api/app/blocks/auth/
├── models/
│   ├── user.py              ✅ 수정 가능
│   ├── session.py           ✅ 수정 가능
│   └── enums.py             ✅ 수정 가능
├── schemas/
│   ├── user_schema.py       ✅ 수정 가능
│   ├── auth_schema.py       ✅ 수정 가능
│   └── token_schema.py      ✅ 수정 가능
├── routes/
│   ├── auth.py              ✅ 수정 가능
│   └── users.py             ✅ 수정 가능
├── services/
│   ├── auth_service.py      ✅ 수정 가능
│   ├── user_service.py      ✅ 수정 가능
│   ├── token_service.py     ✅ 수정 가능
│   └── password_service.py  ✅ 수정 가능
├── contracts/
│   └── auth_contract.py     ✅ 수정 가능 (계약 정의)
├── events/
│   └── auth_events.py       ✅ 수정 가능
├── dependencies/
│   └── auth_deps.py         ✅ 수정 가능
└── tests/
    ├── test_auth.py         ✅ 수정 가능
    ├── test_user.py         ✅ 수정 가능
    └── test_contracts.py    ✅ 수정 가능
```

### 2.3 수정 불가 파일 목록 (Read-Only Files)

```
api/app/blocks/
├── video/                   ❌ 수정 금지 (읽기 전용)
├── channel/                 ❌ 수정 금지
├── analytics/               ❌ 수정 금지
└── orchestrator/
    ├── contracts/           ⚠️  읽기 전용 (계약 확인용)
    └── events/              ⚠️  읽기 전용 (이벤트 스키마 확인용)

api/app/core/
├── database.py              ❌ 수정 금지 (DB 엔진 설정)
├── config.py                ❌ 수정 금지 (전역 설정)
└── security.py              ⚠️  읽기만 가능 (보안 유틸리티)

api/alembic/                 ❌ 마이그레이션은 오케스트레이터가 관리
```

### 2.4 오케스트레이터 경유 규칙 (Orchestrator Mediation)

다른 블럭 참조가 필요한 경우:

```python
# ❌ 잘못된 예시 (직접 호출)
from api.app.blocks.video.services.video_service import VideoService
video = VideoService.get_video(video_id)  # 금지!

# ✅ 올바른 예시 (오케스트레이터 경유)
from api.app.blocks.orchestrator.contracts.video_contract import VideoContract
video = VideoContract.get_video_info(video_id)  # 허용
```

**규칙**:
1. 다른 블럭의 서비스를 직접 import 금지
2. Orchestrator가 제공하는 Contract만 사용
3. 계약이 없으면 오케스트레이터에게 계약 추가 요청

---

## 3. API Endpoints

### 3.1 인증 엔드포인트 (Authentication Endpoints)

#### POST /api/auth/register
**설명**: 신규 사용자 회원가입

```python
# Request
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "username": "john_doe",
  "full_name": "John Doe"
}

# Response (201 Created)
{
  "user": {
    "id": "uuid-1234",
    "email": "user@example.com",
    "username": "john_doe",
    "status": "pending_approval",
    "created_at": "2025-12-11T10:00:00Z"
  },
  "message": "회원가입 완료. 관리자 승인 대기 중입니다."
}

# Error Responses
400 Bad Request - 이메일 중복, 비밀번호 규칙 위반
422 Validation Error - 필수 필드 누락
```

**비즈니스 로직**:
- 이메일 중복 검사
- 비밀번호 강도 검증 (8자 이상, 대소문자+숫자+특수문자)
- bcrypt 해싱 (cost=12)
- 초기 상태: `pending_approval`
- 이벤트 발행: `user_registered`

---

#### POST /api/auth/login
**설명**: 사용자 로그인 및 토큰 발급

```python
# Request
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

# Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid-1234",
    "email": "user@example.com",
    "username": "john_doe",
    "role": "user"
  }
}

# Error Responses
401 Unauthorized - 이메일/비밀번호 불일치
403 Forbidden - 계정 승인 대기 중 (pending_approval)
403 Forbidden - 계정 정지됨 (suspended)
```

**비즈니스 로직**:
- 이메일로 사용자 조회
- bcrypt 비밀번호 검증
- 사용자 상태 확인 (`active`만 로그인 허용)
- JWT 토큰 발급 (Access: 1h, Refresh: 7d)
- 세션 기록 저장 (IP, User-Agent)
- 이벤트 발행: `user_login`

---

#### POST /api/auth/logout
**설명**: 로그아웃 및 토큰 무효화

```python
# Request (Headers)
Authorization: Bearer <access_token>

# Response (200 OK)
{
  "message": "로그아웃 완료"
}
```

**비즈니스 로직**:
- 토큰 블랙리스트 추가 (Redis/DB)
- 세션 종료 시간 기록
- 이벤트 발행: `user_logout`

---

#### GET /api/auth/me
**설명**: 현재 로그인 사용자 정보 조회

```python
# Request (Headers)
Authorization: Bearer <access_token>

# Response (200 OK)
{
  "id": "uuid-1234",
  "email": "user@example.com",
  "username": "john_doe",
  "full_name": "John Doe",
  "role": "user",
  "status": "active",
  "created_at": "2025-12-11T10:00:00Z",
  "last_login": "2025-12-11T12:00:00Z"
}
```

**비즈니스 로직**:
- JWT 토큰 검증
- 블랙리스트 확인
- 사용자 정보 반환

---

#### POST /api/auth/refresh
**설명**: Refresh Token으로 새 Access Token 발급

```python
# Request
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

# Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}

# Error Responses
401 Unauthorized - Refresh Token 만료/유효하지 않음
```

**비즈니스 로직**:
- Refresh Token 검증
- 새 Access Token 발급 (1h)
- Refresh Token은 재사용 (7일 유효)

---

### 3.2 사용자 관리 엔드포인트 (User Management Endpoints)

#### GET /api/users/{user_id}
**설명**: 사용자 정보 조회 (관리자 전용)

```python
# Response (200 OK)
{
  "id": "uuid-1234",
  "email": "user@example.com",
  "username": "john_doe",
  "status": "active",
  "role": "user",
  "created_at": "2025-12-11T10:00:00Z"
}
```

---

#### PATCH /api/users/{user_id}/status
**설명**: 사용자 상태 변경 (관리자 전용)

```python
# Request
{
  "status": "active"  # pending_approval, active, suspended
}

# Response (200 OK)
{
  "id": "uuid-1234",
  "status": "active",
  "updated_at": "2025-12-11T12:00:00Z"
}
```

**비즈니스 로직**:
- `pending_approval` → `active`: 이벤트 `user_approved` 발행
- `active` → `suspended`: 모든 세션 무효화

---

## 4. Data Models

### 4.1 User Model

```python
# api/app/blocks/auth/models/user.py

from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 인증 정보
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)

    # 사용자 정보
    full_name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING_APPROVAL, nullable=False)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # 인덱스
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
        Index("idx_user_status", "status"),
    )
```

---

### 4.2 UserStatus Enum

```python
# api/app/blocks/auth/models/enums.py

from enum import Enum

class UserStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"  # 승인 대기
    ACTIVE = "active"                      # 활성
    SUSPENDED = "suspended"                # 정지
    DELETED = "deleted"                    # 삭제 (soft delete)

class UserRole(str, Enum):
    ADMIN = "admin"                        # 관리자
    USER = "user"                          # 일반 사용자
```

---

### 4.3 Session Model

```python
# api/app/blocks/auth/models/session.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "auth"}

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)

    # 세션 정보
    access_token = Column(String(500), nullable=False, unique=True)
    refresh_token = Column(String(500), nullable=False, unique=True)

    # 메타데이터
    ip_address = Column(String(45), nullable=True)  # IPv6 지원
    user_agent = Column(Text, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    logged_out_at = Column(DateTime, nullable=True)

    # 인덱스
    __table_args__ = (
        Index("idx_session_user", "user_id"),
        Index("idx_session_access_token", "access_token"),
        Index("idx_session_refresh_token", "refresh_token"),
    )
```

---

## 5. Provided Contracts (다른 블럭에 제공)

Auth Block이 다른 블럭에 제공하는 계약 인터페이스:

### 5.1 validate_token(token: str) -> User

```python
# api/app/blocks/auth/contracts/auth_contract.py

class AuthContract:
    @staticmethod
    def validate_token(token: str) -> User:
        """
        JWT 토큰을 검증하고 사용자 객체 반환

        Args:
            token: Bearer 토큰 (헤더 제외)

        Returns:
            User: 검증된 사용자 객체

        Raises:
            UnauthorizedError: 토큰 만료/유효하지 않음
            ForbiddenError: 블랙리스트 토큰
        """
        pass
```

**사용 예시**:
```python
# Video Block에서 사용
from api.app.blocks.auth.contracts.auth_contract import AuthContract

def upload_video(token: str, video_data: dict):
    user = AuthContract.validate_token(token)  # 인증 검증
    # 이후 비즈니스 로직...
```

---

### 5.2 get_user(user_id: str) -> User

```python
@staticmethod
def get_user(user_id: str) -> User:
    """
    사용자 ID로 사용자 정보 조회

    Args:
        user_id: UUID 문자열

    Returns:
        User: 사용자 객체

    Raises:
        NotFoundError: 사용자 없음
    """
    pass
```

**사용 예시**:
```python
# Channel Block에서 사용
user = AuthContract.get_user(channel.owner_id)
```

---

### 5.3 check_permission(user_id: str, resource: str, action: str) -> bool

```python
@staticmethod
def check_permission(user_id: str, resource: str, action: str) -> bool:
    """
    사용자 권한 검증 (RBAC)

    Args:
        user_id: 사용자 ID
        resource: 리소스 타입 (예: "video", "channel")
        action: 액션 (예: "create", "read", "update", "delete")

    Returns:
        bool: 권한 있음(True), 없음(False)
    """
    pass
```

**사용 예시**:
```python
# Analytics Block에서 사용
if not AuthContract.check_permission(user_id, "analytics", "read"):
    raise ForbiddenError("분석 데이터 조회 권한 없음")
```

---

### 5.4 get_active_sessions(user_id: str) -> List[Session]

```python
@staticmethod
def get_active_sessions(user_id: str) -> List[Session]:
    """
    사용자의 활성 세션 목록 조회

    Args:
        user_id: 사용자 ID

    Returns:
        List[Session]: 활성 세션 목록
    """
    pass
```

---

## 6. Required Contracts (다른 블럭에서 필요)

Auth Block은 **Zero Dependency** 블럭이므로 다른 블럭의 계약이 필요하지 않습니다.

```
[의존성: None]

Auth Block은 시스템의 최하위 레이어로, 다른 블럭에 의존하지 않음.
```

**외부 의존성**:
- bcrypt (비밀번호 해싱)
- PyJWT (JWT 토큰)
- FastAPI (웹 프레임워크)
- SQLAlchemy (ORM)

---

## 7. Events Published

Auth Block이 발행하는 이벤트:

### 7.1 user_registered

```python
# api/app/blocks/auth/events/auth_events.py

class UserRegisteredEvent:
    event_type = "user_registered"

    payload = {
        "user_id": "uuid-1234",
        "email": "user@example.com",
        "username": "john_doe",
        "status": "pending_approval",
        "created_at": "2025-12-11T10:00:00Z"
    }
```

**구독자**:
- Email Block (환영 이메일 발송)
- Notification Block (관리자에게 승인 요청 알림)

---

### 7.2 user_approved

```python
class UserApprovedEvent:
    event_type = "user_approved"

    payload = {
        "user_id": "uuid-1234",
        "email": "user@example.com",
        "approved_at": "2025-12-11T12:00:00Z",
        "approved_by": "admin-uuid"
    }
```

**구독자**:
- Email Block (승인 완료 이메일)
- Channel Block (기본 채널 생성)

---

### 7.3 user_login

```python
class UserLoginEvent:
    event_type = "user_login"

    payload = {
        "user_id": "uuid-1234",
        "session_id": "session-uuid",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "login_at": "2025-12-11T14:00:00Z"
    }
```

**구독자**:
- Analytics Block (로그인 통계)
- Security Block (이상 로그인 탐지)

---

### 7.4 user_logout

```python
class UserLogoutEvent:
    event_type = "user_logout"

    payload = {
        "user_id": "uuid-1234",
        "session_id": "session-uuid",
        "logout_at": "2025-12-11T15:00:00Z"
    }
```

**구독자**:
- Analytics Block (세션 시간 분석)

---

### 7.5 user_password_changed

```python
class UserPasswordChangedEvent:
    event_type = "user_password_changed"

    payload = {
        "user_id": "uuid-1234",
        "changed_at": "2025-12-11T16:00:00Z",
        "ip_address": "192.168.1.1"
    }
```

**구독자**:
- Email Block (비밀번호 변경 알림)
- Security Block (보안 로그)

---

## 8. Directory Structure

```
api/app/blocks/auth/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── user.py                 # User 모델
│   ├── session.py              # Session 모델
│   └── enums.py                # UserStatus, UserRole
├── schemas/
│   ├── __init__.py
│   ├── user_schema.py          # UserCreate, UserResponse, UserUpdate
│   ├── auth_schema.py          # LoginRequest, LoginResponse
│   └── token_schema.py         # TokenPayload, TokenResponse
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # /api/auth/* 라우터
│   └── users.py                # /api/users/* 라우터 (관리자용)
├── services/
│   ├── __init__.py
│   ├── auth_service.py         # 인증 비즈니스 로직
│   ├── user_service.py         # 사용자 CRUD
│   ├── token_service.py        # JWT 발급/검증
│   └── password_service.py     # bcrypt 해싱/검증
├── contracts/
│   ├── __init__.py
│   └── auth_contract.py        # 다른 블럭에 제공하는 계약
├── events/
│   ├── __init__.py
│   ├── auth_events.py          # 이벤트 정의
│   └── publisher.py            # 이벤트 발행 유틸리티
├── dependencies/
│   ├── __init__.py
│   └── auth_deps.py            # get_current_user, require_admin
├── exceptions/
│   ├── __init__.py
│   └── auth_exceptions.py      # UnauthorizedError, ForbiddenError
├── tests/
│   ├── __init__.py
│   ├── test_auth.py            # 인증 엔드포인트 테스트
│   ├── test_user.py            # 사용자 관리 테스트
│   ├── test_token.py           # 토큰 서비스 테스트
│   ├── test_contracts.py       # 계약 테스트
│   └── conftest.py             # 테스트 픽스처
└── README.md                   # Auth Block 문서
```

---

## 9. Testing Strategy

### 9.1 독립 테스트 (Unit Tests)

Auth Block은 **Mock 없이 자체 테스트** 가능:

```python
# api/app/blocks/auth/tests/test_auth.py

import pytest
from fastapi.testclient import TestClient
from api.app.blocks.auth.services.auth_service import AuthService

class TestAuthService:
    def test_register_user(self, db_session):
        """회원가입 테스트 (Mock 없이)"""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "username": "testuser"
        }

        user = AuthService.register(db_session, user_data)

        assert user.email == "test@example.com"
        assert user.status == UserStatus.PENDING_APPROVAL
        assert user.password_hash != "SecurePass123!"  # 해싱 확인

    def test_login_success(self, db_session, test_user):
        """로그인 성공 테스트"""
        credentials = {
            "email": test_user.email,
            "password": "original_password"
        }

        result = AuthService.login(db_session, credentials)

        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user"]["id"] == str(test_user.id)

    def test_login_invalid_password(self, db_session, test_user):
        """로그인 실패 테스트 (잘못된 비밀번호)"""
        credentials = {
            "email": test_user.email,
            "password": "wrong_password"
        }

        with pytest.raises(UnauthorizedError):
            AuthService.login(db_session, credentials)
```

---

### 9.2 계약 테스트 (Contract Tests)

다른 블럭이 의존하는 계약 검증:

```python
# api/app/blocks/auth/tests/test_contracts.py

class TestAuthContract:
    def test_validate_token_contract(self, db_session, valid_token, test_user):
        """validate_token 계약 테스트"""
        # Given: 유효한 토큰
        # When: 계약 호출
        user = AuthContract.validate_token(valid_token)

        # Then: User 객체 반환
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert isinstance(user, User)

    def test_validate_token_expired(self, expired_token):
        """만료된 토큰 검증"""
        with pytest.raises(UnauthorizedError) as exc:
            AuthContract.validate_token(expired_token)

        assert "토큰이 만료되었습니다" in str(exc.value)

    def test_get_user_contract(self, db_session, test_user):
        """get_user 계약 테스트"""
        user = AuthContract.get_user(str(test_user.id))

        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_check_permission_admin(self, db_session, admin_user):
        """관리자 권한 검증"""
        result = AuthContract.check_permission(
            str(admin_user.id),
            "users",
            "delete"
        )

        assert result is True

    def test_check_permission_user(self, db_session, test_user):
        """일반 사용자 권한 검증"""
        result = AuthContract.check_permission(
            str(test_user.id),
            "users",
            "delete"
        )

        assert result is False
```

---

### 9.3 통합 테스트 (Integration Tests)

API 엔드포인트 전체 플로우 테스트:

```python
# api/app/blocks/auth/tests/test_integration.py

class TestAuthIntegration:
    def test_full_auth_flow(self, client: TestClient):
        """회원가입 → 로그인 → 인증 확인 플로우"""
        # 1. 회원가입
        register_response = client.post("/api/auth/register", json={
            "email": "integration@test.com",
            "password": "SecurePass123!",
            "username": "integration_user"
        })
        assert register_response.status_code == 201
        user_id = register_response.json()["user"]["id"]

        # 2. 관리자가 승인
        admin_token = get_admin_token(client)
        approve_response = client.patch(
            f"/api/users/{user_id}/status",
            json={"status": "active"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert approve_response.status_code == 200

        # 3. 로그인
        login_response = client.post("/api/auth/login", json={
            "email": "integration@test.com",
            "password": "SecurePass123!"
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # 4. 인증 확인
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "integration@test.com"
```

---

### 9.4 이벤트 테스트 (Event Tests)

```python
# api/app/blocks/auth/tests/test_events.py

class TestAuthEvents:
    def test_user_registered_event_published(self, db_session, event_bus):
        """회원가입 시 이벤트 발행 확인"""
        user_data = {
            "email": "event@test.com",
            "password": "SecurePass123!",
            "username": "event_user"
        }

        user = AuthService.register(db_session, user_data)

        # 이벤트 발행 확인
        published_events = event_bus.get_published_events()
        assert len(published_events) == 1
        assert published_events[0]["event_type"] == "user_registered"
        assert published_events[0]["payload"]["user_id"] == str(user.id)
```

---

### 9.5 테스트 커버리지 목표

| 테스트 유형 | 커버리지 목표 |
|------------|--------------|
| 라인 커버리지 | 90% 이상 |
| 브랜치 커버리지 | 85% 이상 |
| 계약 테스트 | 100% (모든 계약) |
| 통합 테스트 | 핵심 플로우 100% |

```bash
# 테스트 실행
pytest api/app/blocks/auth/tests/ -v --cov=api.app.blocks.auth --cov-report=html

# 계약 테스트만 실행
pytest api/app/blocks/auth/tests/test_contracts.py -v

# 특정 테스트 파일만 실행
pytest api/app/blocks/auth/tests/test_auth.py -v
```

---

## 10. Dependencies & Configuration

### 10.1 외부 라이브러리

```python
# requirements.txt (Auth Block 전용)
bcrypt==4.1.1           # 비밀번호 해싱
PyJWT==2.8.0            # JWT 토큰
python-jose[cryptography]==3.3.0  # JWT 암호화
passlib[bcrypt]==1.7.4  # 비밀번호 유틸리티
```

### 10.2 환경 변수

```bash
# .env
SECRET_KEY=your-secret-key-here                # JWT 서명 키
ALGORITHM=HS256                                 # JWT 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES=60                  # Access Token 만료 (1시간)
REFRESH_TOKEN_EXPIRE_DAYS=7                     # Refresh Token 만료 (7일)
PASSWORD_BCRYPT_ROUNDS=12                       # bcrypt cost
```

---

## 11. Security Considerations

### 11.1 보안 체크리스트

| 항목 | 구현 |
|------|------|
| 비밀번호 해싱 | bcrypt (cost=12) |
| SQL Injection 방지 | SQLAlchemy ORM 사용 |
| JWT 서명 | HS256 알고리즘 |
| 토큰 블랙리스트 | 로그아웃 시 세션 무효화 |
| Rate Limiting | 로그인 API (5회/분) |
| HTTPS 강제 | 프로덕션 환경 필수 |

### 11.2 비밀번호 규칙

```python
# api/app/blocks/auth/services/password_service.py

def validate_password_strength(password: str) -> bool:
    """
    비밀번호 강도 검증
    - 최소 8자
    - 대문자 1개 이상
    - 소문자 1개 이상
    - 숫자 1개 이상
    - 특수문자 1개 이상
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True
```

---

## 12. Migration Strategy

### 12.1 Alembic 마이그레이션

```python
# alembic/versions/001_create_auth_tables.py

def upgrade():
    # auth 스키마 생성
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")

    # users 테이블 생성
    op.create_table(
        "users",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("full_name", sa.String(100)),
        sa.Column("role", sa.Enum("admin", "user", name="user_role"), default="user"),
        sa.Column("status", sa.Enum("pending_approval", "active", "suspended", "deleted", name="user_status"), default="pending_approval"),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), onupdate=datetime.utcnow),
        sa.Column("last_login", sa.DateTime()),
        schema="auth"
    )

    # sessions 테이블 생성
    op.create_table(
        "sessions",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("user_id", UUID(), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("access_token", sa.String(500), unique=True, nullable=False),
        sa.Column("refresh_token", sa.String(500), unique=True, nullable=False),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("logged_out_at", sa.DateTime()),
        schema="auth"
    )

    # 인덱스 생성
    op.create_index("idx_user_email", "users", ["email"], schema="auth")
    op.create_index("idx_user_username", "users", ["username"], schema="auth")
    op.create_index("idx_session_user", "sessions", ["user_id"], schema="auth")
```

---

## 13. Monitoring & Logging

### 13.1 로깅 전략

```python
# api/app/blocks/auth/services/auth_service.py

import logging

logger = logging.getLogger("auth")

class AuthService:
    @staticmethod
    def login(db: Session, credentials: dict):
        logger.info(f"로그인 시도: {credentials['email']}")

        try:
            user = UserService.get_by_email(db, credentials["email"])
            if not PasswordService.verify(credentials["password"], user.password_hash):
                logger.warning(f"로그인 실패 (잘못된 비밀번호): {credentials['email']}")
                raise UnauthorizedError("이메일 또는 비밀번호가 올바르지 않습니다.")

            logger.info(f"로그인 성공: {user.email} (ID: {user.id})")
            return TokenService.create_tokens(user)

        except Exception as e:
            logger.error(f"로그인 오류: {str(e)}", exc_info=True)
            raise
```

---

## 14. Performance Considerations

### 14.1 최적화 전략

| 영역 | 전략 |
|------|------|
| 토큰 검증 | Redis 캐싱 (블랙리스트 조회) |
| 사용자 조회 | 이메일/username 인덱스 |
| 세션 관리 | 만료된 세션 자동 삭제 (cron) |
| 비밀번호 해싱 | bcrypt cost=12 (보안 우선) |

---

## 15. Future Enhancements

### 15.1 로드맵

| 버전 | 기능 |
|------|------|
| v1.1.0 | OAuth2 소셜 로그인 (Google, GitHub) |
| v1.2.0 | 2FA (TOTP) 지원 |
| v1.3.0 | 비밀번호 재설정 이메일 |
| v1.4.0 | IP 화이트리스트/블랙리스트 |

---

## Appendix A: API Reference

전체 엔드포인트 요약:

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | /api/auth/register | 회원가입 | 불필요 |
| POST | /api/auth/login | 로그인 | 불필요 |
| POST | /api/auth/logout | 로그아웃 | 필수 |
| GET | /api/auth/me | 내 정보 조회 | 필수 |
| POST | /api/auth/refresh | 토큰 갱신 | Refresh Token |
| GET | /api/users/{id} | 사용자 조회 | Admin |
| PATCH | /api/users/{id}/status | 상태 변경 | Admin |

---

## Appendix B: Error Codes

| 코드 | HTTP Status | 설명 |
|------|-------------|------|
| AUTH_001 | 400 | 이메일 중복 |
| AUTH_002 | 400 | 비밀번호 규칙 위반 |
| AUTH_003 | 401 | 이메일/비밀번호 불일치 |
| AUTH_004 | 401 | 토큰 만료 |
| AUTH_005 | 403 | 승인 대기 중 |
| AUTH_006 | 403 | 계정 정지 |
| AUTH_007 | 404 | 사용자 없음 |

---

**PRD 작성 완료**: 2025-12-11
**작성자**: Claude (auth-agent)
**검토 필요**: Orchestrator Agent
