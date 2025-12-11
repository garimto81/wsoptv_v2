# Auth Agent Todo

**Block**: Auth (L0 - 무의존)
**Agent**: auth-agent
**Wave**: 1 (병렬 시작 가능)

---

## 컨텍스트 제한

```
✅ 수정 가능:
  - src/blocks/auth/**
  - tests/test_blocks/test_auth_block.py
  - docs/blocks/01-auth.md

❌ 수정 불가:
  - src/blocks/*/ (다른 블럭)
  - src/orchestration/ (읽기 전용)
```

---

## Todo List

### TDD Red Phase
- [ ] A1: `tests/test_blocks/test_auth_block.py` 확장
  - [ ] test_register_user
  - [ ] test_login_success / test_login_fail
  - [ ] test_validate_token_valid / test_validate_token_expired
  - [ ] test_check_permission
  - [ ] test_user_approval_flow

### TDD Green Phase
- [ ] A2: `src/blocks/auth/models.py`
  - [ ] User 모델 (id, email, hashed_password, status, is_admin)
  - [ ] UserStatus Enum (pending, active, suspended)
  - [ ] Session 모델 (id, user_id, token, expires_at)
  - [ ] TokenResult 모델 (valid, user_id, error)

- [ ] A3: `src/blocks/auth/service.py`
  - [ ] register(email, password) → User
  - [ ] login(email, password) → Session
  - [ ] logout(token) → bool
  - [ ] validate_token(token) → TokenResult
  - [ ] get_user(user_id) → User | None
  - [ ] check_permission(user_id, resource) → bool
  - [ ] approve_user(user_id) → User (admin only)

- [ ] A4: `src/blocks/auth/router.py`
  - [ ] POST /auth/register
  - [ ] POST /auth/login
  - [ ] POST /auth/logout
  - [ ] GET /auth/me
  - [ ] POST /auth/users/{id}/approve (admin)

- [ ] A5: 테스트 통과 확인
  - [ ] pytest tests/test_blocks/test_auth_block.py -v
  - [ ] 커버리지 80% 이상

### Refactor Phase
- [ ] A6: 코드 리팩토링
  - [ ] Password hashing (bcrypt/argon2)
  - [ ] JWT token generation
  - [ ] Session management 최적화

- [ ] A7: 문서 업데이트
  - [ ] docs/blocks/01-auth.md API 섹션 업데이트
  - [ ] Contract 버전 명시

---

## 이벤트 발행 (Orchestration 통해)

```python
# 발행 이벤트
await bus.publish("auth.user_registered", BlockMessage(...))
await bus.publish("auth.user_login", BlockMessage(...))
await bus.publish("auth.user_logout", BlockMessage(...))
await bus.publish("auth.user_approved", BlockMessage(...))
```

## 제공 API (Contract)

```python
# 다른 블럭이 호출할 수 있는 API
validate_token(token: str) -> TokenResult
get_user(user_id: str) -> User | None
check_permission(user_id: str, resource: str) -> bool
```

---

## Progress: 0/7 (0%)
