"""
Worker Service

비동기 작업 큐 관리
- 우선순위 큐
- 작업 처리 (ThumbnailWorker, CacheWarmerWorker, NASScannerWorker)
- 재시도 메커니즘
"""

import uuid
from datetime import datetime
from typing import Dict, Optional
import heapq

from .models import Task, TaskType, TaskStatus, TaskResult
from .workers.thumbnail import ThumbnailWorker
from .workers.cache_warmer import CacheWarmerWorker
from .workers.nas_scanner import NASScannerWorker
from src.orchestration.message_bus import MessageBus, BlockMessage


class WorkerService:
    """비동기 작업 큐 서비스"""

    def __init__(self, cache_service=None):
        """
        Args:
            cache_service: CacheService 인스턴스 (Optional, Mock 테스트 용)
        """
        self._queue: list = []  # 우선순위 큐 [(priority, task), ...]
        self._tasks: Dict[str, Task] = {}  # task_id -> Task
        self._cache_service = cache_service

        # Worker 인스턴스
        self._workers = {
            TaskType.THUMBNAIL: ThumbnailWorker(cache_service),
            TaskType.CACHE_WARM: CacheWarmerWorker(cache_service),
            TaskType.NAS_SCAN: NASScannerWorker(cache_service),
        }

        # MessageBus
        self._bus = MessageBus.get_instance()

    async def enqueue(
        self,
        task_type: TaskType | str,
        payload: Dict,
        priority: int = 0
    ) -> Task:
        """
        작업 큐에 추가

        Args:
            task_type: TaskType Enum 또는 문자열
            payload: 작업 데이터
            priority: 우선순위 (높을수록 먼저 처리)

        Returns:
            Task: 생성된 작업
        """
        # 문자열을 TaskType으로 변환
        if isinstance(task_type, str):
            task_type = TaskType[task_type]

        task_id = f"{task_type.value.lower()}-{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            type=task_type,
            payload=payload,
            priority=priority,
        )

        # 우선순위 큐에 추가 (음수로 max heap 구현)
        heapq.heappush(self._queue, (-priority, task.created_at, task))
        self._tasks[task_id] = task

        return task

    async def process_next(self) -> Optional[TaskResult]:
        """
        큐에서 다음 작업 처리 (우선순위 높은 순)

        Returns:
            TaskResult: 작업 결과 (큐가 비었으면 None)
        """
        if not self._queue:
            return None

        # 우선순위가 가장 높은 작업 꺼내기
        _, _, task = heapq.heappop(self._queue)
        task.status = TaskStatus.PROCESSING
        task.updated_at = datetime.now()

        try:
            # 해당 TaskType의 Worker로 작업 처리
            worker = self._workers.get(task.type)
            if not worker:
                raise ValueError(f"Unknown task type: {task.type}")

            result = await worker.process(task)

            # 성공 처리
            if result.success:
                task.status = TaskStatus.COMPLETED
                await self._bus.publish("worker.task_completed", BlockMessage(
                    source_block="worker",
                    event_type="worker.task_completed",
                    payload={
                        "task_id": task.id,
                        "task_type": task.type.value,
                        "result": result.data,
                    }
                ))
            else:
                # 실패 처리
                task.status = TaskStatus.FAILED
                task.retries += 1
                await self._bus.publish("worker.task_failed", BlockMessage(
                    source_block="worker",
                    event_type="worker.task_failed",
                    payload={
                        "task_id": task.id,
                        "task_type": task.type.value,
                        "error": result.message,
                        "retries": task.retries,
                    }
                ))

            task.updated_at = datetime.now()
            return result

        except Exception as e:
            # 예외 처리
            task.status = TaskStatus.FAILED
            task.retries += 1
            task.updated_at = datetime.now()

            await self._bus.publish("worker.task_failed", BlockMessage(
                source_block="worker",
                event_type="worker.task_failed",
                payload={
                    "task_id": task.id,
                    "task_type": task.type.value,
                    "error": str(e),
                    "retries": task.retries,
                }
            ))

            return TaskResult(
                success=False,
                message=f"Task failed: {str(e)}",
                data={"task_id": task.id}
            )

    async def get_queue_status(self) -> Dict:
        """
        큐 상태 조회

        Returns:
            Dict: {total, pending, processing, completed, failed}
        """
        status_counts = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
        }

        for task in self._tasks.values():
            if task.status == TaskStatus.PENDING:
                status_counts["pending"] += 1
            elif task.status == TaskStatus.PROCESSING:
                status_counts["processing"] += 1
            elif task.status == TaskStatus.COMPLETED:
                status_counts["completed"] += 1
            elif task.status == TaskStatus.FAILED:
                status_counts["failed"] += 1

        return {
            "total": len(self._tasks),
            **status_counts,
        }

    async def retry_failed_tasks(self) -> int:
        """
        실패한 작업 재시도

        Returns:
            int: 재시도한 작업 수
        """
        retry_count = 0

        for task in self._tasks.values():
            if task.status == TaskStatus.FAILED and task.retries < 3:
                # 재시도 큐에 추가
                task.status = TaskStatus.PENDING
                heapq.heappush(self._queue, (-task.priority, task.created_at, task))
                retry_count += 1

        return retry_count
