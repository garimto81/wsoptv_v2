# WSOPTV

Private Poker VOD Streaming Platform (18TB+ Archive)

## Overview

WSOPTV는 18TB 이상의 포커 VOD 아카이브를 Netflix 스타일로 스트리밍하는 프라이빗 플랫폼입니다.

**주요 특징:**
- Netflix 스타일 UI (브라우징, 검색, 플레이어)
- 4-Tier 캐싱 시스템 (Redis → SSD → RateLimiter → NAS)
- 9-Block 마이크로서비스 아키텍처
- 관리자 대시보드

## Tech Stack

### Backend
- **Framework**: FastAPI + Python 3.12
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Search**: MeiliSearch
- **Architecture**: 9-Block Orchestration Pattern

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: Zustand + TanStack Query

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose

### Infrastructure
```powershell
docker-compose up -d
```

### Backend
```powershell
python -m uvicorn src.main:app --port 8002 --reload
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

## Architecture

### 9-Block Structure
```
Orchestration Layer: MessageBus (Pub/Sub) + BlockRegistry

L0 (No dependencies):
├── auth         - 인증/인가
├── cache        - 4-Tier 캐싱
└── title_generator - 제목 생성 (Block G)

L1 (L0 dependencies):
├── content      - 콘텐츠 관리
├── search       - MeiliSearch 검색
├── worker       - 백그라운드 작업
└── flat_catalog - Netflix형 카탈로그 (Block F)

L2 (Full dependencies):
├── stream       - HTTP Range 스트리밍
└── admin        - 관리자 대시보드
```

### Cache Tiers
```
Request → Redis(L1) → SSD(L2) → RateLimiter(L3) → NAS(L4)
```

## Environment Variables

```env
DATABASE_URL=postgresql://wsoptv:wsoptv@localhost:5434/wsoptv
REDIS_URL=redis://localhost:6380/0
MEILISEARCH_URL=http://localhost:7701
NAS_MOUNT_PATH=Z:\ARCHIVE
```

## Testing

```powershell
# Lint
ruff check src/ --fix

# Unit Test (개별 파일 권장)
pytest tests/test_blocks/test_auth_block.py -v

# Full Test (120초 타임아웃 주의)
pytest tests/ -v --cov=src
```

## Documentation

| 문서 | 설명 |
|------|------|
| [Backend Blocks](docs/blocks/) | 9개 블록 기술 설계 |
| [PRD](tasks/prds/0010-prd-wsoptv/) | 제품 요구사항 문서 |
| [CLAUDE.md](CLAUDE.md) | Claude Code 가이드 |
| [CHANGELOG](CHANGELOG.md) | 변경 이력 |

## Project Structure

```
wsoptv_v2/
├── src/
│   ├── main.py              # FastAPI Entry Point
│   ├── core/                # Database
│   ├── orchestration/       # MessageBus, Registry
│   └── blocks/              # 9 Feature Blocks
├── frontend/
│   ├── src/app/             # Next.js App Router
│   ├── src/components/      # React Components
│   └── src/lib/             # Utilities, API Client
├── tests/
│   ├── test_blocks/         # Unit Tests
│   └── test_integration/    # Integration Tests
├── docs/blocks/             # Technical Documentation
└── tasks/prds/              # PRD Documents
```

## License

Private - All Rights Reserved
