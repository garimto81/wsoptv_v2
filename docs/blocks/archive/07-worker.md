# PRD: Worker Block

**Version**: 1.0.0
**Date**: 2025-12-11
**Block ID**: worker
**전담 에이전트**: worker-agent
**Status**: Draft

---

## 1. Block Overview

### 1.1 책임 범위

Worker Block은 비동기 백그라운드 작업을 처리하는 전담 블럭입니다. 메인 API 서버의 응답 속도에 영향을 주지 않으면서 시간이 오래 걸리는 작업들을 큐 기반으로 처리합니다.

**핵심 책임**:
- 썸네일 생성 (FFmpeg 프레임 추출)
- SSD 캐시 워밍 (Hot Content → SSD 복사)
- NAS 스캔 (새 파일 감지 및 DB 등록)
- 주기적 유지보수 작업 (캐시 정리, 통계 집계 등)

### 1.2 설계 원칙

| 원칙 | 설명 |
|------|------|
| **비동기성** | 모든 작업은 큐를 통해 비동기 처리 |
| **재시도 가능** | 실패 시 자동 재시도 (최대 3회) |
| **멱등성** | 동일 작업 중복 실행 시 안전 보장 |
| **모니터링** | 작업 상태 실시간 추적 가능 |

### 1.3 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Worker Block Architecture                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                      ┌─────────────────────┐                            │
│                      │   Task Queue        │                            │
│                      │   (Redis Queue)     │                            │
│                      └──────────┬──────────┘                            │
│                                 │                                        │
│         ┌───────────┬───────────┼───────────┬───────────┐              │
│         │           │           │           │           │              │
│         ▼           ▼           ▼           ▼           ▼              │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │Thumbnail │ │  Cache   │ │   NAS    │ │  Stats   │ │  Cleanup │   │
│   │  Worker  │ │  Warmer  │ │ Scanner  │ │Aggregator│ │  Worker  │   │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│        │             │             │             │             │        │
│        ▼             ▼             ▼             ▼             ▼        │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │ FFmpeg   │ │  SSD     │ │  NAS     │ │   DB     │ │  Cache   │   │
│   │          │ │  Cache   │ │  (SMB)   │ │          │ │  (Redis) │   │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Rules

### 2.1 worker-agent 전담 규칙

```markdown
## Worker Block 전담 에이전트 규칙

1. **컨텍스트 제한**
   - `api/app/blocks/worker/` 디렉토리만 수정
   - 다른 블럭 코드 읽기 금지 (계약 인터페이스만 참조)

2. **수정 가능 파일**
   - `api/app/blocks/worker/**/*`
   - `tests/blocks/worker/**/*`
   - `docs/blocks/07-worker.md`

3. **수정 불가 파일**
   - `api/app/blocks/*/` (다른 블럭)
   - `api/app/orchestration/` (오케스트레이터)

4. **통신 규칙**
   - 다른 블럭 호출 시 반드시 오케스트레이터 경유
   - 직접 import 금지 (예: `from blocks.content import ...`)
   - 계약 인터페이스 사용 (예: `orchestrator.request("content", "get_content", {...})`)

5. **작업 처리 규칙**
   - 모든 Worker는 독립적으로 실행 가능해야 함
   - Worker 간 의존성 없음
   - 실패 시 작업 큐에 재등록 (재시도 카운트 증가)
```

### 2.2 책임 경계

| 범위 | Worker Block 책임 | 다른 블럭 책임 |
|------|------------------|---------------|
| **작업 등록** | 큐 관리, 우선순위 처리 | 작업 요청 (enqueue) |
| **작업 실행** | Worker 프로세스 실행 | - |
| **결과 알림** | 이벤트 발행 | 이벤트 구독 및 처리 |
| **재시도** | 실패 감지 및 재등록 | - |

---

## 3. Worker Types

### 3.1 ThumbnailWorker

**책임**: 비디오 파일에서 썸네일 이미지 추출

```python
# api/app/blocks/worker/workers/thumbnail.py

from pathlib import Path
import asyncio
from .base import BaseWorker, TaskResult

class ThumbnailWorker(BaseWorker):
    """비디오 썸네일 생성 Worker"""

    def __init__(self, cache_dir: Path):
        super().__init__(name="thumbnail")
        self.cache_dir = cache_dir

    async def process(self, task_data: dict) -> TaskResult:
        """
        FFmpeg으로 10초 지점 프레임 추출

        Args:
            task_data: {
                "content_id": str,
                "video_path": str,  # NAS 또는 SSD 경로
                "timestamp": int     # 추출 시점 (초), 기본 10
            }

        Returns:
            TaskResult(
                success=True,
                output={"thumbnail_path": "/path/to/thumb.jpg"}
            )
        """
        content_id = task_data["content_id"]
        video_path = task_data["video_path"]
        timestamp = task_data.get("timestamp", 10)

        output_dir = self.cache_dir / content_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "poster.jpg"

        # 이미 존재하면 스킵
        if output_path.exists():
            return TaskResult(
                success=True,
                output={"thumbnail_path": str(output_path)},
                message="Thumbnail already exists"
            )

        # FFmpeg 프레임 추출
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp),           # 10초 지점
            "-i", video_path,
            "-vframes", "1",                 # 1프레임만
            "-vf", "scale=480:-1",          # 가로 480px, 세로 비율 유지
            "-q:v", "2",                     # 품질 (2 = 고품질)
            str(output_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.wait_communicate()

        if proc.returncode != 0:
            return TaskResult(
                success=False,
                error=f"FFmpeg failed: {stderr.decode()}"
            )

        return TaskResult(
            success=True,
            output={"thumbnail_path": str(output_path)}
        )
```

**설정**:
| 항목 | 값 | 설명 |
|------|-----|------|
| 추출 시점 | 10초 | 오프닝 스킵 |
| 해상도 | 480px (가로) | 카드 썸네일 |
| 품질 | q:v=2 | 고품질 JPEG |
| 저장 경로 | `{cache_dir}/{content_id}/poster.jpg` | |

### 3.2 CacheWarmer

**책임**: Hot Content를 NAS → SSD로 복사

```python
# api/app/blocks/worker/workers/cache_warmer.py

import asyncio
from pathlib import Path
from .base import BaseWorker, TaskResult

class CacheWarmer(BaseWorker):
    """SSD 캐시 워밍 Worker"""

    def __init__(self, ssd_cache_dir: Path, max_size_gb: int = 500):
        super().__init__(name="cache_warmer")
        self.ssd_cache_dir = ssd_cache_dir
        self.max_bytes = max_size_gb * 1024 ** 3

    async def process(self, task_data: dict) -> TaskResult:
        """
        NAS → SSD 저속 복사 (백그라운드)

        Args:
            task_data: {
                "content_id": str,
                "nas_path": str,      # 원본 NAS 경로
                "file_size": int      # 바이트 단위
            }

        Returns:
            TaskResult(
                success=True,
                output={"cached_path": "/path/to/ssd/content.mp4"}
            )
        """
        content_id = task_data["content_id"]
        nas_path = Path(task_data["nas_path"])
        file_size = task_data["file_size"]

        cached_path = self.ssd_cache_dir / f"{content_id}.mp4"

        # 이미 캐시됨
        if cached_path.exists():
            return TaskResult(
                success=True,
                output={"cached_path": str(cached_path)},
                message="Already cached"
            )

        # 공간 확보
        await self._ensure_space(file_size)

        # robocopy로 저속 복사 (NAS 부하 최소화)
        # /Z: 재시작 가능
        # /IPG:100: 패킷 간 100ms 갭 (저속)
        proc = await asyncio.create_subprocess_exec(
            "robocopy",
            str(nas_path.parent),
            str(self.ssd_cache_dir),
            nas_path.name,
            "/Z",        # 재시작 가능 모드
            "/IPG:100",  # 100ms 갭 (저속)
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await proc.wait()

        # robocopy 종료 코드: 0-7은 성공
        if proc.returncode > 7:
            return TaskResult(
                success=False,
                error=f"robocopy failed with code {proc.returncode}"
            )

        return TaskResult(
            success=True,
            output={"cached_path": str(cached_path)},
            message=f"Cached {file_size / 1024**3:.2f} GB"
        )

    async def _ensure_space(self, required: int):
        """LRU 방식으로 공간 확보"""
        current_size = sum(f.stat().st_size for f in self.ssd_cache_dir.glob("*.mp4"))

        while current_size + required > self.max_bytes:
            # 가장 오래된 파일 삭제 (st_atime = 마지막 접근 시간)
            oldest = min(
                self.ssd_cache_dir.glob("*.mp4"),
                key=lambda p: p.stat().st_atime
            )
            oldest_size = oldest.stat().st_size
            oldest.unlink()
            current_size -= oldest_size

            logger.info(f"Evicted {oldest.name} ({oldest_size / 1024**3:.2f} GB)")
```

**Hot Content 기준**:
| 조건 | 값 | 설명 |
|------|-----|------|
| 조회 횟수 | 7일 내 5회+ | 인기 콘텐츠 |
| 스트림 시작 | 5회차 스트림 시작 시 | 동시 접속 예상 |
| 캐시 정책 | LRU | 오래된 파일 우선 삭제 |

### 3.3 NASScanner

**책임**: NAS 폴더 스캔 및 새 파일 DB 등록

```python
# api/app/blocks/worker/workers/nas_scanner.py

from pathlib import Path
import asyncio
from datetime import datetime
from .base import BaseWorker, TaskResult

class NASScanner(BaseWorker):
    """NAS 폴더 스캔 Worker"""

    def __init__(self, nas_root: Path):
        super().__init__(name="nas_scanner")
        self.nas_root = nas_root

    async def process(self, task_data: dict) -> TaskResult:
        """
        NAS 폴더 재귀 스캔 → 새 파일 DB 등록

        Args:
            task_data: {
                "scan_path": str,     # 스캔할 경로 (기본: nas_root)
                "catalog_id": str,    # 카탈로그 ID (선택)
                "recursive": bool     # 재귀 스캔 여부 (기본: True)
            }

        Returns:
            TaskResult(
                success=True,
                output={
                    "scanned": 150,
                    "new": 12,
                    "skipped": 138
                }
            )
        """
        scan_path = Path(task_data.get("scan_path", self.nas_root))
        catalog_id = task_data.get("catalog_id")
        recursive = task_data.get("recursive", True)

        stats = {"scanned": 0, "new": 0, "skipped": 0}

        # 비디오 파일만 스캔
        pattern = "**/*.mp4" if recursive else "*.mp4"

        for video_file in scan_path.glob(pattern):
            stats["scanned"] += 1

            # DB에 이미 존재하는지 확인
            exists = await self._check_content_exists(str(video_file))
            if exists:
                stats["skipped"] += 1
                continue

            # 새 콘텐츠 등록
            await self._create_content(
                catalog_id=catalog_id or await self._infer_catalog(video_file),
                title=video_file.stem,
                nas_path=str(video_file),
                file_size=video_file.stat().st_size,
                duration=await self._get_duration(video_file)
            )

            stats["new"] += 1

        return TaskResult(
            success=True,
            output=stats,
            message=f"Scanned {stats['scanned']}, added {stats['new']}"
        )

    async def _check_content_exists(self, nas_path: str) -> bool:
        """오케스트레이터를 통해 Content Block에 확인"""
        result = await self.orchestrator.request(
            target="content",
            action="check_exists",
            payload={"nas_path": nas_path}
        )
        return result.get("exists", False)

    async def _create_content(self, **kwargs):
        """오케스트레이터를 통해 Content Block에 생성 요청"""
        await self.orchestrator.request(
            target="content",
            action="create_content",
            payload=kwargs
        )

    async def _infer_catalog(self, video_path: Path) -> str:
        """파일 경로에서 카탈로그 추론"""
        # Z:\ARCHIVE\WSOP\2024\... → catalog = "WSOP"
        parts = video_path.relative_to(self.nas_root).parts
        if len(parts) > 0:
            return parts[0]  # 첫 번째 폴더명
        return "Unknown"

    async def _get_duration(self, video_path: Path) -> int:
        """FFprobe로 비디오 길이 추출 (초 단위)"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.wait_communicate()

        if proc.returncode == 0:
            return int(float(stdout.decode().strip()))
        return 0
```

**스캔 트리거**:
| 트리거 | 주기 | 설명 |
|--------|------|------|
| 자동 스캔 | 일 1회 (새벽 2시) | 전체 NAS 스캔 |
| 수동 스캔 | 관리자 요청 | Admin Dashboard에서 실행 |
| 이벤트 스캔 | NAS 파일 변경 감지 시 | 특정 폴더만 스캔 |

### 3.4 StatsAggregator

**책임**: 통계 데이터 집계 (일일/주간/월간)

```python
# api/app/blocks/worker/workers/stats_aggregator.py

from datetime import datetime, timedelta
from .base import BaseWorker, TaskResult

class StatsAggregator(BaseWorker):
    """통계 집계 Worker"""

    def __init__(self):
        super().__init__(name="stats_aggregator")

    async def process(self, task_data: dict) -> TaskResult:
        """
        통계 데이터 집계

        Args:
            task_data: {
                "type": "daily" | "weekly" | "monthly",
                "date": "2025-12-11"  # ISO 날짜
            }
        """
        agg_type = task_data["type"]
        target_date = datetime.fromisoformat(task_data["date"])

        if agg_type == "daily":
            await self._aggregate_daily(target_date)
        elif agg_type == "weekly":
            await self._aggregate_weekly(target_date)
        elif agg_type == "monthly":
            await self._aggregate_monthly(target_date)

        return TaskResult(
            success=True,
            message=f"{agg_type} stats aggregated for {target_date.date()}"
        )

    async def _aggregate_daily(self, date: datetime):
        """일일 통계 집계"""
        # 뷰 이벤트에서 집계
        stats = await self.orchestrator.request(
            target="content",
            action="get_view_stats",
            payload={
                "start_date": date.isoformat(),
                "end_date": (date + timedelta(days=1)).isoformat()
            }
        )

        # 집계 결과 저장
        await self.orchestrator.request(
            target="admin",
            action="save_daily_stats",
            payload={
                "date": date.date().isoformat(),
                "total_views": stats["total_views"],
                "unique_users": stats["unique_users"],
                "total_watch_time": stats["total_watch_time"],
                "popular_contents": stats["top_10"]
            }
        )
```

**집계 주기**:
| 타입 | 실행 시간 | 데이터 범위 |
|------|----------|-----------|
| Daily | 매일 00:30 | 전날 00:00 ~ 23:59 |
| Weekly | 매주 월요일 01:00 | 지난주 월~일 |
| Monthly | 매월 1일 02:00 | 지난달 1일~말일 |

### 3.5 CleanupWorker

**책임**: 주기적 데이터 정리

```python
# api/app/blocks/worker/workers/cleanup.py

from datetime import datetime, timedelta
from .base import BaseWorker, TaskResult

class CleanupWorker(BaseWorker):
    """데이터 정리 Worker"""

    def __init__(self):
        super().__init__(name="cleanup")

    async def process(self, task_data: dict) -> TaskResult:
        """
        오래된 데이터 정리

        Args:
            task_data: {
                "target": "sessions" | "logs" | "temp_files"
            }
        """
        target = task_data["target"]

        if target == "sessions":
            deleted = await self._cleanup_expired_sessions()
        elif target == "logs":
            deleted = await self._cleanup_old_logs()
        elif target == "temp_files":
            deleted = await self._cleanup_temp_files()

        return TaskResult(
            success=True,
            output={"deleted_count": deleted}
        )

    async def _cleanup_expired_sessions(self) -> int:
        """만료된 세션 삭제 (24시간+)"""
        # Redis에서 만료된 세션 정리
        # (실제로는 Redis TTL이 자동 처리하지만, 추가 검증용)
        pass

    async def _cleanup_old_logs(self) -> int:
        """30일 이상 된 로그 삭제"""
        pass

    async def _cleanup_temp_files(self) -> int:
        """임시 파일 삭제"""
        pass
```

---

## 4. Task Queue

### 4.1 Redis Queue 구조

```python
# api/app/blocks/worker/queue.py

import json
import uuid
from datetime import datetime
from redis import Redis
from pydantic import BaseModel

class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class Task(BaseModel):
    id: str
    type: str                      # "thumbnail", "cache_warm", etc.
    priority: TaskPriority
    data: dict                     # Worker별 입력 데이터
    status: TaskStatus
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None

class TaskQueue:
    """Redis 기반 우선순위 작업 큐"""

    def __init__(self, redis: Redis):
        self.redis = redis

    def enqueue(self, task_type: str, data: dict, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """작업 등록"""
        task = Task(
            id=str(uuid.uuid4()),
            type=task_type,
            priority=priority,
            data=data,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )

        # 우선순위 큐에 추가 (ZADD: score = priority)
        self.redis.zadd(
            "worker:queue",
            {task.id: priority.value},
            nx=True  # 중복 방지
        )

        # Task 데이터 저장
        self.redis.set(
            f"worker:task:{task.id}",
            task.model_dump_json(),
            ex=86400 * 7  # 7일 보관
        )

        return task.id

    def dequeue(self) -> Task | None:
        """우선순위가 높은 작업부터 가져오기"""
        # ZPOPMAX: 가장 높은 score (우선순위) 가져오기
        result = self.redis.zpopmax("worker:queue")
        if not result:
            return None

        task_id, _ = result[0]
        task_json = self.redis.get(f"worker:task:{task_id}")

        if not task_json:
            return None

        task = Task.model_validate_json(task_json)
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.utcnow()

        # 상태 업데이트
        self.redis.set(f"worker:task:{task.id}", task.model_dump_json(), ex=86400 * 7)

        return task

    def complete(self, task_id: str, output: dict = None):
        """작업 완료 처리"""
        task = self._get_task(task_id)
        if not task:
            return

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        if output:
            task.data["output"] = output

        self.redis.set(f"worker:task:{task.id}", task.model_dump_json(), ex=86400 * 7)

    def fail(self, task_id: str, error: str):
        """작업 실패 처리 (재시도 또는 최종 실패)"""
        task = self._get_task(task_id)
        if not task:
            return

        task.retry_count += 1
        task.error = error

        if task.retry_count < task.max_retries:
            # 재시도
            task.status = TaskStatus.RETRYING
            self.redis.zadd("worker:queue", {task.id: task.priority.value})
        else:
            # 최종 실패
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()

        self.redis.set(f"worker:task:{task.id}", task.model_dump_json(), ex=86400 * 7)

    def get_status(self, task_id: str) -> dict:
        """작업 상태 조회"""
        task = self._get_task(task_id)
        if not task:
            return {"error": "Task not found"}

        return {
            "id": task.id,
            "type": task.type,
            "status": task.status,
            "retry_count": task.retry_count,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error
        }

    def _get_task(self, task_id: str) -> Task | None:
        task_json = self.redis.get(f"worker:task:{task_id}")
        if not task_json:
            return None
        return Task.model_validate_json(task_json)
```

### 4.2 우선순위 정책

| Priority | 값 | 사용 케이스 | 예상 대기 시간 |
|----------|-----|------------|--------------|
| URGENT | 3 | 실시간 요청 (즉시 썸네일 필요) | < 10초 |
| HIGH | 2 | 캐시 워밍 (스트림 시작 직전) | < 1분 |
| NORMAL | 1 | 일반 썸네일, 주기적 스캔 | < 10분 |
| LOW | 0 | 통계 집계, 정리 작업 | < 1시간 |

### 4.3 Worker Pool

```python
# api/app/blocks/worker/pool.py

import asyncio
from typing import Dict, Type
from .queue import TaskQueue
from .workers.base import BaseWorker

class WorkerPool:
    """Worker 프로세스 풀 관리"""

    def __init__(self, queue: TaskQueue, workers: Dict[str, Type[BaseWorker]], pool_size: int = 4):
        self.queue = queue
        self.workers = workers  # {"thumbnail": ThumbnailWorker, ...}
        self.pool_size = pool_size
        self.running = False

    async def start(self):
        """Worker Pool 시작"""
        self.running = True
        tasks = [
            asyncio.create_task(self._worker_loop(i))
            for i in range(self.pool_size)
        ]
        await asyncio.gather(*tasks)

    async def stop(self):
        """Worker Pool 정지"""
        self.running = False

    async def _worker_loop(self, worker_id: int):
        """개별 Worker 루프"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            # 큐에서 작업 가져오기
            task = self.queue.dequeue()

            if not task:
                # 큐 비어있음 → 1초 대기
                await asyncio.sleep(1)
                continue

            logger.info(f"Worker {worker_id} processing task {task.id} ({task.type})")

            # Worker 인스턴스 가져오기
            worker_class = self.workers.get(task.type)
            if not worker_class:
                self.queue.fail(task.id, f"Unknown task type: {task.type}")
                continue

            worker = worker_class()

            try:
                # 작업 실행
                result = await worker.process(task.data)

                if result.success:
                    self.queue.complete(task.id, result.output)
                    logger.info(f"Task {task.id} completed: {result.message}")
                else:
                    self.queue.fail(task.id, result.error)
                    logger.warning(f"Task {task.id} failed: {result.error}")

            except Exception as e:
                self.queue.fail(task.id, str(e))
                logger.error(f"Task {task.id} exception: {e}")

        logger.info(f"Worker {worker_id} stopped")
```

---

## 5. Provided Contracts

Worker Block이 다른 블럭에 제공하는 API:

```python
# api/app/orchestration/contracts/worker.py

class WorkerBlockAPI:
    """Worker Block 인터페이스 계약"""

    async def enqueue_thumbnail(self, content_id: str, video_path: str, priority: str = "normal") -> str:
        """
        썸네일 생성 작업 등록

        Args:
            content_id: 콘텐츠 ID
            video_path: 비디오 파일 경로
            priority: "low" | "normal" | "high" | "urgent"

        Returns:
            task_id: 작업 ID
        """
        ...

    async def enqueue_cache_warm(self, content_id: str, nas_path: str, file_size: int) -> str:
        """
        캐시 워밍 작업 등록

        Args:
            content_id: 콘텐츠 ID
            nas_path: NAS 원본 경로
            file_size: 파일 크기 (바이트)

        Returns:
            task_id: 작업 ID
        """
        ...

    async def enqueue_nas_scan(self, scan_path: str, catalog_id: str = None) -> str:
        """
        NAS 스캔 작업 등록

        Args:
            scan_path: 스캔할 경로
            catalog_id: 카탈로그 ID (선택)

        Returns:
            task_id: 작업 ID
        """
        ...

    async def get_task_status(self, task_id: str) -> dict:
        """
        작업 상태 조회

        Returns:
            {
                "id": str,
                "type": str,
                "status": "pending" | "processing" | "completed" | "failed",
                "retry_count": int,
                "created_at": str,
                "error": str | None
            }
        """
        ...

    async def get_queue_stats(self) -> dict:
        """
        큐 통계 조회

        Returns:
            {
                "pending": 42,
                "processing": 3,
                "completed_today": 156,
                "failed_today": 2
            }
        """
        ...
```

---

## 6. Required Contracts

Worker Block이 다른 블럭에 요청하는 API:

### 6.1 Content Block

```python
# content.get_content(content_id) -> Content
await orchestrator.request(
    target="content",
    action="get_content",
    payload={"content_id": "content-123"}
)

# content.check_exists(nas_path) -> bool
await orchestrator.request(
    target="content",
    action="check_exists",
    payload={"nas_path": "Z:\\ARCHIVE\\WSOP\\..."}
)

# content.create_content(...) -> Content
await orchestrator.request(
    target="content",
    action="create_content",
    payload={
        "catalog_id": "catalog-1",
        "title": "WSOP 2024 Main Event",
        "nas_path": "Z:\\ARCHIVE\\...",
        "file_size": 1024**3 * 5,
        "duration": 7200
    }
)
```

### 6.2 Cache Block

```python
# cache.is_hot_content(content_id) -> bool
await orchestrator.request(
    target="cache",
    action="is_hot_content",
    payload={"content_id": "content-123"}
)

# cache.get_cache_stats() -> dict
await orchestrator.request(
    target="cache",
    action="get_cache_stats",
    payload={}
)
```

---

## 7. Events Subscribed

Worker Block이 구독하는 이벤트:

```python
# api/app/blocks/worker/events.py

@orchestrator.subscribe("content_added")
async def on_content_added(event: BlockMessage):
    """
    새 콘텐츠 추가 시 → 썸네일 생성 작업 등록

    Event payload:
        {
            "content_id": str,
            "nas_path": str
        }
    """
    await worker_service.enqueue_thumbnail(
        content_id=event.payload["content_id"],
        video_path=event.payload["nas_path"],
        priority=TaskPriority.NORMAL
    )

@orchestrator.subscribe("stream_started")
async def on_stream_started(event: BlockMessage):
    """
    스트림 시작 5회차 → 캐시 워밍 작업 등록

    Event payload:
        {
            "content_id": str,
            "stream_count": int,
            "nas_path": str,
            "file_size": int
        }
    """
    if event.payload["stream_count"] >= 5:
        await worker_service.enqueue_cache_warm(
            content_id=event.payload["content_id"],
            nas_path=event.payload["nas_path"],
            file_size=event.payload["file_size"]
        )

@orchestrator.subscribe("schedule_trigger")
async def on_schedule_trigger(event: BlockMessage):
    """
    스케줄 트리거 → 주기적 작업 등록

    Event payload:
        {
            "trigger": "daily_scan" | "stats_aggregation" | "cleanup"
        }
    """
    trigger = event.payload["trigger"]

    if trigger == "daily_scan":
        await worker_service.enqueue_nas_scan(
            scan_path="Z:\\ARCHIVE",
            priority=TaskPriority.LOW
        )
    elif trigger == "stats_aggregation":
        await worker_service.enqueue_stats_aggregation(
            agg_type="daily",
            date=datetime.utcnow().isoformat()
        )
    elif trigger == "cleanup":
        await worker_service.enqueue_cleanup(
            target="temp_files"
        )
```

---

## 8. Events Published

Worker Block이 발행하는 이벤트:

```python
@router.on_task_completed("thumbnail")
async def publish_thumbnail_generated(task: Task):
    """썸네일 생성 완료 이벤트"""
    await orchestrator.publish(
        event="thumbnail_generated",
        payload={
            "content_id": task.data["content_id"],
            "thumbnail_path": task.data["output"]["thumbnail_path"]
        }
    )

@router.on_task_completed("cache_warm")
async def publish_cache_warmed(task: Task):
    """캐시 워밍 완료 이벤트"""
    await orchestrator.publish(
        event="cache_warmed",
        payload={
            "content_id": task.data["content_id"],
            "cached_path": task.data["output"]["cached_path"]
        }
    )

@router.on_task_completed("nas_scan")
async def publish_nas_scan_completed(task: Task):
    """NAS 스캔 완료 이벤트"""
    await orchestrator.publish(
        event="nas_scan_completed",
        payload={
            "scanned": task.data["output"]["scanned"],
            "new": task.data["output"]["new"],
            "skipped": task.data["output"]["skipped"]
        }
    )
```

**이벤트 목록**:

| Event | Trigger | Payload | 구독 블럭 |
|-------|---------|---------|----------|
| `thumbnail_generated` | 썸네일 생성 완료 | `{content_id, thumbnail_path}` | Content, Admin |
| `cache_warmed` | 캐시 워밍 완료 | `{content_id, cached_path}` | Cache, Admin |
| `nas_scan_completed` | NAS 스캔 완료 | `{scanned, new, skipped}` | Admin |
| `task_failed` | 작업 최종 실패 | `{task_id, type, error}` | Admin |

---

## 9. FFmpeg Thumbnail Generation

### 9.1 FFmpeg 명령어 상세

```bash
ffmpeg -y \
  -ss 10 \                        # 10초 지점으로 이동 (빠른 seek)
  -i /path/to/video.mp4 \         # 입력 파일
  -vframes 1 \                    # 1프레임만 추출
  -vf "scale=480:-1" \            # 가로 480px, 세로 비율 유지
  -q:v 2 \                        # JPEG 품질 (1=최고, 31=최저)
  /path/to/output.jpg             # 출력 파일
```

**옵션 설명**:

| 옵션 | 값 | 설명 |
|------|-----|------|
| `-ss 10` | 10초 | 시작 시점 (오프닝 스킵) |
| `-vframes 1` | 1 | 프레임 수 제한 |
| `-vf scale=480:-1` | 480px | 가로 고정, 세로 자동 (비율 유지) |
| `-q:v 2` | 2 | JPEG 품질 (2 = 고품질, 파일 크기 ~100KB) |
| `-y` | - | 기존 파일 덮어쓰기 |

### 9.2 대체 추출 시점

첫 프레임이 검은 화면인 경우 대비:

```python
async def extract_thumbnail_with_fallback(video_path: str, output_path: str):
    """여러 시점 시도 (10초 → 30초 → 60초)"""
    for timestamp in [10, 30, 60]:
        try:
            await extract_frame(video_path, output_path, timestamp)

            # 검은 화면 감지 (평균 밝기 < 10)
            if not await is_black_frame(output_path):
                return

        except Exception:
            continue

    # 모두 실패 시 기본 썸네일
    shutil.copy("default_poster.jpg", output_path)

async def is_black_frame(image_path: str) -> bool:
    """평균 밝기로 검은 화면 감지"""
    from PIL import Image
    import numpy as np

    img = Image.open(image_path).convert('L')  # 그레이스케일
    avg_brightness = np.array(img).mean()
    return avg_brightness < 10
```

### 9.3 성능 최적화

| 항목 | 설정 | 효과 |
|------|------|------|
| 입력 Seek | `-ss` before `-i` | 디코딩 최소화 (10배 빠름) |
| 스레드 | `-threads 1` | CPU 부하 제한 |
| 동시 실행 | Worker Pool 크기 4 | 4개 동시 처리 |

---

## 10. Directory Structure

```
api/app/blocks/worker/
├── __init__.py
├── router.py                   # FastAPI 라우터
├── service.py                  # Worker 서비스
├── queue.py                    # Task Queue 관리
├── pool.py                     # Worker Pool
├── events.py                   # 이벤트 구독/발행
│
├── workers/                    # Worker 구현체
│   ├── __init__.py
│   ├── base.py                # BaseWorker 추상 클래스
│   ├── thumbnail.py           # ThumbnailWorker
│   ├── cache_warmer.py        # CacheWarmer
│   ├── nas_scanner.py         # NASScanner
│   ├── stats_aggregator.py   # StatsAggregator
│   └── cleanup.py             # CleanupWorker
│
├── models.py                   # Pydantic 모델
└── config.py                   # Worker 설정

tests/blocks/worker/
├── __init__.py
├── conftest.py                # Fixtures
├── test_queue.py              # 큐 테스트
├── test_pool.py               # Worker Pool 테스트
├── test_thumbnail_worker.py   # ThumbnailWorker 테스트
├── test_cache_warmer.py       # CacheWarmer 테스트
└── test_nas_scanner.py        # NASScanner 테스트

docs/blocks/
└── 07-worker.md               # 이 문서
```

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# tests/blocks/worker/test_thumbnail_worker.py

import pytest
from pathlib import Path
from app.blocks.worker.workers.thumbnail import ThumbnailWorker

@pytest.fixture
def sample_video(tmp_path):
    """10초 테스트 비디오 생성"""
    video_path = tmp_path / "test.mp4"
    # FFmpeg로 10초 더미 비디오 생성
    # ...
    return video_path

@pytest.fixture
def cache_dir(tmp_path):
    return tmp_path / "cache"

async def test_thumbnail_generation_success(sample_video, cache_dir):
    """썸네일 생성 성공"""
    worker = ThumbnailWorker(cache_dir)

    result = await worker.process({
        "content_id": "test-content",
        "video_path": str(sample_video),
        "timestamp": 5
    })

    assert result.success
    assert "thumbnail_path" in result.output
    assert Path(result.output["thumbnail_path"]).exists()

async def test_thumbnail_already_exists(sample_video, cache_dir):
    """이미 존재하는 썸네일 → 스킵"""
    worker = ThumbnailWorker(cache_dir)

    # 첫 번째 실행
    result1 = await worker.process({
        "content_id": "test-content",
        "video_path": str(sample_video)
    })

    # 두 번째 실행 → 스킵
    result2 = await worker.process({
        "content_id": "test-content",
        "video_path": str(sample_video)
    })

    assert result2.success
    assert "already exists" in result2.message.lower()

async def test_thumbnail_invalid_video(cache_dir):
    """잘못된 비디오 파일 → 실패"""
    worker = ThumbnailWorker(cache_dir)

    result = await worker.process({
        "content_id": "test-content",
        "video_path": "/nonexistent.mp4"
    })

    assert not result.success
    assert result.error is not None
```

### 11.2 Queue Tests

```python
# tests/blocks/worker/test_queue.py

import pytest
from app.blocks.worker.queue import TaskQueue, TaskPriority, TaskStatus

@pytest.fixture
def queue(redis_client):
    return TaskQueue(redis_client)

def test_enqueue_dequeue(queue):
    """작업 등록 및 가져오기"""
    task_id = queue.enqueue(
        task_type="thumbnail",
        data={"content_id": "test"},
        priority=TaskPriority.NORMAL
    )

    task = queue.dequeue()

    assert task is not None
    assert task.id == task_id
    assert task.type == "thumbnail"
    assert task.status == TaskStatus.PROCESSING

def test_priority_order(queue):
    """우선순위 순서 보장"""
    # LOW → NORMAL → HIGH 순서로 등록
    id_low = queue.enqueue("test", {}, TaskPriority.LOW)
    id_normal = queue.enqueue("test", {}, TaskPriority.NORMAL)
    id_high = queue.enqueue("test", {}, TaskPriority.HIGH)

    # 가져올 때는 HIGH → NORMAL → LOW 순서
    assert queue.dequeue().id == id_high
    assert queue.dequeue().id == id_normal
    assert queue.dequeue().id == id_low

def test_retry_on_failure(queue):
    """실패 시 재시도"""
    task_id = queue.enqueue("test", {}, max_retries=3)
    task = queue.dequeue()

    # 첫 번째 실패 → 재시도
    queue.fail(task.id, "Error 1")
    task = queue.dequeue()
    assert task.retry_count == 1
    assert task.status == TaskStatus.RETRYING

    # 두 번째 실패 → 재시도
    queue.fail(task.id, "Error 2")
    task = queue.dequeue()
    assert task.retry_count == 2

    # 세 번째 실패 → 최종 실패
    queue.fail(task.id, "Error 3")
    task_status = queue.get_status(task.id)
    assert task_status["status"] == TaskStatus.FAILED
```

### 11.3 Integration Tests

```python
# tests/blocks/worker/test_integration.py

import pytest
from app.orchestration.orchestrator import Orchestrator

@pytest.fixture
async def orchestrator():
    """오케스트레이터 Mock"""
    # ...
    pass

async def test_content_added_triggers_thumbnail(orchestrator):
    """content_added 이벤트 → 썸네일 작업 등록"""
    # Content Block에서 이벤트 발행
    await orchestrator.publish(
        event="content_added",
        payload={
            "content_id": "content-123",
            "nas_path": "/path/to/video.mp4"
        }
    )

    # Worker Block이 작업 등록했는지 확인
    queue_stats = await orchestrator.request(
        target="worker",
        action="get_queue_stats",
        payload={}
    )

    assert queue_stats["pending"] >= 1

async def test_thumbnail_completed_event(orchestrator, worker_pool):
    """썸네일 완료 → 이벤트 발행"""
    events_received = []

    @orchestrator.subscribe("thumbnail_generated")
    async def on_thumbnail(event):
        events_received.append(event)

    # 썸네일 작업 등록 및 실행
    task_id = await orchestrator.request(
        target="worker",
        action="enqueue_thumbnail",
        payload={
            "content_id": "content-123",
            "video_path": "/test.mp4"
        }
    )

    # Worker 처리 대기
    await asyncio.sleep(2)

    # 이벤트 수신 확인
    assert len(events_received) == 1
    assert events_received[0].payload["content_id"] == "content-123"
```

### 11.4 테스트 커버리지 목표

| 영역 | 목표 | 우선순위 |
|------|------|---------|
| Queue 로직 | 95%+ | P0 |
| Worker 구현 | 85%+ | P0 |
| 이벤트 처리 | 80%+ | P1 |
| 에러 핸들링 | 90%+ | P0 |

---

## 12. Performance & Scalability

### 12.1 성능 목표

| Metric | Target | Measurement |
|--------|--------|-------------|
| 썸네일 생성 시간 | < 3초 (480p) | Worker 로그 |
| 캐시 워밍 처리량 | 100MB/s | robocopy 로그 |
| 큐 처리 지연 | < 5초 (NORMAL) | enqueue → dequeue 시간 |
| Worker Pool 활용률 | > 70% | 활성 Worker / 전체 |

### 12.2 확장성

```python
# Worker Pool 크기 동적 조정
class AutoScalingWorkerPool:
    def __init__(self, min_workers=2, max_workers=8):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.current_workers = min_workers

    async def scale_up_if_needed(self):
        """큐 크기에 따라 Worker 증가"""
        queue_size = await self.queue.size()

        if queue_size > 20 and self.current_workers < self.max_workers:
            await self.add_worker()
            self.current_workers += 1
            logger.info(f"Scaled up to {self.current_workers} workers")

    async def scale_down_if_needed(self):
        """유휴 시 Worker 감소"""
        queue_size = await self.queue.size()

        if queue_size < 5 and self.current_workers > self.min_workers:
            await self.remove_worker()
            self.current_workers -= 1
            logger.info(f"Scaled down to {self.current_workers} workers")
```

### 12.3 병목 지점 및 대응

| 병목 | 원인 | 대응 |
|------|------|------|
| FFmpeg CPU 사용률 | 고해상도 비디오 | 스레드 제한, Worker 분산 |
| robocopy 느림 | NAS 대역폭 | IPG 조정, 야간 실행 |
| Redis 메모리 | Task 데이터 축적 | TTL 7일, 완료 작업 정리 |

---

## 13. Monitoring & Alerts

### 13.1 메트릭

```python
# 메트릭 수집
class WorkerMetrics:
    async def collect(self):
        return {
            "queue_size": await redis.zcard("worker:queue"),
            "processing_count": await redis.scard("worker:processing"),
            "completed_today": await self._count_completed_today(),
            "failed_today": await self._count_failed_today(),
            "avg_processing_time_sec": await self._avg_processing_time(),
            "worker_pool_size": self.pool.current_workers,
            "worker_utilization_pct": await self._calculate_utilization()
        }
```

### 13.2 알림 조건

| 조건 | 임계값 | 알림 |
|------|--------|------|
| 큐 크기 | > 100 | 경고 |
| 실패율 | > 10% | 즉시 알림 |
| 평균 처리 시간 | > 10초 | 경고 |
| Worker 다운 | 1개 이상 | 즉시 알림 |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-11 | Claude Code | Initial draft |
