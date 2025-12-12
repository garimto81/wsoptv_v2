# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**WSOPTV** - 초대 기반 프라이빗 포커 VOD 스트리밍 플랫폼 (18TB+ 아카이브)

**Current Version**: 1.6.0

**GitHub**: https://github.com/garimto81/wsoptv_v2

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.12, Block Architecture (9 Blocks) |
| Database | PostgreSQL 16 (Docker: port 5434) |
| Cache | Redis 7 (L1), Local SSD (L2) |
| Search | MeiliSearch v1.6 |
| Storage | NAS (SMB, `Z:\ARCHIVE` → `/mnt/nas/ARCHIVE`) |

---

## Commands

### Frontend (Next.js)

```powershell
cd D:\AI\claude01\wsoptv_v2\frontend
npm install
npm run dev              # Development (localhost:3000)
npm run build            # Production build
npm run lint             # ESLint
```

### Backend (Python)

```powershell
cd D:\AI\claude01\wsoptv_v2

# 테스트 실행 (단일 파일)
pytest tests/test_orchestration.py -v

# 테스트 실행 (블럭별)
pytest tests/test_blocks/test_auth_block.py -v

# 린트 & 포맷
ruff check src/ tests/
ruff format src/ tests/

# 타입 체크
mypy src/ --ignore-missing-imports
```

### Docker (Infrastructure Only)

```powershell
cd D:\AI\claude01\wsoptv_v2
docker-compose up -d     # Redis, PostgreSQL, MeiliSearch만 시작
docker-compose logs -f   # View logs
docker-compose down      # Stop all services
```

| Service | Port | Description |
|---------|------|-------------|
| redis | 6380:6379 | L1 Cache |
| postgres | 5434:5432 | Metadata Store |
| meilisearch | 7701:7700 | Search Engine |

### Backend (Local - NAS 접근 필요)

```powershell
# Docker for Windows는 네트워크 드라이브 마운트 불가 → 로컬 실행 필수
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002

# 카탈로그 동기화 (NAS → API)
python scripts/sync_nas_to_catalog.py
```

## Architecture

### Block Architecture (Backend)

9개의 독립적인 블럭으로 구성된 마이크로서비스 아키텍처:

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ MessageBus   │  │ BlockRegistry│  │ Contract     │      │
│  │ (Pub/Sub)    │  │ (Lifecycle)  │  │ (Validation) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
┌────────┴────────┬──────────┴──────────┬────────┴────────┐
│   Wave 1 (L0)   │    Wave 2 (L1)      │    Wave 3 (L2)  │
│  ┌────────────┐ │ ┌────────────────┐  │ ┌────────────┐  │
│  │    Auth    │ │ │    Content     │  │ │   Stream   │  │
│  │   Cache    │ │ │    Search      │  │ │   Admin    │  │
│  │Title Gen(G)│ │ │    Worker      │  │ └────────────┘  │
│  └────────────┘ │ │ FlatCatalog(F) │  │  (Full deps)    │
│   (No deps)     │ └────────────────┘  │                  │
└─────────────────┴─────────────────────┴──────────────────┘
```

**9개 블럭:**
| Block | Purpose | Wave |
|-------|---------|------|
| auth | 인증/권한 | L0 |
| cache | Redis/SSD 캐싱 | L0 |
| title_generator (G) | 파일명 → 표시 제목 | L0 |
| content | 콘텐츠 메타데이터 | L1 |
| search | MeiliSearch 검색 | L1 |
| worker | 썸네일/NAS 스캔 | L1 |
| flat_catalog (F) | Netflix 스타일 카탈로그 | L1 |
| stream | HTTP Range 스트리밍 | L2 |
| admin | 대시보드/사용자 관리 | L2 |

**핵심 원칙:**
- 블럭 간 직접 import 금지 → MessageBus를 통한 통신만 허용
- 각 블럭은 `provides`/`requires` Contract로 의존성 명시
- BlockRegistry가 의존성 순서 보장 (L0 → L1 → L2)

**주요 파일:**
- `src/main.py` - FastAPI 앱, 블럭 등록, 라우터 통합
- `src/orchestration/message_bus.py` - Pub/Sub 메시지 버스 (싱글톤)
- `src/orchestration/registry.py` - 블럭 등록/헬스체크/의존성 관리
- `src/orchestration/contract.py` - 버전 호환성/스키마 검증
- `src/blocks/{block}/` - 각 블럭 구현 (models, service, router)

### 4-Tier Cache System

```
Request → [L1: Redis] → [L2: SSD Cache] → [L3: Rate Limiter] → [L4: NAS]
           (Metadata)    (Hot Content)     (20 global/3 per user)  (Origin)
```

- **L1 Redis**: 메타데이터, 세션 (TTL 5-10분)
- **L2 SSD**: 7일 내 5회+ 조회된 Hot 콘텐츠 캐싱 (500GB, LRU)
- **L3 Rate Limiter**: 전체 20, 사용자당 3 동시 스트림
- **L4 NAS**: 원본 파일 (SMB: `10.10.100.122`)

### Frontend Architecture

```
frontend/src/
├── app/                   # Next.js App Router
│   ├── (auth)/            # 인증 그룹 (login, register)
│   ├── (main)/            # 메인 그룹 (browse, search, watch, history)
│   └── admin/             # 관리자 (dashboard, users, streams)
├── components/
│   ├── ui/                # shadcn/ui 컴포넌트
│   ├── layout/            # Header, Sidebar, Footer
│   ├── content/           # ContentCard, ContentGrid
│   └── player/            # VideoPlayer, PlayerControls
├── lib/
│   ├── api/               # API 클라이언트 (auth, content, stream)
│   ├── hooks/             # useAuth, useContent, usePlayer
│   └── stores/            # Zustand 스토어
└── types/                 # TypeScript 타입 정의
```

**상태 관리:**
- `Zustand` - 클라이언트 상태 (auth, player)
- `TanStack Query` - 서버 상태 캐싱/동기화

### Key API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /auth/register` | 회원가입 (Pending 상태) |
| `POST /auth/login` | 로그인 (Active만 가능) |
| `GET /content/` | 콘텐츠 카탈로그 |
| `GET /search?keyword=` | 검색 (MeiliSearch) |
| `GET /stream/{id}` | HTTP Range 스트리밍 |
| `GET /admin/dashboard` | 관리자 대시보드 |
| `GET /health` | 블럭별 헬스 체크 |
| **Block F/G (v1 API)** | |
| `GET /api/v1/catalog/` | Flat Catalog 목록 |
| `GET /api/v1/catalog/{id}` | 단일 카탈로그 아이템 |
| `GET /api/v1/catalog/category/{cat}` | 카테고리별 필터링 |
| `POST /api/v1/title/generate` | 단일 제목 생성 |
| `POST /api/v1/title/batch` | 배치 제목 생성 |
| `POST /api/v1/progress/{id}` | 시청 진행률 저장 |

---

## Development Notes

- Windows Native 환경에서 개발 (Docker for Windows)
- 트랜스코딩 없이 원본 파일 직접 스트리밍 (HTTP Range Request)
- FFmpeg으로 썸네일 생성 (10초 지점 프레임 추출)
- 테스트: `asyncio_mode = "auto"` (pytest-asyncio)
- NAS 마운트: Windows `Z:\ARCHIVE` → Docker `/mnt/nas/ARCHIVE`

### Block F/G 구현 규칙

- **Block F (flat_catalog)**: NAS 파일 → 단일 계층 CatalogItem 매핑
- **Block G (title_generator)**: 파일명 패턴 매칭 → Netflix 스타일 표시 제목
- PRD 문서: `tasks/prds/0002-prd-flat-catalog-title-generator.md`
