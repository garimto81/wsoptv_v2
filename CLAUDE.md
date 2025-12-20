# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**WSOPTV** - 프라이빗 포커 VOD 스트리밍 (18TB+) | v1.6.0

## Stack
Frontend: Next.js 14, TypeScript, Tailwind, shadcn/ui
Backend: FastAPI, Python 3.12, 9-Block Architecture
Infra: PostgreSQL(5434), Redis(6380), MeiliSearch(7701), NAS(Z:\ARCHIVE)

## Commands
```powershell
# Frontend
cd frontend && npm run dev

# Backend
python -m uvicorn src.main:app --port 8002

# Docker (Infra)
docker-compose up -d

# Test (개별 파일 권장, 전체 120초 타임아웃)
pytest tests/test_blocks/test_auth_block.py -v
ruff check src/ && ruff format src/
mypy src/
```

## Architecture
```
Orchestration: MessageBus(Pub/Sub) + BlockRegistry + Contract
L0 (No deps): auth, cache, title_generator
L1 (L0 deps): content, search, worker, flat_catalog
L2 (Full):    stream, admin
```
- 블럭 간 직접 import 금지 → MessageBus 통신만 (`{block}.{event}` 채널)
- `src/blocks/{block}/` 구조: models, service, router

## Cache (4-Tier)
`Request → Redis(L1) → SSD(L2) → RateLimiter(L3) → NAS(L4)`

## Env
```
DATABASE_URL=postgresql://wsoptv:wsoptv@localhost:5434/wsoptv
REDIS_URL=redis://localhost:6380/0
MEILISEARCH_URL=http://localhost:7701
NAS_MOUNT_PATH=Z:\ARCHIVE
```

## Test Paths
- Unit: `tests/test_blocks/`
- Integration: `tests/test_integration/`
- E2E: `frontend/e2e/`

## Google Drive 문서 관리

### 폴더 구조
- **루트**: https://drive.google.com/drive/folders/19Sbq1_K-fJOEN2LnMEaMTE9fYjAEFoou
  - 최종 버전 문서만 배치
- **_archive/**: 이전 버전 문서 보관 (`12k3ho-PxWJ00mvKIowD_O1HCjmSkUIoV`)
- **content-strategy/**: 콘텐츠 전략 이미지 (`1NqPboT9HsAfF2XPI9Xfot-nc0wcVA2uR`)
- **wireframes/**: 와이어프레임 (`1Y1b0l4g_vLeGMm6OVqKkaZcgNvYIjnTG`)
- **architecture/**: 아키텍처 다이어그램 (`1PtlNDoJwy8CCOPr7N5QSmr1pr5NONN5W`)

### 문서 관리 원칙
| 원칙 | 설명 |
|------|------|
| **기존 문서 수정** | 신규 버전 제작 금지, 기존 문서 직접 수정 |
| **최종 버전만 루트** | 이전 버전은 `_archive/`로 이동 |
| **버전 관리 금지** | v1, v2 등 버전 번호 붙이지 않음 |

## Reference

### PRD (Product Requirements)
- Master: `tasks/prds/0010-prd-wsoptv/00-master.md`
- Features: `tasks/prds/0010-prd-wsoptv/01-features.md`
- UX: `tasks/prds/0010-prd-wsoptv/02-user-experience.md`
- Content: `tasks/prds/0010-prd-wsoptv/03-content-strategy.md`
- Screen: `tasks/prds/0010-prd-wsoptv/03-screen-design.md`
- Technical: `tasks/prds/0010-prd-wsoptv/04-technical.md`

### Block PRDs
- Auth: `tasks/prds/0010-prd-wsoptv/05-blocks/auth.md`
- Content: `tasks/prds/0010-prd-wsoptv/05-blocks/content.md`
- Stream: `tasks/prds/0010-prd-wsoptv/05-blocks/stream.md`
- Cache: `tasks/prds/0010-prd-wsoptv/05-blocks/cache.md`
- Search: `tasks/prds/0010-prd-wsoptv/05-blocks/search.md`
- Admin: `tasks/prds/0010-prd-wsoptv/05-blocks/admin.md`
- Worker: `tasks/prds/0010-prd-wsoptv/05-blocks/worker.md`
