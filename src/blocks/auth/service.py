"""
Auth Block Service

인증/인가 비즈니스 로직
"""

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional

from .models import User, UserStatus, Session, TokenResult
from src.orchestration.message_bus import MessageBus, BlockMessage


class AuthService:
    """
    인증/인가 서비스

    TDD 구현:
    - 간단한 해싱 (hashlib.sha256)
    - UUID 기반 토큰
    - 인메모리 저장소 (테스트용)
    """

    def __init__(self):
        # 인메모리 저장소 (실제로는 DB 사용)
        self._users: dict[str, User] = {}
        self._sessions: dict[str, Session] = {}
        self._email_to_user_id: dict[str, str] = {}
        self._bus = MessageBus.get_instance()

        # 테스트용 초기 데이터
        self._init_test_data()

    def _init_test_data(self):
        """테스트용 초기 데이터"""
        # 일반 사용자
        user_id = "user123"
        user = User(
            id=user_id,
            email="test@test.com",
            hashed_password=self._hash_password("password"),
            status=UserStatus.ACTIVE,
            is_admin=False,
        )
        self._users[user_id] = user
        self._email_to_user_id[user.email] = user_id

        # 관리자
        admin_id = "admin_user"
        admin = User(
            id=admin_id,
            email="admin@test.com",
            hashed_password=self._hash_password("admin"),
            status=UserStatus.ACTIVE,
            is_admin=True,
        )
        self._users[admin_id] = admin
        self._email_to_user_id[admin.email] = admin_id

        # 유효한 토큰 세션
        valid_token = "valid_jwt_token_123"
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=valid_token,
            expires_at=datetime.now() + timedelta(days=1),
        )
        self._sessions[valid_token] = session

        # 만료된 토큰 세션
        expired_token = "expired_jwt_token"
        expired_session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=expired_token,
            expires_at=datetime.now() - timedelta(days=1),  # 과거
        )
        self._sessions[expired_token] = expired_session

    def _hash_password(self, password: str) -> str:
        """비밀번호 해싱 (간단한 구현)"""
        return hashlib.sha256(password.encode()).hexdigest()

    async def register(self, email: str, password: str) -> User:
        """
        회원가입

        Args:
            email: 이메일
            password: 비밀번호

        Returns:
            생성된 사용자 (PENDING 상태)
        """
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            hashed_password=self._hash_password(password),
            status=UserStatus.PENDING,  # 승인 대기
            is_admin=False,
        )

        self._users[user_id] = user
        self._email_to_user_id[email] = user_id

        # 이벤트 발행
        await self._bus.publish(
            "auth.user_registered",
            BlockMessage(
                source_block="auth",
                event_type="user_registered",
                payload={
                    "user_id": user_id,
                    "email": email,
                    "status": UserStatus.PENDING.value,
                },
            ),
        )

        return user

    async def login(self, email: str, password: str) -> Session:
        """
        로그인

        Args:
            email: 이메일
            password: 비밀번호

        Returns:
            세션 정보

        Raises:
            ValueError: 인증 실패
        """
        user_id = self._email_to_user_id.get(email)
        if not user_id:
            raise ValueError("Invalid credentials")

        user = self._users[user_id]
        if user.hashed_password != self._hash_password(password):
            raise ValueError("Invalid credentials")

        if user.status != UserStatus.ACTIVE:
            raise ValueError("User not active")

        # 세션 생성
        token = str(uuid.uuid4())
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=token,
            expires_at=datetime.now() + timedelta(days=1),
        )
        self._sessions[token] = session

        # 이벤트 발행
        await self._bus.publish(
            "auth.user_login",
            BlockMessage(
                source_block="auth",
                event_type="user_login",
                payload={
                    "user_id": user_id,
                    "email": email,
                    "token": token,
                },
            ),
        )

        return session

    async def logout(self, token: str) -> bool:
        """
        로그아웃

        Args:
            token: 세션 토큰

        Returns:
            성공 여부
        """
        if token in self._sessions:
            session = self._sessions[token]
            del self._sessions[token]

            # 이벤트 발행
            await self._bus.publish(
                "auth.user_logout",
                BlockMessage(
                    source_block="auth",
                    event_type="user_logout",
                    payload={
                        "user_id": session.user_id,
                        "token": token,
                    },
                ),
            )
            return True

        return False

    async def validate_token(self, token: str) -> TokenResult:
        """
        토큰 검증

        Args:
            token: 검증할 토큰

        Returns:
            검증 결과
        """
        if token not in self._sessions:
            return TokenResult(valid=False, error="token_invalid")

        session = self._sessions[token]

        # 만료 확인
        if session.expires_at < datetime.now():
            return TokenResult(valid=False, error="token_expired")

        return TokenResult(valid=True, user_id=session.user_id)

    async def get_user(self, user_id: str) -> Optional[User]:
        """
        사용자 조회

        Args:
            user_id: 사용자 ID

        Returns:
            사용자 정보 또는 None
        """
        return self._users.get(user_id)

    async def check_permission(self, user_id: str, resource: str) -> bool:
        """
        권한 확인

        Args:
            user_id: 사용자 ID
            resource: 리소스 (예: "admin")

        Returns:
            권한 여부
        """
        user = self._users.get(user_id)
        if not user:
            return False

        # 간단한 권한 체크 (admin 리소스는 is_admin 필요)
        if resource == "admin":
            return user.is_admin

        # 기타 리소스는 ACTIVE 사용자면 접근 가능
        return user.status == UserStatus.ACTIVE

    async def approve_user(self, user_id: str) -> User:
        """
        사용자 승인 (관리자 전용)

        Args:
            user_id: 승인할 사용자 ID

        Returns:
            승인된 사용자

        Raises:
            ValueError: 사용자를 찾을 수 없음
        """
        user = self._users.get(user_id)
        if not user:
            raise ValueError("User not found")

        user.status = UserStatus.ACTIVE

        # 이벤트 발행
        await self._bus.publish(
            "auth.user_approved",
            BlockMessage(
                source_block="auth",
                event_type="user_approved",
                payload={
                    "user_id": user_id,
                    "email": user.email,
                    "status": UserStatus.ACTIVE.value,
                },
            ),
        )

        return user
