# 07. Deployment

*← [06-security.md](./06-security.md) | [README](./README.md) →*

---

## 1. Development Environment

### 1.1 Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| Docker Desktop | Latest | Container runtime |
| Git | Latest | Version control |

### 1.2 Directory Structure

```
D:\AI\claude01\wsoptv_v2\
├── src/                    # Backend source
│   ├── main.py
│   ├── orchestration/
│   └── blocks/
├── tests/                  # Backend tests
├── frontend/               # Next.js frontend
│   ├── src/
│   └── package.json
├── scripts/                # Utility scripts
├── docker-compose.yml      # Infrastructure
├── pyproject.toml          # Python config
└── CLAUDE.md               # Project docs
```

---

## 2. Docker Compose Setup

### 2.1 Services Architecture

```mermaid
flowchart TB
    subgraph Docker["Docker Compose (wsoptv-v2-network)"]
        Redis["redis<br/>━━━━━━━━━━━━<br/>6380:6379<br/>L1 Cache"]
        PostgreSQL["postgres<br/>━━━━━━━━━━━━<br/>5434:5432<br/>Metadata"]
        MeiliSearch["meilisearch<br/>━━━━━━━━━━━━<br/>7701:7700<br/>Search"]
    end

    subgraph Local["Local Services"]
        Backend["uvicorn<br/>━━━━━━━━━━━━<br/>Port 8002<br/>FastAPI"]
        Frontend["next dev<br/>━━━━━━━━━━━━<br/>Port 3000<br/>Next.js"]
    end

    subgraph Storage["Network Storage"]
        NAS["NAS<br/>━━━━━━━━━━━━<br/>Z:\\ARCHIVE<br/>SMB Mount"]
    end

    Frontend --> Backend
    Backend --> Docker
    Backend --> NAS
```

### 2.2 docker-compose.yml

```yaml
services:
  # Redis - L1 Cache
  redis:
    image: redis:7-alpine
    container_name: wsoptv-v2-redis
    ports:
      - "6380:6379"
    volumes:
      - wsoptv-v2-redis-data:/data
    networks:
      - wsoptv-v2-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    command: >
      redis-server
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru

  # PostgreSQL - Metadata Store
  postgres:
    image: postgres:16-alpine
    container_name: wsoptv-v2-postgres
    ports:
      - "5434:5432"
    environment:
      - POSTGRES_USER=wsoptv
      - POSTGRES_PASSWORD=wsoptv
      - POSTGRES_DB=wsoptv
    volumes:
      - wsoptv-v2-postgres-data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:ro
    networks:
      - wsoptv-v2-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U wsoptv -d wsoptv"]
      interval: 10s
      timeout: 5s
      retries: 3

  # MeiliSearch - Search Engine
  meilisearch:
    image: getmeili/meilisearch:v1.6
    container_name: wsoptv-v2-meilisearch
    ports:
      - "7701:7700"
    environment:
      - MEILI_MASTER_KEY=masterKey
      - MEILI_ENV=development
    volumes:
      - wsoptv-v2-meilisearch-data:/meili_data
    networks:
      - wsoptv-v2-network
    restart: unless-stopped

networks:
  wsoptv-v2-network:
    driver: bridge

volumes:
  wsoptv-v2-redis-data:
  wsoptv-v2-postgres-data:
  wsoptv-v2-meilisearch-data:
```

---

## 3. Environment Configuration

### 3.1 Backend Environment Variables

```bash
# .env (Backend)
REDIS_URL=redis://localhost:6380/0
DATABASE_URL=postgresql://wsoptv:wsoptv@localhost:5434/wsoptv
MEILISEARCH_URL=http://localhost:7701
MEILISEARCH_API_KEY=masterKey

# Storage
NAS_MOUNT_PATH=Z:\ARCHIVE
SSD_CACHE_PATH=D:\cache

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Server
HOST=0.0.0.0
PORT=8002
DEBUG=true
```

### 3.2 Frontend Environment Variables

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8002
```

---

## 4. Development Commands

### 4.1 Docker Infrastructure

```bash
# Start infrastructure services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f redis
docker-compose logs -f postgres
docker-compose logs -f meilisearch

# Stop all services
docker-compose down

# Reset volumes (clean start)
docker-compose down -v
```

### 4.2 Backend Development

```bash
cd D:\AI\claude01\wsoptv_v2

# Install dependencies
pip install -e ".[dev]"

# Run development server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_blocks/test_auth_block.py -v

# Lint & format
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/ --ignore-missing-imports
```

### 4.3 Frontend Development

```bash
cd D:\AI\claude01\wsoptv_v2\frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build production
npm run build

# Lint
npm run lint
```

---

## 5. Health Checks

### 5.1 Service Health Endpoints

| Service | Health Check | Expected |
|---------|--------------|----------|
| Backend | `GET /health` | `{"status": "healthy"}` |
| Redis | `redis-cli ping` | `PONG` |
| PostgreSQL | `pg_isready` | Exit 0 |
| MeiliSearch | `GET /health` | `{"status": "available"}` |

### 5.2 Health Check Script

```bash
#!/bin/bash
# scripts/health-check.sh

echo "Checking services..."

# Backend
curl -s http://localhost:8002/health | jq .status

# Redis
docker exec wsoptv-v2-redis redis-cli ping

# PostgreSQL
docker exec wsoptv-v2-postgres pg_isready -U wsoptv -d wsoptv

# MeiliSearch
curl -s http://localhost:7701/health | jq .status
```

---

## 6. Monitoring

### 6.1 Metrics Dashboard (Admin)

```mermaid
flowchart TB
    subgraph Metrics["Admin Dashboard Metrics"]
        direction TB
        Users["👥 Users<br/>━━━━━━━━━━━━<br/>Total, Active<br/>Pending, Suspended"]
        Streams["📺 Streams<br/>━━━━━━━━━━━━<br/>Active/Limit<br/>Today total"]
        Content["🎬 Content<br/>━━━━━━━━━━━━<br/>Total items<br/>Visible/Hidden"]
        Usage["📊 Usage<br/>━━━━━━━━━━━━<br/>7-day chart<br/>Views/day"]
    end
```

### 6.2 Key Metrics to Monitor

| Category | Metric | Alert Threshold |
|----------|--------|-----------------|
| **API** | Response time P95 | > 500ms |
| **API** | Error rate | > 1% |
| **Cache** | L1 hit rate | < 80% |
| **Stream** | Active streams | > 18/20 |
| **System** | CPU usage | > 80% |
| **System** | Memory usage | > 80% |
| **Disk** | SSD cache usage | > 90% |

---

## 7. Backup Strategy

### 7.1 PostgreSQL Backup

```bash
# Manual backup
docker exec wsoptv-v2-postgres pg_dump -U wsoptv wsoptv > backup.sql

# Restore
docker exec -i wsoptv-v2-postgres psql -U wsoptv wsoptv < backup.sql
```

### 7.2 Backup Schedule (Recommended)

| Data | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| PostgreSQL | Daily | 7 days | pg_dump |
| Redis | N/A | - | Ephemeral cache |
| MeiliSearch | Weekly | 2 weeks | /dumps endpoint |
| NAS Content | N/A | - | Separate backup |

---

## 8. Troubleshooting

### 8.1 Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Redis connection | `ConnectionRefused` | Check Docker: `docker-compose ps` |
| DB connection | `Connection timeout` | Check port 5434 |
| NAS access | `FileNotFound` | Check Z: drive mount |
| Stream limit | `429 Too Many Requests` | Wait for stream slots |

### 8.2 Log Locations

| Service | Log Command |
|---------|-------------|
| Backend | Console output (uvicorn) |
| Redis | `docker-compose logs redis` |
| PostgreSQL | `docker-compose logs postgres` |
| MeiliSearch | `docker-compose logs meilisearch` |
| Frontend | Console output (next dev) |

### 8.3 Debug Commands

```bash
# Check all container status
docker-compose ps

# Check container logs
docker-compose logs -f --tail=100 redis

# Access PostgreSQL
docker exec -it wsoptv-v2-postgres psql -U wsoptv -d wsoptv

# Access Redis CLI
docker exec -it wsoptv-v2-redis redis-cli

# Check API health
curl http://localhost:8002/health | jq

# List registered blocks
curl http://localhost:8002/blocks | jq
```

---

## 9. Production Considerations

### 9.1 Not Implemented (Future)

| Feature | Priority | Notes |
|---------|----------|-------|
| HTTPS/TLS | High | nginx reverse proxy |
| Load Balancer | Medium | Multiple backend instances |
| CDN | Medium | Static asset caching |
| Container Orchestration | Low | Kubernetes/Swarm |
| CI/CD Pipeline | Medium | GitHub Actions |
| Centralized Logging | Medium | ELK/Loki |
| APM | Low | Datadog/New Relic |

### 9.2 Production Checklist

- [ ] HTTPS 설정
- [ ] CORS origin 제한
- [ ] JWT secret 환경변수 분리
- [ ] Database credentials 분리
- [ ] Rate limiting 강화
- [ ] Security headers 추가
- [ ] Backup 자동화
- [ ] Monitoring 설정
- [ ] Alerting 설정

---

## 10. Quick Start Guide

### 10.1 First Time Setup

```bash
# 1. Clone repository
git clone https://github.com/garimto81/wsoptv_v2.git
cd wsoptv_v2

# 2. Start infrastructure
docker-compose up -d

# 3. Install backend dependencies
pip install -e ".[dev]"

# 4. Start backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload

# 5. (New terminal) Install frontend dependencies
cd frontend
npm install

# 6. Start frontend
npm run dev

# 7. Open browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8002/docs
```

### 10.2 Daily Development

```bash
# Start infrastructure (if not running)
docker-compose up -d

# Start backend
python -m uvicorn src.main:app --port 8002 --reload

# Start frontend (new terminal)
cd frontend && npm run dev
```

---

*← [06-security.md](./06-security.md) | [README](./README.md) →*
