# Worker Block PRD

**Version**: 2.0.0 | **Block ID**: worker | **Level**: L1 (Depends on content, cache)

---

## 1. Overview

Worker Block은 **백그라운드 작업**을 처리하는 비동기 작업자입니다.

### 책임 범위

| 책임 영역 | 세부 기능 |
|----------|----------|
| **썸네일 생성** | FFmpeg 기반 비디오 썸네일 추출 |
| **메타데이터 추출** | 재생 시간, 코덱 정보, 해상도 추출 |
| **캐시 워밍** | Hot Content SSD 사전 캐싱 |
| **검색 인덱싱** | MeiliSearch 인덱스 동기화 |
| **정리 작업** | 오래된 세션/로그 정리 |

---

## 2. Job Queue

### Redis Queue 구조

```python
# Queue 네이밍
queues = {
    "worker:high": ["thumbnail", "metadata"],     # 우선 처리
    "worker:normal": ["cache_warm", "index"],     # 일반 처리
    "worker:low": ["cleanup"]                     # 낮은 우선순위
}
```

### Job 스키마

```json
{
  "id": "job-uuid",
  "type": "thumbnail",
  "payload": {
    "content_id": "content-123",
    "file_path": "/path/to/video.mp4"
  },
  "created_at": "2025-12-20T10:00:00Z",
  "retry_count": 0,
  "max_retries": 3
}
```

---

## 3. Job Types

### 썸네일 생성

```python
class ThumbnailJob:
    """비디오에서 썸네일 추출"""

    async def execute(self, content_id: str, file_path: str) -> str:
        # FFmpeg으로 10% 지점 프레임 추출
        output_path = f"/cache/thumbnails/{content_id}.jpg"
        await ffmpeg.extract_frame(
            input=file_path,
            output=output_path,
            position="10%",
            size="640x360"
        )
        return output_path
```

### 메타데이터 추출

```python
class MetadataJob:
    """비디오 메타데이터 추출"""

    async def execute(self, content_id: str, file_path: str) -> dict:
        probe = await ffmpeg.probe(file_path)
        return {
            "duration_seconds": probe.duration,
            "video_codec": probe.video_codec,
            "audio_codec": probe.audio_codec,
            "resolution": f"{probe.width}x{probe.height}",
            "file_size": probe.file_size
        }
```

### 캐시 워밍

```python
class CacheWarmJob:
    """Hot Content SSD 사전 캐싱"""

    async def execute(self, content_id: str) -> None:
        file_path = await content.get_file_path(content_id)
        await cache.copy_to_ssd(file_path, content_id)
```

### 검색 인덱싱

```python
class IndexJob:
    """MeiliSearch 인덱스 업데이트"""

    async def execute(self, content_id: str) -> None:
        content = await content_service.get(content_id)
        await meilisearch.index("contents").update_documents([content])
```

---

## 4. Scheduling

### Cron Jobs

| 작업 | 스케줄 | 설명 |
|------|--------|------|
| 캐시 정리 | 매일 03:00 | 오래된 L2 캐시 삭제 |
| 세션 정리 | 매시간 | 만료된 세션 삭제 |
| 전체 재인덱싱 | 매일 04:00 | MeiliSearch 전체 동기화 |
| 통계 집계 | 매일 00:00 | 일별 통계 생성 |

### 스케줄러 설정

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# 캐시 정리
@scheduler.scheduled_job("cron", hour=3)
async def cleanup_cache():
    await cache.cleanup_old_entries()

# 세션 정리
@scheduler.scheduled_job("cron", minute=0)
async def cleanup_sessions():
    await auth.cleanup_expired_sessions()
```

---

## 5. Error Handling

### 재시도 정책

| 상황 | 재시도 | 대기 시간 |
|------|:------:|----------|
| 파일 접근 실패 | 3회 | 지수 백오프 (1, 2, 4분) |
| FFmpeg 오류 | 2회 | 고정 1분 |
| 네트워크 오류 | 5회 | 지수 백오프 |

### Dead Letter Queue

```python
# 최대 재시도 초과 시
if job.retry_count >= job.max_retries:
    await redis.rpush("worker:dead_letter", job)
    await notify_admin(f"Job failed: {job.id}")
```

---

## 6. Events

### 구독 이벤트

| 채널 | 처리 |
|------|------|
| `content.created` | 썸네일 + 메타데이터 Job 생성 |
| `content.updated` | 검색 인덱스 Job 생성 |
| `cache.warm_request` | 캐시 워밍 Job 생성 |

### 발행 이벤트

| 채널 | 페이로드 | 설명 |
|------|----------|------|
| `worker.thumbnail_ready` | `{content_id, path}` | 썸네일 생성 완료 |
| `worker.metadata_ready` | `{content_id, metadata}` | 메타데이터 추출 완료 |
| `worker.job_failed` | `{job_id, error}` | 작업 실패 |

---

## 7. Contracts

### 의존 계약

```python
# Content Block
content.get_file_path(content_id) -> str
content.update_metadata(content_id, metadata) -> None

# Cache Block
cache.copy_to_ssd(file_path, content_id) -> None
cache.cleanup_old_entries() -> int
```

### 제공 계약

```python
class WorkerContract:
    async def enqueue(job_type: str, payload: dict) -> str:
        """작업 큐에 추가"""

    async def get_job_status(job_id: str) -> JobStatus:
        """작업 상태 조회"""
```

---

## 8. Monitoring

### 메트릭

| 메트릭 | 설명 |
|--------|------|
| `worker.queue_size` | 대기 중인 작업 수 |
| `worker.processing_rate` | 초당 처리 작업 수 |
| `worker.failure_rate` | 작업 실패율 |
| `worker.avg_duration_ms` | 평균 작업 처리 시간 |

---

*Parent: [04-technical.md](../04-technical.md)*
