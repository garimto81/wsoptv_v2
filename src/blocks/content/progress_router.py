"""
Progress Router - 시청 진행률 API (Frontend 호환)

엔드포인트:
- GET /api/v1/progress/{content_id}?token=... : 진행률 조회
- POST /api/v1/progress?token=... : 진행률 저장
- POST /api/v1/progress/{content_id}/complete?token=... : 시청 완료
"""


from fastapi import APIRouter, Query
from pydantic import BaseModel

from .service import ContentService

router = APIRouter(prefix="/progress", tags=["progress"])

# 서비스 인스턴스
_service = ContentService()


class ProgressUpdate(BaseModel):
    """진행률 업데이트 요청"""
    content_id: str
    position_seconds: int
    duration_seconds: int


class ProgressResponse(BaseModel):
    """진행률 응답"""
    content_id: str
    position_seconds: int
    duration_seconds: int
    progress_percent: float


def _get_user_id_from_token(token: str | None) -> str:
    """토큰에서 user_id 추출 (Mock: 토큰 그대로 사용)"""
    if not token:
        return "anonymous"
    # TODO: 실제 JWT 파싱으로 교체
    return token.replace("mock-", "").replace("-token", "") or "user"


@router.get("/{content_id}")
async def get_progress(
    content_id: str,
    token: str | None = Query(None)
) -> dict:
    """
    시청 진행률 조회

    Args:
        content_id: 콘텐츠 ID
        token: 인증 토큰

    Returns:
        진행률 정보 (progress_percent 포함)
    """
    user_id = _get_user_id_from_token(token)

    progress = await _service.get_progress(user_id=user_id, content_id=content_id)

    if not progress:
        # 진행률이 없으면 0으로 반환 (404 대신)
        return {
            "content_id": content_id,
            "position_seconds": 0,
            "duration_seconds": 0,
            "progress_percent": 0.0,
        }

    return {
        "content_id": progress.content_id,
        "position_seconds": progress.position_seconds,
        "duration_seconds": progress.total_seconds,
        "progress_percent": progress.percentage,
    }


@router.post("")
async def save_progress(
    data: ProgressUpdate,
    token: str | None = Query(None)
) -> dict:
    """
    시청 진행률 저장

    Args:
        data: 진행률 데이터
        token: 인증 토큰

    Returns:
        저장 성공 메시지
    """
    user_id = _get_user_id_from_token(token)

    await _service.update_progress(
        user_id=user_id,
        content_id=data.content_id,
        position_seconds=data.position_seconds,
        total_seconds=data.duration_seconds,
    )

    return {"status": "saved", "content_id": data.content_id}


@router.post("/{content_id}/complete")
async def mark_complete(
    content_id: str,
    token: str | None = Query(None)
) -> dict:
    """
    시청 완료 표시

    Args:
        content_id: 콘텐츠 ID
        token: 인증 토큰

    Returns:
        완료 성공 메시지
    """
    user_id = _get_user_id_from_token(token)

    # 100%로 진행률 업데이트
    await _service.update_progress(
        user_id=user_id,
        content_id=content_id,
        position_seconds=100,  # 완료 마커
        total_seconds=100,
    )

    return {"status": "completed", "content_id": content_id}
