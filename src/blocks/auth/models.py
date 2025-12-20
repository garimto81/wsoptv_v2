"""
Auth Block Models

사용자, 세션, 토큰 결과 모델
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class UserStatus(Enum):
    """사용자 상태"""
    PENDING = "pending"      # 승인 대기
    ACTIVE = "active"        # 활성
    SUSPENDED = "suspended"  # 정지


@dataclass
class User:
    """사용자 모델"""
    id: str
    email: str
    hashed_password: str
    status: UserStatus
    is_admin: bool = False
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Session:
    """세션 모델"""
    id: str
    user_id: str
    token: str
    expires_at: datetime


@dataclass
class TokenResult:
    """토큰 검증 결과"""
    valid: bool
    user_id: str | None = None
    error: str | None = None
