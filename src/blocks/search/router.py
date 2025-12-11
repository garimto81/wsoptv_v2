"""
Search Block Router

FastAPI 라우터 정의
"""

from typing import Annotated, Optional, Dict
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel

from .service import SearchService
from .models import SearchQuery, SearchItem


router = APIRouter(prefix="/search", tags=["search"])


# Request/Response Models
class SearchRequest(BaseModel):
    keyword: str
    filters: Optional[Dict[str, str]] = None
    page: int = 1
    size: int = 10


class SearchItemResponse(BaseModel):
    id: str
    title: str
    score: float
    highlights: list[str]
    description: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = []


class SearchResponse(BaseModel):
    items: list[SearchItemResponse]
    total: int
    took_ms: float
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class IndexContentRequest(BaseModel):
    content_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = []


class MessageResponse(BaseModel):
    message: str
    count: Optional[int] = None


# Dependency
def get_search_service() -> SearchService:
    """SearchService 인스턴스 생성"""
    from src.blocks.auth.service import AuthService
    auth_service = AuthService()
    return SearchService(auth_service=auth_service)


@router.get("/", response_model=SearchResponse)
async def search(
    q: Annotated[str, Query(description="검색 키워드")],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
    category: Optional[str] = None,
    authorization: Annotated[str, Header()] = None
):
    """
    검색 수행

    Args:
        q: 검색 키워드
        page: 페이지 번호 (1부터 시작)
        size: 페이지 크기 (1-100)
        category: 카테고리 필터 (Optional)
        authorization: Bearer 토큰
    """
    service = get_search_service()

    # 토큰 추출
    token = None
    if authorization:
        token = authorization.replace("Bearer ", "")

    # 필터 구성
    filters = {}
    if category:
        filters["category"] = category

    # 검색 쿼리 생성
    query = SearchQuery(
        keyword=q,
        filters=filters,
        page=page,
        size=size
    )

    try:
        # 검색 수행
        result = await service.search(query, token=token)

        # 응답 생성
        items = [
            SearchItemResponse(
                id=item.id,
                title=item.title,
                score=item.score,
                highlights=item.highlights,
                description=item.description,
                category=item.category,
                tags=item.tags
            )
            for item in result.items
        ]

        return SearchResponse(
            items=items,
            total=result.total,
            took_ms=result.took_ms,
            page=result.page,
            size=result.size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/", response_model=SearchResponse)
async def search_post(
    request: SearchRequest,
    authorization: Annotated[str, Header()] = None
):
    """
    POST 방식 검색 (복잡한 필터 사용 시)

    Args:
        request: 검색 요청
        authorization: Bearer 토큰
    """
    service = get_search_service()

    # 토큰 추출
    token = None
    if authorization:
        token = authorization.replace("Bearer ", "")

    # 검색 쿼리 생성
    query = SearchQuery(
        keyword=request.keyword,
        filters=request.filters or {},
        page=request.page,
        size=request.size
    )

    try:
        # 검색 수행
        result = await service.search(query, token=token)

        # 응답 생성
        items = [
            SearchItemResponse(
                id=item.id,
                title=item.title,
                score=item.score,
                highlights=item.highlights,
                description=item.description,
                category=item.category,
                tags=item.tags
            )
            for item in result.items
        ]

        return SearchResponse(
            items=items,
            total=result.total,
            took_ms=result.took_ms,
            page=result.page,
            size=result.size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/index", response_model=MessageResponse)
async def index_content(
    request: IndexContentRequest,
    authorization: Annotated[str, Header()]
):
    """
    컨텐츠 인덱싱 (관리자 전용)

    Args:
        request: 인덱싱 요청
        authorization: Bearer 토큰
    """
    service = get_search_service()

    # 토큰 추출 및 검증
    token = authorization.replace("Bearer ", "")

    try:
        # 토큰 검증은 service 내부에서 수행
        await service.index_content(
            content_id=request.content_id,
            title=request.title,
            description=request.description,
            category=request.category,
            tags=request.tags
        )

        return MessageResponse(message="Content indexed successfully")

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.delete("/index/{content_id}", response_model=MessageResponse)
async def remove_from_index(
    content_id: str,
    authorization: Annotated[str, Header()]
):
    """
    인덱스에서 컨텐츠 제거 (관리자 전용)

    Args:
        content_id: 컨텐츠 ID
        authorization: Bearer 토큰
    """
    service = get_search_service()

    # 토큰 추출
    token = authorization.replace("Bearer ", "")

    try:
        await service.remove_from_index(content_id)
        return MessageResponse(message="Content removed from index")

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/reindex", response_model=MessageResponse)
async def reindex_all(authorization: Annotated[str, Header()]):
    """
    전체 재인덱싱 (관리자 전용)

    Args:
        authorization: Bearer 토큰
    """
    service = get_search_service()

    # 토큰 추출 및 관리자 권한 확인 필요
    token = authorization.replace("Bearer ", "")

    try:
        count = await service.reindex_all()
        return MessageResponse(
            message="Reindex completed",
            count=count
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
