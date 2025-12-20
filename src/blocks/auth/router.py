"""
Auth Block Router

FastAPI 라우터 정의
"""

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from .models import UserStatus
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


# Request/Response Models
class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: str


class UserResponse(BaseModel):
    id: str
    email: str
    status: UserStatus
    is_admin: bool


class MessageResponse(BaseModel):
    message: str


# Singleton instance
_auth_service: AuthService | None = None


# Dependency
def get_auth_service() -> AuthService:
    """AuthService 싱글톤 인스턴스 반환"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


def reset_auth_service():
    """테스트용: AuthService 인스턴스 리셋"""
    global _auth_service
    _auth_service = None


@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """회원가입"""
    service = get_auth_service()
    user = await service.register(request.email, request.password)

    return UserResponse(
        id=user.id,
        email=user.email,
        status=user.status,
        is_admin=user.is_admin,
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """로그인"""
    service = get_auth_service()

    try:
        session = await service.login(request.email, request.password)
        return LoginResponse(token=session.token, user_id=session.user_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
async def logout(authorization: Annotated[str, Header()]):
    """로그아웃"""
    service = get_auth_service()

    # Bearer 토큰 추출
    token = authorization.replace("Bearer ", "")

    success = await service.logout(token)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(authorization: Annotated[str, Header()]):
    """현재 사용자 정보 조회"""
    service = get_auth_service()

    # Bearer 토큰 추출
    token = authorization.replace("Bearer ", "")

    # 토큰 검증
    result = await service.validate_token(token)
    if not result.valid:
        raise HTTPException(status_code=401, detail=result.error)

    # 사용자 조회
    user = await service.get_user(result.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        status=user.status,
        is_admin=user.is_admin,
    )


@router.post("/users/{user_id}/approve", response_model=UserResponse)
async def approve_user(user_id: str, authorization: Annotated[str, Header()]):
    """사용자 승인 (관리자 전용)"""
    service = get_auth_service()

    # Bearer 토큰 추출
    token = authorization.replace("Bearer ", "")

    # 토큰 검증
    result = await service.validate_token(token)
    if not result.valid:
        raise HTTPException(status_code=401, detail=result.error)

    # 관리자 권한 확인
    has_admin = await service.check_permission(result.user_id, "admin")
    if not has_admin:
        raise HTTPException(status_code=403, detail="Admin permission required")

    # 사용자 승인
    try:
        approved_user = await service.approve_user(user_id)
        return UserResponse(
            id=approved_user.id,
            email=approved_user.email,
            status=approved_user.status,
            is_admin=approved_user.is_admin,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
