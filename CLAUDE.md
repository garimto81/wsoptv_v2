# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**WSOPTV** - 초대 기반 프라이빗 포커 VOD 스트리밍 플랫폼 (18TB+ 아카이브)

**Current Version**: 1.5.0

| Layer | Technology |
|-------|------------|
| Frontend | SvelteKit 2, TypeScript |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16 |
| Search | MeiliSearch 1.11 |
| Cache | Redis 7 (L1), Local SSD (L2) |
| Storage | NAS (SMB 3.0, `Z:\ARCHIVE`) |

## Commands

```powershell
# Backend (api/)
cd D:\AI\claude01\wsoptv_v2\api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (web/)
cd D:\AI\claude01\wsoptv_v2\web
npm install
npm run dev              # Development
npm run build            # Production build
npm run preview          # Preview build

# Database
# PostgreSQL runs as Windows Service: postgresql-x64-16

# Tests
pytest api/tests/ -v                    # All backend tests
pytest api/tests/test_auth.py -v        # Single test file
npm run test                            # Frontend tests
```

## Architecture

### 4-Tier Cache System

```
Request → [L1: Redis] → [L2: SSD Cache] → [L3: Rate Limiter] → [L4: NAS]
           (Metadata)    (Hot Content)     (20 global/3 per user)  (Origin)
```

- **L1 Redis**: 메타데이터, 세션 (TTL 5-10분)
- **L2 SSD**: 7일 내 5회+ 조회된 Hot 콘텐츠 캐싱 (500GB, LRU)
- **L3 Rate Limiter**: 전체 20, 사용자당 3 동시 스트림
- **L4 NAS**: 원본 파일 (`Z:\ARCHIVE`)

### Directory Structure (Target)

```
wsoptv_v2/
├── api/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/       # auth, contents, stream, admin
│   │   ├── services/      # cache, stream, thumbnail
│   │   ├── models/        # SQLAlchemy models
│   │   └── core/          # config, security
│   └── requirements.txt
├── web/                    # SvelteKit Frontend
│   ├── src/
│   │   ├── routes/        # +page.svelte files
│   │   └── lib/           # components, stores, api
│   └── package.json
├── cache/                  # Local SSD Cache
│   ├── hot/               # Video files
│   └── thumbnails/        # Generated images
└── scripts/               # PowerShell management
```

### Key API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/auth/register` | 회원가입 (Pending 상태) |
| `POST /api/auth/login` | 로그인 (Active만 가능) |
| `GET /api/home` | 홈페이지 Row 목록 |
| `GET /api/contents` | 콘텐츠 목록 (필터/페이지) |
| `GET /api/stream/{id}` | HTTP Range 스트리밍 |
| `PUT /api/progress/{id}` | 시청 진행률 저장 |
| `POST /api/admin/users/{id}/approve` | 사용자 승인 |

### Authentication Flow

```
회원가입 → Pending → 관리자 승인 → Active → 로그인 가능
```

## Environment Variables

```env
DATABASE_URL=postgresql://wsoptv:password@localhost:5432/wsoptv
REDIS_URL=redis://localhost:6379
MEILI_HOST=http://localhost:7700
NAS_PATH=Z:\ARCHIVE
SSD_CACHE_PATH=D:\WSOPTV\cache\hot
SSD_CACHE_MAX_GB=500
MAX_GLOBAL_STREAMS=20
MAX_USER_STREAMS=3
JWT_SECRET=your_jwt_secret
```

## Development Notes

- Windows Native 환경에서 개발 (NAS는 SMB 마운트)
- 트랜스코딩 없이 원본 파일 직접 스트리밍 (HTTP Range Request)
- FFmpeg으로 썸네일 생성 (10초 지점 프레임 추출)
- MeiliSearch로 콘텐츠 검색 (title, description, catalog_name)

## Version Management

버전 업데이트 시 아래 파일들을 **반드시 동일한 버전으로 통일**:

| 파일 | 위치 | 수정 항목 |
|------|------|----------|
| `package.json` | `frontend/package.json` | `"version": "X.Y.Z"` |
| `layout.tsx` | `frontend/src/app/layout.tsx` | `APP_VERSION = 'X.Y.Z'` |
| `prd.md` | `docs/prd.md` | `**Version**: X.Y.Z` |
| `tasks/*.md` | `tasks/` | Task 파일 헤더 |
| `CHANGELOG.md` | 루트 | 변경 내역 추가 |
| `CLAUDE.md` | 루트 | `Current Version` 업데이트 |

### 버전 규칙 (Semantic Versioning)

```
MAJOR.MINOR.PATCH
  │     │     └── 버그 수정
  │     └──────── 새 기능 (하위 호환)
  └────────────── 호환성 깨지는 변경
```

### 버전 업데이트 체크리스트

```powershell
# 버전 업데이트 시 확인 사항
1. frontend/package.json 의 version
2. frontend/src/app/layout.tsx 의 APP_VERSION
3. docs/prd.md 의 Version 헤더
4. tasks/*.md 파일의 PRD 버전 참조
5. CHANGELOG.md 에 변경 내역 추가
6. CLAUDE.md 의 Current Version
```
