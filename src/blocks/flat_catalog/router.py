"""
Block F: Flat Catalog - API 라우터

카탈로그 관련 REST API 엔드포인트.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.blocks.flat_catalog.models import CatalogItem, NASFileInfo
from src.blocks.flat_catalog.service import FlatCatalogService, get_flat_catalog_service

router = APIRouter(prefix="/catalog", tags=["catalog"])


# Pydantic 스키마
class CatalogItemResponse(BaseModel):
    """카탈로그 아이템 응답"""

    id: str
    nas_file_id: str | None
    display_title: str
    short_title: str
    thumbnail_url: str | None
    project_code: str
    year: int | None
    category_tags: list[str]
    file_path: str
    file_name: str
    file_size_bytes: int
    file_size_formatted: str
    file_extension: str
    duration_seconds: int | None
    quality: str | None
    is_visible: bool
    confidence: float
    created_at: str
    updated_at: str


class CatalogListResponse(BaseModel):
    """카탈로그 목록 응답"""

    items: list[CatalogItemResponse]
    total: int
    skip: int
    limit: int


class CatalogUpdateRequest(BaseModel):
    """카탈로그 업데이트 요청"""

    display_title: str | None = None
    short_title: str | None = None
    thumbnail_url: str | None = None
    is_visible: bool | None = None
    category_tags: list[str] | None = None


class NASFileRequest(BaseModel):
    """NAS 파일 정보 요청"""

    id: str
    file_path: str
    file_name: str
    file_size_bytes: int
    file_extension: str
    file_category: str = "VIDEO"
    is_hidden_file: bool = False


class SyncRequest(BaseModel):
    """동기화 요청"""

    files: list[NASFileRequest] = Field(
        ..., min_length=1, max_length=5000, description="NAS 파일 목록"
    )


class SyncResponse(BaseModel):
    """동기화 응답"""

    created: int
    updated: int
    deleted: int
    skipped: int
    errors: int
    total_processed: int
    duration_seconds: float
    error_messages: list[str]


class ProjectStats(BaseModel):
    """프로젝트 통계"""

    code: str
    count: int


class CatalogStats(BaseModel):
    """카탈로그 통계"""

    total_items: int
    visible_items: int
    projects: list[ProjectStats]
    years: list[int]


# 의존성
CatalogServiceDep = Annotated[FlatCatalogService, Depends(get_flat_catalog_service)]


def _to_response(item: CatalogItem) -> CatalogItemResponse:
    """CatalogItem을 응답 스키마로 변환"""
    return CatalogItemResponse(
        id=str(item.id),
        nas_file_id=str(item.nas_file_id) if item.nas_file_id else None,
        display_title=item.display_title,
        short_title=item.short_title,
        thumbnail_url=item.thumbnail_url,
        project_code=item.project_code,
        year=item.year,
        category_tags=item.category_tags,
        file_path=item.file_path,
        file_name=item.file_name,
        file_size_bytes=item.file_size_bytes,
        file_size_formatted=item.format_file_size(),
        file_extension=item.file_extension,
        duration_seconds=item.duration_seconds,
        quality=item.quality,
        is_visible=item.is_visible,
        confidence=item.confidence,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


@router.get(
    "/",
    response_model=CatalogListResponse,
    summary="카탈로그 목록",
    description="필터링 및 페이지네이션을 지원하는 카탈로그 목록을 반환합니다.",
)
async def list_catalog(
    service: CatalogServiceDep,
    project_code: str | None = Query(None, description="프로젝트 코드 필터"),
    year: int | None = Query(None, description="연도 필터"),
    visible_only: bool = Query(True, description="표시 가능한 항목만"),
    skip: int = Query(0, ge=0, description="스킵할 개수"),
    limit: int = Query(100, ge=1, le=500, description="반환할 최대 개수"),
) -> CatalogListResponse:
    """
    카탈로그 목록 조회

    - **project_code**: WSOP, HCL, GGMILLIONS, GOG, MPP, PAD, OTHER
    - **year**: 연도 필터 (예: 2024)
    - **visible_only**: True면 숨김 항목 제외
    - **skip/limit**: 페이지네이션
    """
    items = service.get_all(
        project_code=project_code,
        year=year,
        visible_only=visible_only,
        skip=skip,
        limit=limit,
    )
    total = service.count(project_code=project_code, visible_only=visible_only)

    return CatalogListResponse(
        items=[_to_response(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/search",
    response_model=list[CatalogItemResponse],
    summary="카탈로그 검색",
    description="제목 및 태그 기반 검색을 수행합니다.",
)
async def search_catalog(
    service: CatalogServiceDep,
    q: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(50, ge=1, le=100, description="반환할 최대 개수"),
) -> list[CatalogItemResponse]:
    """
    카탈로그 검색

    제목과 카테고리 태그에서 검색어를 찾습니다.
    결과는 신뢰도 기준으로 정렬됩니다.
    """
    items = service.search(query=q, limit=limit)
    return [_to_response(item) for item in items]


@router.get(
    "/stats",
    response_model=CatalogStats,
    summary="카탈로그 통계",
    description="프로젝트별 통계 및 연도 목록을 반환합니다.",
)
async def get_catalog_stats(
    service: CatalogServiceDep,
) -> CatalogStats:
    """카탈로그 통계"""
    projects_raw = service.get_projects()
    years = service.get_years()

    return CatalogStats(
        total_items=service.count(visible_only=False),
        visible_items=service.count(visible_only=True),
        projects=[ProjectStats(code=p["code"], count=p["count"]) for p in projects_raw],
        years=years,
    )


@router.get(
    "/projects",
    response_model=list[ProjectStats],
    summary="프로젝트 목록",
    description="프로젝트별 콘텐츠 개수를 반환합니다.",
)
async def list_projects(
    service: CatalogServiceDep,
) -> list[ProjectStats]:
    """프로젝트별 통계"""
    projects_raw = service.get_projects()
    return [ProjectStats(code=p["code"], count=p["count"]) for p in projects_raw]


@router.get(
    "/years",
    response_model=list[int],
    summary="연도 목록",
    description="콘텐츠가 있는 연도 목록을 반환합니다.",
)
async def list_years(
    service: CatalogServiceDep,
    project_code: str | None = Query(None, description="프로젝트 코드 필터"),
) -> list[int]:
    """연도 목록 (내림차순)"""
    return service.get_years(project_code=project_code)


@router.get(
    "/{item_id}",
    response_model=CatalogItemResponse,
    summary="카탈로그 상세",
    description="특정 카탈로그 아이템의 상세 정보를 반환합니다.",
)
async def get_catalog_item(
    item_id: UUID,
    service: CatalogServiceDep,
) -> CatalogItemResponse:
    """카탈로그 아이템 상세 조회"""
    item = service.get_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item not found: {item_id}",
        )
    return _to_response(item)


@router.patch(
    "/{item_id}",
    response_model=CatalogItemResponse,
    summary="카탈로그 수정",
    description="카탈로그 아이템의 정보를 수정합니다.",
)
async def update_catalog_item(
    item_id: UUID,
    request: CatalogUpdateRequest,
    service: CatalogServiceDep,
) -> CatalogItemResponse:
    """
    카탈로그 아이템 수정

    제목, 썸네일, 가시성, 태그를 수정할 수 있습니다.
    """
    # None이 아닌 필드만 업데이트
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    item = service.update(item_id, **update_data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item not found: {item_id}",
        )
    return _to_response(item)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="카탈로그 삭제",
    description="카탈로그 아이템을 삭제합니다.",
)
async def delete_catalog_item(
    item_id: UUID,
    service: CatalogServiceDep,
) -> None:
    """카탈로그 아이템 삭제"""
    success = service.delete(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item not found: {item_id}",
        )


@router.post(
    "/{item_id}/visibility",
    response_model=CatalogItemResponse,
    summary="가시성 변경",
    description="카탈로그 아이템의 표시 여부를 변경합니다.",
)
async def set_visibility(
    item_id: UUID,
    service: CatalogServiceDep,
    visible: bool = Query(..., description="표시 여부"),
) -> CatalogItemResponse:
    """가시성 설정"""
    item = service.set_visibility(item_id, visible)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item not found: {item_id}",
        )
    return _to_response(item)


@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="NAS 동기화",
    description="NAS 파일 목록과 카탈로그를 동기화합니다.",
)
async def sync_catalog(
    request: SyncRequest,
    service: CatalogServiceDep,
) -> SyncResponse:
    """
    NAS 파일 목록에서 카탈로그 동기화

    - 새 파일: 카탈로그 아이템 생성
    - 기존 파일: 변경사항 업데이트
    - 삭제된 파일: 카탈로그에서 제거
    """
    # NASFileInfo 객체로 변환
    nas_files = [
        NASFileInfo(
            id=UUID(f.id),
            file_path=f.file_path,
            file_name=f.file_name,
            file_size_bytes=f.file_size_bytes,
            file_extension=f.file_extension,
            file_category=f.file_category,
            is_hidden_file=f.is_hidden_file,
        )
        for f in request.files
    ]

    result = service.sync_from_nas_files(nas_files)

    return SyncResponse(
        created=result.created,
        updated=result.updated,
        deleted=result.deleted,
        skipped=result.skipped,
        errors=result.errors,
        total_processed=result.total_processed,
        duration_seconds=result.duration_seconds,
        error_messages=result.error_messages,
    )


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="전체 삭제",
    description="모든 카탈로그 아이템을 삭제합니다. (주의: 복구 불가)",
)
async def clear_catalog(
    service: CatalogServiceDep,
    confirm: bool = Query(False, description="삭제 확인"),
) -> None:
    """
    전체 카탈로그 삭제

    confirm=true 파라미터가 필요합니다.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required: set confirm=true",
        )
    service.clear()
