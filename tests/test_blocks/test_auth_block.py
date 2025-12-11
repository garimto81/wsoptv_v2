"""
Auth Block 테스트

TDD RED Phase: Auth 블럭의 핵심 기능 검증
"""

import pytest
from datetime import datetime, timedelta


class TestAuthBlock:
    """Auth Block - L0 (무의존) 블럭 테스트"""

    @pytest.mark.asyncio
    async def test_validate_token_success(self):
        """유효한 토큰 검증"""
        from src.blocks.auth.service import AuthService

        service = AuthService()
        token = "valid_jwt_token_123"

        result = await service.validate_token(token)

        assert result.valid is True
        assert result.user_id is not None

    @pytest.mark.asyncio
    async def test_validate_token_expired(self):
        """만료된 토큰 검증"""
        from src.blocks.auth.service import AuthService

        service = AuthService()
        expired_token = "expired_jwt_token"

        result = await service.validate_token(expired_token)

        assert result.valid is False
        assert result.error == "token_expired"

    @pytest.mark.asyncio
    async def test_get_user(self):
        """사용자 정보 조회"""
        from src.blocks.auth.service import AuthService

        service = AuthService()

        user = await service.get_user("user123")

        assert user is not None
        assert user.id == "user123"

    @pytest.mark.asyncio
    async def test_check_permission(self):
        """권한 검증"""
        from src.blocks.auth.service import AuthService

        service = AuthService()

        # 일반 사용자 - admin 권한 없음
        has_admin = await service.check_permission("user123", "admin")
        assert has_admin is False

        # 관리자 - admin 권한 있음
        has_admin = await service.check_permission("admin_user", "admin")
        assert has_admin is True

    @pytest.mark.asyncio
    async def test_user_approval_flow(self):
        """사용자 승인 플로우 (Register → Pending → Approve → Active)"""
        from src.blocks.auth.service import AuthService
        from src.blocks.auth.models import UserStatus

        service = AuthService()

        # 1. 회원가입 → pending 상태
        user = await service.register(
            email="newuser@test.com",
            password="password123"
        )
        assert user.status == UserStatus.PENDING

        # 2. 관리자 승인 → active 상태
        approved_user = await service.approve_user(user.id)
        assert approved_user.status == UserStatus.ACTIVE


class TestAuthBlockEvents:
    """Auth Block 이벤트 발행 테스트"""

    @pytest.mark.asyncio
    async def test_user_registered_event(self):
        """사용자 등록 시 이벤트 발행"""
        from src.blocks.auth.service import AuthService
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        received_events = []

        async def handler(msg):
            received_events.append(msg)

        await bus.subscribe("auth.user_registered", handler)

        service = AuthService()
        await service.register("test@test.com", "password")

        assert len(received_events) == 1
        assert received_events[0].event_type == "user_registered"

    @pytest.mark.asyncio
    async def test_user_login_event(self):
        """로그인 시 이벤트 발행"""
        from src.blocks.auth.service import AuthService
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        received_events = []

        async def handler(msg):
            received_events.append(msg)

        await bus.subscribe("auth.user_login", handler)

        service = AuthService()
        await service.login("test@test.com", "password")

        assert len(received_events) == 1
        assert received_events[0].event_type == "user_login"


class TestAuthRouter:
    """Auth Router 통합 테스트 - FastAPI 엔드포인트 검증"""

    @pytest.fixture
    def client(self):
        """TestClient 생성 (각 테스트마다 AuthService 리셋)"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.blocks.auth.router import router, reset_auth_service

        # 각 테스트 전 AuthService 리셋하여 깨끗한 상태에서 시작
        reset_auth_service()

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_register_endpoint(self, client):
        """회원가입 엔드포인트 테스트"""
        response = client.post(
            "/auth/register",
            json={"email": "newuser@test.com", "password": "pass123"}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["email"] == "newuser@test.com"

    def test_login_endpoint(self, client):
        """로그인 엔드포인트 테스트 - 사전 등록된 활성 사용자로 테스트"""
        # AuthService는 테스트용 초기 데이터로 test@test.com (ACTIVE) 사용자가 있음
        response = client.post(
            "/auth/login",
            json={"email": "test@test.com", "password": "password"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user_id" in data

    def test_login_with_invalid_credentials(self, client):
        """잘못된 인증 정보로 로그인 시도"""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@test.com", "password": "wrongpass"}
        )
        assert response.status_code == 401

    def test_logout_endpoint(self, client):
        """로그아웃 엔드포인트 테스트"""
        # 사전 등록된 활성 사용자로 로그인
        login_resp = client.post(
            "/auth/login",
            json={"email": "test@test.com", "password": "password"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]

        # 로그아웃
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_me_endpoint_without_token(self, client):
        """토큰 없이 /me 엔드포인트 호출"""
        response = client.get("/auth/me")
        assert response.status_code == 422  # Validation error (missing header)

    def test_me_endpoint_with_invalid_token(self, client):
        """유효하지 않은 토큰으로 /me 엔드포인트 호출"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_me_endpoint_with_valid_token(self, client):
        """유효한 토큰으로 /me 엔드포인트 호출"""
        # 사전 등록된 활성 사용자로 로그인
        login_resp = client.post(
            "/auth/login",
            json={"email": "test@test.com", "password": "password"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]

        # /me 호출
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@test.com"

    def test_approve_user_endpoint_without_admin(self, client):
        """관리자 권한 없이 사용자 승인 시도"""
        # 일반 사용자(test@test.com)로 로그인
        login_resp = client.post(
            "/auth/login",
            json={"email": "test@test.com", "password": "password"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]

        # 다른 사용자 승인 시도 - 일반 사용자는 admin 권한이 없음
        response = client.post(
            "/auth/users/someuser/approve",
            headers={"Authorization": f"Bearer {token}"}
        )
        # 관리자가 아니면 403
        assert response.status_code == 403

    def test_register_validation_error(self, client):
        """잘못된 요청 데이터로 회원가입 시도"""
        response = client.post(
            "/auth/register",
            json={"email": "invalid"}  # password 누락
        )
        assert response.status_code == 422  # Validation error
