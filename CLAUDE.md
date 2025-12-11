# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**WSOPTV** - 초대 기반 프라이빗 포커 VOD 스트리밍 플랫폼 (18TB+ 아카이브)

**Current Version**: 1.5.0

**GitHub**: https://github.com/garimto81/wsoptv_v2

**Last Commit**: `def1c47` (2024-12-11)

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16 (Docker: port 5435) |
| Cache | Redis 7 (L1), Local SSD (L2) |
| Storage | NAS (SMB, `10.10.100.122`) |

---

## Session Resume - 다음 세션에서 이어갈 작업

### 현재 상태 (2024-12-11)

**완료된 작업:**
- Netflix 스타일 다크 테마 UI 구현
- Auth 시스템 (로그인/회원가입)
- Catalog 페이지 (카테고리 필터: WSOP, HCL, GGMillions, GOG, MPP, PAD)
- Video Player (진행률 추적)
- Docker 설정 완료
- Git 초기 커밋 및 GitHub 푸시 완료

**해결 필요한 이슈:**

| 이슈 | 상태 | 설명 |
|------|------|------|
| CORS 에러 | **미해결** | Catalog 페이지에서 "Failed to load video catalog" 에러 |
| | | OPTIONS 요청이 400 Bad Request 반환 |
| | | 백엔드 CORS 미들웨어 수정 필요 |

### CORS 에러 해결 방법

**문제 위치**: `D:\AI\claude01\wsoptv_v2_db\backend\src\main.py` (Docker 백엔드)

**증상**:
```
OPTIONS /api/v1/nas/files/videos HTTP/1.1" 400 Bad Request
```

**해결 옵션**:
1. Docker 백엔드의 CORS 설정 수정 (`allow_origins=["*"]`, `allow_methods=["*"]`)
2. Next.js API Route로 프록시 구현 (`/api/proxy/catalog`)

### 관련 파일 및 포트

| 서비스 | 경로/포트 | 설명 |
|--------|-----------|------|
| Frontend (Dev) | `localhost:3001` (Docker) / `3000+` (Local) | Next.js |
| Backend | `localhost:8004` | FastAPI (Docker) |
| PostgreSQL | `localhost:5435` | Docker |
| API URL 설정 | `frontend/.env.local` | `NEXT_PUBLIC_CATALOG_API_URL=http://localhost:8004` |

### Docker 상태 확인

```powershell
# Docker 컨테이너 확인
docker ps

# 백엔드 로그 확인
docker logs pokervod-backend -f

# API 직접 테스트 (CORS 우회)
curl http://localhost:8004/api/v1/nas/files/videos
```

---

## Commands

```powershell
# Frontend (Next.js)
cd D:\AI\claude01\wsoptv_v2\frontend
npm install
npm run dev              # Development (localhost:3000)
npm run build            # Production build

# Backend (Docker)
cd D:\AI\claude01\wsoptv_v2_db
docker-compose up -d     # Start all services
docker-compose logs -f   # View logs

# Screenshots (Playwright)
cd D:\AI\claude01\wsoptv_v2\frontend
node screenshot.mjs      # Capture UI screenshots
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
- **L4 NAS**: 원본 파일 (SMB: `10.10.100.122`)

### Directory Structure

```
wsoptv_v2/
├── frontend/              # Next.js 14 Frontend
│   ├── src/
│   │   ├── app/          # App Router pages
│   │   ├── components/   # React components
│   │   └── lib/api/      # API clients
│   ├── .env.local        # API URL config
│   └── screenshot.mjs    # Playwright automation
├── src/                   # Block-based Backend
│   ├── blocks/           # Feature blocks (auth, content, stream, etc.)
│   └── orchestration/    # Message bus, registry
├── tests/                 # Test suites
└── docker-compose.yml     # Docker config

wsoptv_v2_db/              # Docker Backend (별도 디렉토리)
├── backend/src/main.py   # FastAPI entry
└── docker-compose.yml    # PostgreSQL, Backend, Frontend
```

### Key API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/nas/files/videos` | NAS 비디오 파일 목록 |
| `POST /api/auth/register` | 회원가입 (Pending 상태) |
| `POST /api/auth/login` | 로그인 (Active만 가능) |
| `GET /api/stream/{id}` | HTTP Range 스트리밍 |
| `PUT /api/progress/{id}` | 시청 진행률 저장 |

## Development Notes

- Windows Native 환경에서 개발
- NAS는 SMB 마운트 (`10.10.100.122`)
- 트랜스코딩 없이 원본 파일 직접 스트리밍 (HTTP Range Request)
- FFmpeg으로 썸네일 생성 (10초 지점 프레임 추출)
- 로그인 테스트: `garimto` / `1234`

## Version Management

버전 업데이트 시 아래 파일들을 **반드시 동일한 버전으로 통일**:

| 파일 | 위치 | 수정 항목 |
|------|------|----------|
| `package.json` | `frontend/package.json` | `"version": "X.Y.Z"` |
| `layout.tsx` | `frontend/src/app/layout.tsx` | `APP_VERSION = 'X.Y.Z'` |
| `prd.md` | `docs/prd.md` | `**Version**: X.Y.Z` |
| `CHANGELOG.md` | 루트 | 변경 내역 추가 |
| `CLAUDE.md` | 루트 | `Current Version` 업데이트 |

### 버전 규칙 (Semantic Versioning)

```
MAJOR.MINOR.PATCH
  │     │     └── 버그 수정
  │     └──────── 새 기능 (하위 호환)
  └────────────── 호환성 깨지는 변경
```
