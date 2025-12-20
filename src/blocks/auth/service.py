"""
Auth Block Service

인증/인가 비즈니스 로직 - PostgreSQL 연동
"""

import uuid
from datetime import datetime, timedelta

import bcrypt

from src.core.database import Database
from src.orchestration.message_bus import BlockMessage, MessageBus

from .models import Session, TokenResult, User, UserStatus


class AuthService:
    """
    인증/인가 서비스

    PostgreSQL 연동:
    - bcrypt 비밀번호 해싱
    - UUID 기반 토큰
    - DB 기반 사용자 관리 + 인메모리 세션
    """

    def __init__(self):
        # 인메모리 세션 저장소
        self._sessions: dict[str, Session] = {}
        self._bus = MessageBus.get_instance()

    def _hash_password(self, password: str) -> str:
        """비밀번호 해싱 (bcrypt)"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, hashed: str) -> bool:
        """비밀번호 검증 (bcrypt)"""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception:
            return False

    async def register(self, email: str, password: str) -> User:
        """
        회원가입

        Args:
            email: 이메일
            password: 비밀번호

        Returns:
            생성된 사용자 (PENDING 상태)
        """
        hashed_password = self._hash_password(password)

        async with Database.connection() as conn:
            # 이메일 중복 체크
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", email
            )
            if existing:
                raise ValueError("Email already exists")

            # 사용자 생성
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, password_hash, role, status)
                VALUES ($1, $2, 'user', 'pending')
                RETURNING id, email, role, status, created_at
                """,
                email,
                hashed_password,
            )

        user = User(
            id=str(row["id"]),
            email=row["email"],
            hashed_password=hashed_password,
            status=UserStatus(row["status"]),
            is_admin=row["role"] == "admin",
        )

        # 이벤트 발행
        await self._bus.publish(
            "auth.user_registered",
            BlockMessage(
                source_block="auth",
                event_type="user_registered",
                payload={
                    "user_id": user.id,
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
        async with Database.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, password_hash, role, status
                FROM users WHERE email = $1
                """,
                email,
            )

        if not row:
            raise ValueError("Invalid credentials")

        if not self._verify_password(password, row["password_hash"]):
            raise ValueError("Invalid credentials")

        if row["status"] != "active":
            raise ValueError("User not active")

        user_id = str(row["id"])

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

    async def get_user(self, user_id: str) -> User | None:
        """
        사용자 조회

        Args:
            user_id: 사용자 ID

        Returns:
            사용자 정보 또는 None
        """
        async with Database.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, password_hash, role, status
                FROM users WHERE id = $1
                """,
                uuid.UUID(user_id),
            )

        if not row:
            return None

        return User(
            id=str(row["id"]),
            email=row["email"],
            hashed_password=row["password_hash"],
            status=UserStatus(row["status"]),
            is_admin=row["role"] == "admin",
        )

    async def check_permission(self, user_id: str, resource: str) -> bool:
        """
        권한 확인

        Args:
            user_id: 사용자 ID
            resource: 리소스 (예: "admin")

        Returns:
            권한 여부
        """
        user = await self.get_user(user_id)
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
        async with Database.connection() as conn:
            row = await conn.fetchrow(
                """
                UPDATE users SET status = 'active', updated_at = NOW()
                WHERE id = $1
                RETURNING id, email, password_hash, role, status
                """,
                uuid.UUID(user_id),
            )

        if not row:
            raise ValueError("User not found")

        user = User(
            id=str(row["id"]),
            email=row["email"],
            hashed_password=row["password_hash"],
            status=UserStatus(row["status"]),
            is_admin=row["role"] == "admin",
        )

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
