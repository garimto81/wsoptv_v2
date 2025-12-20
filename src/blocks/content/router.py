"""
Content Router - FastAPI 엔드포인트

콘텐츠 조회, 카탈로그, 시청 진행률 API
"""


from fastapi import APIRouter, Header, HTTPException

from .service import AuthenticationError, ContentService

router = APIRouter(prefix="/content", tags=["content"])

# 서비스 인스턴스 (실제로는 의존성 주입 사용)
_service = ContentService()


@router.get("/{content_id}", response_model=dict)
async def get_content(
    content_id: str, authorization: str | None = Header(None)
) -> dict:
    """
    콘텐츠 조회

    Args:
        content_id: 콘텐츠 ID
        authorization: Bearer 토큰

    Returns:
        콘텐츠 정보
    """
    try:
        # Bearer 토큰 추출
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")

        content = await _service.get_content(content_id, token=token)

        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        return {
            "id": content.id,
            "title": content.title,
            "duration_seconds": content.duration_seconds,
            "file_size_bytes": content.file_size_bytes,
            "codec": content.codec,
            "resolution": content.resolution,
            "path": content.path,
            "created_at": content.created_at.isoformat(),
        }

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/", response_model=dict)
async def get_catalog(page: int = 1, size: int = 20) -> dict:
    """
    콘텐츠 카탈로그 조회

    Args:
        page: 페이지 번호 (1부터 시작)
        size: 페이지 크기

    Returns:
        카탈로그 정보
    """
    catalog = await _service.get_catalog(page=page, size=size)

    return {
        "items": [
            {"id": item.id, "title": item.title, "duration_seconds": item.duration_seconds}
            for item in catalog.items
        ],
        "total": catalog.total,
        "page": catalog.page,
        "size": catalog.size,
    }


@router.post("/{content_id}/progress", status_code=204)
async def update_progress(
    content_id: str,
    user_id: str,
    position_seconds: int,
    total_seconds: int,
) -> None:
    """
    시청 진행률 업데이트

    Args:
        content_id: 콘텐츠 ID
        user_id: 사용자 ID
        position_seconds: 현재 재생 위치 (초)
        total_seconds: 전체 길이 (초)
    """
    await _service.update_progress(
        user_id=user_id,
        content_id=content_id,
        position_seconds=position_seconds,
        total_seconds=total_seconds,
    )


@router.get("/{content_id}/progress", response_model=dict)
async def get_progress(content_id: str, user_id: str) -> dict:
    """
    시청 진행률 조회

    Args:
        content_id: 콘텐츠 ID
        user_id: 사용자 ID

    Returns:
        진행률 정보
    """
    progress = await _service.get_progress(user_id=user_id, content_id=content_id)

    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    return {
        "user_id": progress.user_id,
        "content_id": progress.content_id,
        "position_seconds": progress.position_seconds,
        "total_seconds": progress.total_seconds,
        "percentage": progress.percentage,
    }
