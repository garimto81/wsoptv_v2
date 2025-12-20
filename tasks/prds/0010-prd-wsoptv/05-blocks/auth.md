# Auth Block PRD

**Version**: 2.0.0 | **Block ID**: auth | **Level**: L0 (No dependencies)

---

## 1. Overview

Auth Block은 WSOPTV 시스템의 **인증(Authentication)**, **인가(Authorization)**, **사용자 관리**를 담당하는 최하위 의존성 블럭입니다.

### 책임 범위

| 책임 영역 | 세부 기능 |
|----------|----------|
| **인증** | 회원가입, 로그인, 로그아웃, 토큰 발급/갱신 |
| **인가** | 권한 검증, 역할 기반 접근 제어 (RBAC) |
| **사용자 관리** | 사용자 정보 CRUD, 상태 관리, 프로필 관리 |
| **세션 관리** | JWT 기반 세션, 토큰 블랙리스트 관리 |

### 독립성 원칙

- L0 블럭: 다른 블럭에 의존하지 않음
- 모든 블럭이 Auth Block의 인증/인가 서비스 사용
- 외부 의존성 최소화 (bcrypt, PyJWT만 허용)

---

## 2. API Endpoints

### 인증 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 |
| POST | `/api/auth/logout` | 로그아웃 |
| POST | `/api/auth/refresh` | 토큰 갱신 |

### 사용자 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/users/me` | 내 정보 조회 |
| PATCH | `/api/users/me` | 내 정보 수정 |
| GET | `/api/users/{id}` | 사용자 조회 (admin) |

---

## 3. Data Models

### User

```python
class User(Base):
    id: UUID
    email: str              # unique
    password_hash: str
    username: str           # unique
    full_name: str
    role: UserRole          # user, admin
    subscription_status: SubscriptionStatus  # free, premium
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### Session

```python
class Session(Base):
    id: UUID
    user_id: UUID
    refresh_token: str
    expires_at: datetime
    created_at: datetime
```

---

## 4. Security

### JWT 설정

| 항목 | 값 |
|------|---|
| Access Token TTL | 15분 |
| Refresh Token TTL | 7일 |
| 알고리즘 | HS256 |
| 블랙리스트 | Redis |

### 비밀번호 정책

- 최소 8자
- 대문자, 소문자, 숫자 포함
- bcrypt 해싱 (cost factor: 12)

---

## 5. Events

### 발행 이벤트

| 채널 | 페이로드 | 설명 |
|------|----------|------|
| `auth.user_created` | `{user_id, email}` | 사용자 생성됨 |
| `auth.user_updated` | `{user_id, fields}` | 사용자 정보 수정됨 |
| `auth.login_success` | `{user_id}` | 로그인 성공 |
| `auth.subscription_changed` | `{user_id, status}` | 구독 상태 변경 |

---

## 6. Contracts

### 제공 계약 (다른 블럭에서 호출 가능)

```python
class AuthContract:
    async def validate_token(token: str) -> User:
        """토큰 검증 및 사용자 반환"""

    async def get_user(user_id: UUID) -> User:
        """사용자 조회"""

    async def check_subscription(user_id: UUID) -> SubscriptionStatus:
        """구독 상태 확인"""

    async def require_role(user: User, role: UserRole) -> bool:
        """역할 검증"""
```

---

*Parent: [04-technical.md](../04-technical.md)*
