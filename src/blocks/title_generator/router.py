"""
Block G: Title Generator - API 라우터

제목 생성 관련 REST API 엔드포인트.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.blocks.title_generator.models import GeneratedTitle
from src.blocks.title_generator.service import (
    TitleGeneratorService,
    get_title_generator_service,
)

router = APIRouter(prefix="/title", tags=["title"])


# Pydantic 스키마
class TitleGenerateRequest(BaseModel):
    """제목 생성 요청"""

    file_name: str = Field(..., min_length=1, description="파일명")
    file_path: str | None = Field(None, description="파일 경로 (선택)")


class TitleBatchRequest(BaseModel):
    """배치 제목 생성 요청"""

    files: list[TitleGenerateRequest] = Field(
        ..., min_length=1, max_length=100, description="파일 목록"
    )


class ParsedMetadataResponse(BaseModel):
    """파싱된 메타데이터 응답"""

    project_code: str | None
    year: int | None
    event_number: int | None
    event_name: str | None
    episode_number: int | None
    season_number: int | None
    day_number: int | None
    part_number: int | None
    game_type: str | None
    buy_in: str | None
    content_type: str | None
    extra_tags: list[str]


class TitleGenerateResponse(BaseModel):
    """제목 생성 응답"""

    display_title: str
    short_title: str
    confidence: float
    metadata: ParsedMetadataResponse


class TitleBatchResponse(BaseModel):
    """배치 제목 생성 응답"""

    results: list[TitleGenerateResponse]
    total: int


# 의존성
TitleServiceDep = Annotated[TitleGeneratorService, Depends(get_title_generator_service)]


def _to_response(generated: GeneratedTitle) -> TitleGenerateResponse:
    """GeneratedTitle을 응답 스키마로 변환"""
    meta = generated.metadata
    return TitleGenerateResponse(
        display_title=generated.display_title,
        short_title=generated.short_title,
        confidence=generated.confidence,
        metadata=ParsedMetadataResponse(
            project_code=meta.project_code.value if meta.project_code else None,
            year=meta.year,
            event_number=meta.event_number,
            event_name=meta.event_name,
            episode_number=meta.episode_number,
            season_number=meta.season_number,
            day_number=meta.day_number,
            part_number=meta.part_number,
            game_type=meta.game_type.value if meta.game_type else None,
            buy_in=str(meta.buy_in) if meta.buy_in else None,
            content_type=meta.content_type.value if meta.content_type else None,
            extra_tags=meta.extra_tags,
        ),
    )


@router.post(
    "/generate",
    response_model=TitleGenerateResponse,
    summary="제목 생성",
    description="파일명을 분석하여 Netflix 스타일의 표시 제목을 생성합니다.",
)
async def generate_title(
    request: TitleGenerateRequest,
    service: TitleServiceDep,
) -> TitleGenerateResponse:
    """
    단일 파일의 제목 생성

    - **file_name**: 분석할 파일명 (필수)
    - **file_path**: 파일 경로 (선택, 추가 컨텍스트 제공)
    """
    result = service.generate(request.file_name, request.file_path)
    return _to_response(result)


@router.post(
    "/generate-batch",
    response_model=TitleBatchResponse,
    summary="배치 제목 생성",
    description="여러 파일의 제목을 한 번에 생성합니다.",
)
async def generate_titles_batch(
    request: TitleBatchRequest,
    service: TitleServiceDep,
) -> TitleBatchResponse:
    """
    배치 제목 생성 (최대 100개)

    - **files**: 파일 목록 (file_name 필수, file_path 선택)
    """
    files = [
        {"file_name": f.file_name, "file_path": f.file_path} for f in request.files
    ]
    results = service.batch_generate(files)

    return TitleBatchResponse(
        results=[_to_response(r) for r in results],
        total=len(results),
    )


@router.post(
    "/parse",
    response_model=ParsedMetadataResponse,
    summary="메타데이터 파싱",
    description="파일명에서 메타데이터만 추출합니다.",
)
async def parse_metadata(
    request: TitleGenerateRequest,
    service: TitleServiceDep,
) -> ParsedMetadataResponse:
    """
    파일명에서 메타데이터 추출

    제목 생성 없이 메타데이터만 파싱합니다.
    """
    meta = service.parse_metadata(request.file_name)

    return ParsedMetadataResponse(
        project_code=meta.project_code.value if meta.project_code else None,
        year=meta.year,
        event_number=meta.event_number,
        event_name=meta.event_name,
        episode_number=meta.episode_number,
        season_number=meta.season_number,
        day_number=meta.day_number,
        part_number=meta.part_number,
        game_type=meta.game_type.value if meta.game_type else None,
        buy_in=str(meta.buy_in) if meta.buy_in else None,
        content_type=meta.content_type.value if meta.content_type else None,
        extra_tags=meta.extra_tags,
    )


@router.get(
    "/projects",
    response_model=list[dict[str, str]],
    summary="프로젝트 코드 목록",
    description="지원되는 포커 시리즈 프로젝트 코드 목록을 반환합니다.",
)
async def list_project_codes() -> list[dict[str, str]]:
    """지원되는 프로젝트 코드 목록"""
    from src.blocks.title_generator.models import ProjectCode

    return [
        {"code": p.value, "name": _get_project_name(p)} for p in ProjectCode
    ]


def _get_project_name(code) -> str:
    """프로젝트 코드의 전체 이름"""
    names = {
        "WSOP": "World Series of Poker",
        "HCL": "High Card Lineup / Hustler Casino Live",
        "GGMILLIONS": "GGPoker Millions",
        "GOG": "Game of Gold",
        "MPP": "Mystery Poker Players",
        "PAD": "Poker After Dark",
        "OTHER": "Other",
    }
    return names.get(code.value, code.value)
