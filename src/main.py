"""
WSOPTV - Private Poker VOD Streaming Platform

FastAPI 메인 애플리케이션
모든 블럭 라우터 통합
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.orchestration.registry import BlockRegistry, BlockInfo, BlockStatus
from src.orchestration.message_bus import MessageBus

# Block Routers
from src.blocks.auth.router import router as auth_router
from src.blocks.content.router import router as content_router
from src.blocks.search.router import router as search_router
from src.blocks.stream.router import router as stream_router
from src.blocks.admin.router import router as admin_router
from src.blocks.flat_catalog.router import router as catalog_router
from src.blocks.title_generator.router import router as title_router


# Block Registry 초기화
registry = BlockRegistry()


def register_blocks():
    """모든 블럭을 레지스트리에 등록"""
    blocks = [
        # Wave 1: 기반 블럭 (무의존)
        BlockInfo(
            block_id="auth",
            version="1.0.0",
            provides=["auth.validate_token", "auth.get_user", "auth.check_permission"],
            requires=[],
            status=BlockStatus.HEALTHY,
            metadata={"name": "Auth Block"},
        ),
        BlockInfo(
            block_id="cache",
            version="1.0.0",
            provides=["cache.get", "cache.set", "cache.delete"],
            requires=[],
            status=BlockStatus.HEALTHY,
            metadata={"name": "Cache Block"},
        ),
        BlockInfo(
            block_id="title_generator",
            version="1.0.0",
            provides=["title.generate", "title.parse", "title.batch"],
            requires=[],
            status=BlockStatus.HEALTHY,
            metadata={"name": "Title Generator Block (G)"},
        ),

        # Wave 2: 콘텐츠 블럭
        BlockInfo(
            block_id="content",
            version="1.0.0",
            provides=["content.get_content", "content.get_metadata"],
            requires=["auth.validate_token", "cache.get"],
            status=BlockStatus.HEALTHY,
            metadata={"name": "Content Block"},
        ),
        BlockInfo(
            block_id="search",
            version="1.0.0",
            provides=["search.search", "search.index"],
            requires=["auth.validate_token"],
            status=BlockStatus.HEALTHY,
            metadata={"name": "Search Block"},
        ),
        BlockInfo(
            block_id="worker",
            version="1.0.0",
            provides=["worker.enqueue", "worker.process"],
            requires=["cache.get"],
            status=BlockStatus.HEALTHY,
            metadata={"name": "Worker Block"},
        ),
        BlockInfo(
            block_id="flat_catalog",
            version="1.0.0",
            provides=["catalog.list", "catalog.get", "catalog.search", "catalog.sync"],
            requires=["title.generate"],
            status=BlockStatus.HEALTHY,
            metadata={"name": "Flat Catalog Block (F)"},
        ),

        # Wave 3: 최종 블럭
        BlockInfo(
            block_id="stream",
            version="1.0.0",
            provides=["stream.get_url", "stream.range"],
            requires=["auth.validate_token", "cache.get", "content.get_metadata"],
            status=BlockStatus.HEALTHY,
            metadata={"name": "Stream Block"},
        ),
        BlockInfo(
            block_id="admin",
            version="1.0.0",
            provides=["admin.dashboard", "admin.users"],
            requires=["auth.validate_token", "auth.check_permission"],
            status=BlockStatus.HEALTHY,
            metadata={"name": "Admin Block"},
        ),
    ]

    for block in blocks:
        # 이미 등록된 블럭은 건너뛰기
        if block.block_id not in registry.get_all_blocks():
            if registry.can_register(block):
                registry.register(block)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # Startup
    register_blocks()

    # MessageBus 초기화
    bus = MessageBus.get_instance()

    print("=" * 50)
    print("WSOPTV Server Started")
    print("=" * 50)
    print(f"Registered Blocks: {len(registry.get_all_blocks())}")
    for block in registry.get_all_blocks():
        name = block.metadata.get("name", block.block_id)
        print(f"  - {name} v{block.version} [{block.status.value}]")
    print("=" * 50)

    yield

    # Shutdown
    print("WSOPTV Server Shutting Down...")


# OpenAPI 태그 메타데이터
tags_metadata = [
    {
        "name": "auth",
        "description": "인증 및 사용자 관리 (회원가입, 로그인, 승인)",
    },
    {
        "name": "content",
        "description": "콘텐츠 조회 및 시청 진행률 관리",
    },
    {
        "name": "search",
        "description": "콘텐츠 검색 (MeiliSearch 기반)",
    },
    {
        "name": "stream",
        "description": "비디오 스트리밍 (HTTP Range Request 지원)",
    },
    {
        "name": "admin",
        "description": "관리자 대시보드 및 사용자 관리",
    },
    {
        "name": "catalog",
        "description": "Flat Catalog - Netflix 스타일 단일 계층 카탈로그",
    },
    {
        "name": "title",
        "description": "Title Generator - 파일명 기반 표시 제목 생성",
    },
]


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="WSOPTV API",
    description="""
## Private Poker VOD Streaming Platform

WSOPTV는 프라이빗 포커 VOD 스트리밍 플랫폼입니다.

### 주요 기능

- **인증 (Auth)**: 회원가입, 로그인, 관리자 승인 시스템
- **콘텐츠 (Content)**: VOD 메타데이터 조회, 시청 진행률 저장
- **검색 (Search)**: MeiliSearch 기반 풀텍스트 검색
- **스트리밍 (Stream)**: HTTP Range Request 기반 비디오 스트리밍
- **관리 (Admin)**: 대시보드, 사용자 관리

### 아키텍처

9개의 독립적인 블럭으로 구성된 마이크로서비스 아키텍처:
- Auth, Cache, Content, Search, Worker, Stream, Admin
- **Flat Catalog (F)**: Netflix 스타일 단일 계층 카탈로그
- **Title Generator (G)**: 파일명 기반 표시 제목 생성

### API 문서

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
    """,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "WSOPTV Team",
        "email": "support@wsoptv.local",
    },
    license_info={
        "name": "Private",
        "identifier": "LicenseRef-Private",
    },
)


# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 라우터 등록
app.include_router(auth_router)
app.include_router(content_router)
app.include_router(search_router)
app.include_router(stream_router)
app.include_router(admin_router)
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(title_router, prefix="/api/v1")


@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "name": "WSOPTV API",
        "version": "1.0.0",
        "status": "healthy",
        "blocks": len(registry.get_all_blocks()),
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    blocks_status = {}
    all_healthy = True

    for block in registry.get_all_blocks():
        is_healthy = registry.is_healthy(block.block_id)
        blocks_status[block.block_id] = {
            "name": block.metadata.get("name", block.block_id),
            "version": block.version,
            "healthy": is_healthy,
        }
        if not is_healthy:
            all_healthy = False

    return {
        "status": "healthy" if all_healthy else "degraded",
        "blocks": blocks_status,
    }


@app.get("/blocks")
async def list_blocks():
    """등록된 블럭 목록 조회"""
    blocks = []
    for block in registry.get_all_blocks():
        blocks.append({
            "id": block.block_id,
            "name": block.metadata.get("name", block.block_id),
            "version": block.version,
            "status": block.status.value,
            "provides": block.provides,
            "requires": block.requires,
        })

    return {
        "total": len(blocks),
        "blocks": blocks,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
