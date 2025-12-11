"""
Admin Block Router

FastAPI 라우터:
- GET /admin/dashboard
- GET /admin/users
- POST /admin/users/{user_id}/approve
- POST /admin/users/{user_id}/suspend
- GET /admin/system
- GET /admin/streams
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional, List, Dict

from .service import AdminService
from .models import DashboardData, SystemHealth


router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_service() -> AdminService:
    """AdminService 의존성"""
    return AdminService()


async def get_token(authorization: str = Header(...)) -> str:
    """
    Authorization 헤더에서 토큰 추출

    Args:
        authorization: Authorization 헤더 (Bearer {token})

    Returns:
        토큰

    Raises:
        HTTPException: 잘못된 헤더 형식
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    return authorization.replace("Bearer ", "")


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard(
    token: str = Depends(get_token),
    service: AdminService = Depends(get_admin_service),
):
    """
    대시보드 데이터 조회

    관리자 권한 필요
    """
    try:
        return await service.get_dashboard(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/users")
async def get_user_list(
    page: int = 1,
    size: int = 20,
    token: str = Depends(get_token),
    service: AdminService = Depends(get_admin_service),
):
    """
    사용자 목록 조회

    관리자 권한 필요

    Query Parameters:
    - page: 페이지 번호 (기본값: 1)
    - size: 페이지 크기 (기본값: 20)
    """
    try:
        return await service.get_user_list(token, page, size)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/users/{user_id}/approve")
async def approve_user(
    user_id: str,
    token: str = Depends(get_token),
    service: AdminService = Depends(get_admin_service),
):
    """
    사용자 승인

    관리자 권한 필요

    Path Parameters:
    - user_id: 승인할 사용자 ID
    """
    try:
        return await service.approve_user(token, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    token: str = Depends(get_token),
    service: AdminService = Depends(get_admin_service),
):
    """
    사용자 정지

    관리자 권한 필요

    Path Parameters:
    - user_id: 정지할 사용자 ID
    """
    try:
        return await service.suspend_user(token, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/system", response_model=SystemHealth)
async def get_system_stats(
    token: str = Depends(get_token),
    service: AdminService = Depends(get_admin_service),
):
    """
    시스템 상태 조회

    관리자 권한 필요
    """
    try:
        return await service.get_system_stats(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/streams")
async def get_active_streams(
    token: str = Depends(get_token),
    service: AdminService = Depends(get_admin_service),
) -> List[Dict]:
    """
    활성 스트림 목록 조회

    관리자 권한 필요
    """
    try:
        return await service.get_active_streams(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
