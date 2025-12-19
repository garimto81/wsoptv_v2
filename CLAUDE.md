# CLAUDE.md

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
```

## Architecture
```
Orchestration: MessageBus(Pub/Sub) + BlockRegistry + Contract
L0 (No deps): auth, cache, title_generator
L1 (L0 deps): content, search, worker, flat_catalog
L2 (Full):    stream, admin
```
- 블럭 간 직접 import 금지 → MessageBus 통신만
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
