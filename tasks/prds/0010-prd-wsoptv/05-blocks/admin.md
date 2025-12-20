# Admin Block PRD

**Version**: 2.0.0 | **Block ID**: admin | **Level**: L2 (Full dependencies)

---

## 1. Overview

Admin Block은 WSOPTV의 **관리자 대시보드**와 **시스템 관리 기능**을 제공합니다.

### 책임 범위

| 책임 영역 | 세부 기능 |
|----------|----------|
| **대시보드** | 시스템 상태, 통계, 모니터링 |
| **사용자 관리** | 사용자 목록, 권한 관리, 구독 관리 |
| **콘텐츠 관리** | 콘텐츠 CRUD, 메타데이터 편집 |
| **캐시 관리** | 캐시 상태 확인, 수동 워밍/클리어 |
| **시스템 설정** | 환경 설정, Rate Limit 조정 |

---

## 2. API Endpoints

### 대시보드

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/dashboard` | 대시보드 통계 |
| GET | `/api/admin/dashboard/streams` | 활성 스트림 현황 |
| GET | `/api/admin/dashboard/health` | 시스템 헬스 |

### 사용자 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/users` | 사용자 목록 |
| GET | `/api/admin/users/{id}` | 사용자 상세 |
| PATCH | `/api/admin/users/{id}` | 사용자 수정 |
| POST | `/api/admin/users/{id}/subscription` | 구독 상태 변경 |

### 콘텐츠 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/contents` | 콘텐츠 목록 |
| POST | `/api/admin/contents` | 콘텐츠 등록 |
| PATCH | `/api/admin/contents/{id}` | 콘텐츠 수정 |
| DELETE | `/api/admin/contents/{id}` | 콘텐츠 삭제 |

### 캐시 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/cache/stats` | 캐시 통계 |
| POST | `/api/admin/cache/clear` | 캐시 클리어 |
| POST | `/api/admin/cache/warm/{id}` | 수동 캐시 워밍 |

---

## 3. Dashboard Metrics

### 실시간 통계

```json
{
  "current": {
    "active_streams": 45,
    "active_users": 38,
    "cache_hit_rate": 0.87,
    "avg_response_time_ms": 45
  },
  "today": {
    "total_views": 1250,
    "unique_users": 180,
    "new_signups": 12,
    "total_watch_hours": 342.5
  },
  "system": {
    "cpu_usage": 0.35,
    "memory_usage": 0.62,
    "ssd_usage": 0.78,
    "redis_memory_mb": 1024
  }
}
```

### 차트 데이터

| 차트 | 기간 | 데이터 |
|------|------|--------|
| 시청자 추이 | 24시간 | 시간별 동시 접속자 |
| 인기 콘텐츠 | 7일 | 조회수 Top 10 |
| 구독 추이 | 30일 | 일별 신규/해지 |

---

## 4. Access Control

### 관리자 권한

| 역할 | 대시보드 | 사용자 | 콘텐츠 | 시스템 |
|------|:-------:|:------:|:------:|:------:|
| `admin` | ✅ | ✅ | ✅ | ✅ |
| `moderator` | ✅ | 읽기 | ✅ | ❌ |
| `user` | ❌ | ❌ | ❌ | ❌ |

### 인증 요구사항

```python
@router.get("/admin/dashboard")
async def get_dashboard(
    current_user: User = Depends(require_admin)
):
    ...
```

---

## 5. Content Management

### 콘텐츠 등록 플로우

```
1. 메타데이터 입력
   - 제목, 설명, 시리즈, 연도, 이벤트 유형

2. 파일 경로 지정
   - NAS/S3 경로 입력

3. 자동 처리 (Worker Block)
   - 썸네일 생성
   - 재생 시간 추출
   - 검색 인덱싱

4. 활성화
   - 공개 여부 설정
```

### Best Hands 관리

```python
# Best Hands 일괄 등록
POST /api/admin/contents/{id}/hands
Body: {
  "hands": [
    {"index": 1, "start": 45, "end": 180, "category": "all_in", "title": "AA vs KK"},
    {"index": 2, "start": 210, "end": 420, "category": "bluff", "title": "River Bluff"},
    ...
  ]
}
```

---

## 6. Monitoring

### 시스템 헬스체크

```json
{
  "status": "healthy",
  "blocks": {
    "auth": {"status": "healthy", "latency_ms": 2},
    "content": {"status": "healthy", "latency_ms": 5},
    "stream": {"status": "healthy", "latency_ms": 3},
    "cache": {"status": "healthy", "latency_ms": 1},
    "search": {"status": "healthy", "latency_ms": 8}
  },
  "dependencies": {
    "postgres": {"status": "connected", "pool_size": 10},
    "redis": {"status": "connected", "memory_mb": 1024},
    "meilisearch": {"status": "connected", "index_count": 2}
  }
}
```

### 알림 설정

| 조건 | 알림 |
|------|------|
| 블럭 장애 | 즉시 알림 |
| SSD 사용률 > 90% | 경고 |
| 에러율 > 5% | 경고 |
| 응답 시간 > 500ms | 경고 |

---

## 7. Contracts

### 의존 계약 (모든 블럭)

```python
# 전체 블럭 상태 조회
orchestration.get_block_status() -> dict[str, BlockStatus]

# Auth Block
auth.get_users() -> list[User]
auth.update_user(user_id, data) -> User

# Content Block
content.get_all_contents() -> list[Content]
content.create_content(data) -> Content

# Cache Block
cache.get_stats() -> CacheStats
cache.clear(pattern) -> None
```

---

*Parent: [04-technical.md](../04-technical.md)*
