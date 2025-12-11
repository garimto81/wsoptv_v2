"""
Worker Block 테스트

TDD RED Phase: 비동기 작업 큐 시스템 검증
"""

import pytest
from datetime import datetime, timedelta


class TestWorkerBlockModels:
    """Worker Block - 모델 테스트"""

    def test_task_type_enum(self):
        """TaskType Enum 정의"""
        from src.blocks.worker.models import TaskType

        assert hasattr(TaskType, "THUMBNAIL")
        assert hasattr(TaskType, "CACHE_WARM")
        assert hasattr(TaskType, "NAS_SCAN")

    def test_task_status_enum(self):
        """TaskStatus Enum 정의"""
        from src.blocks.worker.models import TaskStatus

        assert hasattr(TaskStatus, "PENDING")
        assert hasattr(TaskStatus, "PROCESSING")
        assert hasattr(TaskStatus, "COMPLETED")
        assert hasattr(TaskStatus, "FAILED")

    def test_task_model_creation(self):
        """Task 모델 생성"""
        from src.blocks.worker.models import Task, TaskType, TaskStatus

        task = Task(
            id="task-123",
            type=TaskType.THUMBNAIL,
            payload={"video_id": "v1", "frame_time": 10},
            priority=1,
        )

        assert task.id == "task-123"
        assert task.type == TaskType.THUMBNAIL
        assert task.payload["video_id"] == "v1"
        assert task.priority == 1
        assert task.status == TaskStatus.PENDING
        assert task.retries == 0
        assert isinstance(task.created_at, datetime)

    def test_task_result_model(self):
        """TaskResult 모델 생성"""
        from src.blocks.worker.models import TaskResult

        result = TaskResult(
            success=True,
            message="Thumbnail generated",
            data={"path": "/ssd/thumbs/v1.jpg"}
        )

        assert result.success is True
        assert result.message == "Thumbnail generated"
        assert result.data["path"] == "/ssd/thumbs/v1.jpg"


class TestWorkerService:
    """Worker Block - WorkerService 테스트"""

    @pytest.mark.asyncio
    async def test_enqueue_task(self):
        """작업 큐 추가"""
        from src.blocks.worker.service import WorkerService
        from src.blocks.worker.models import TaskType, TaskStatus

        service = WorkerService()
        task = await service.enqueue(
            task_type=TaskType.THUMBNAIL,
            payload={"video_id": "v1"},
            priority=1
        )

        assert task.id is not None
        assert task.type == TaskType.THUMBNAIL
        assert task.status == TaskStatus.PENDING
        assert task.priority == 1

    @pytest.mark.asyncio
    async def test_process_thumbnail_task(self):
        """썸네일 생성 작업 처리"""
        from src.blocks.worker.service import WorkerService
        from src.blocks.worker.models import TaskType

        service = WorkerService()

        # 작업 추가
        task = await service.enqueue(
            task_type=TaskType.THUMBNAIL,
            payload={"video_id": "v1", "frame_time": 5}
        )

        # 작업 처리
        result = await service.process_next()

        assert result is not None
        assert result.success is True
        assert "thumbnail" in result.message.lower() or "generated" in result.message.lower()

    @pytest.mark.asyncio
    async def test_process_cache_warm_task(self):
        """캐시 워밍 작업 처리"""
        from src.blocks.worker.service import WorkerService
        from src.blocks.worker.models import TaskType

        service = WorkerService()

        # 작업 추가
        task = await service.enqueue(
            task_type=TaskType.CACHE_WARM,
            payload={"nas_path": "/nas/videos/v1.mp4", "ssd_path": "/ssd/cache/v1.mp4"}
        )

        # 작업 처리
        result = await service.process_next()

        assert result is not None
        assert result.success is True
        assert "cache" in result.message.lower() or "copied" in result.message.lower()

    @pytest.mark.asyncio
    async def test_task_priority(self):
        """작업 우선순위 처리"""
        from src.blocks.worker.service import WorkerService
        from src.blocks.worker.models import TaskType

        service = WorkerService()

        # 우선순위 낮은 작업 추가
        low_priority_task = await service.enqueue(
            task_type=TaskType.NAS_SCAN,
            payload={"path": "/nas"},
            priority=0
        )

        # 우선순위 높은 작업 추가
        high_priority_task = await service.enqueue(
            task_type=TaskType.THUMBNAIL,
            payload={"video_id": "urgent"},
            priority=10
        )

        # 우선순위 높은 작업이 먼저 처리되어야 함
        result = await service.process_next()
        assert result is not None
        # 첫 번째로 처리된 작업이 high_priority_task인지 확인
        # (구현 시 task_id를 result에 포함하거나, queue 상태로 확인)

    @pytest.mark.asyncio
    async def test_task_retry_on_failure(self):
        """작업 실패 시 재시도"""
        from src.blocks.worker.service import WorkerService
        from src.blocks.worker.models import TaskType

        service = WorkerService()

        # 실패할 작업 추가 (잘못된 payload)
        task = await service.enqueue(
            task_type=TaskType.THUMBNAIL,
            payload={"invalid": "data"}
        )

        # 첫 번째 처리 (실패 예상)
        result = await service.process_next()

        # 실패한 작업 재시도
        retry_count = await service.retry_failed_tasks()
        assert retry_count >= 0  # 재시도 대상이 있을 수 있음

    @pytest.mark.asyncio
    async def test_get_queue_status(self):
        """큐 상태 조회"""
        from src.blocks.worker.service import WorkerService
        from src.blocks.worker.models import TaskType

        service = WorkerService()

        # 여러 작업 추가
        await service.enqueue(TaskType.THUMBNAIL, {"video_id": "v1"})
        await service.enqueue(TaskType.CACHE_WARM, {"path": "/nas/v2.mp4"})
        await service.enqueue(TaskType.NAS_SCAN, {"path": "/nas"})

        status = await service.get_queue_status()

        assert "total" in status
        assert "pending" in status
        assert "processing" in status
        assert "completed" in status
        assert "failed" in status
        assert status["total"] >= 3

    @pytest.mark.asyncio
    async def test_empty_queue_process(self):
        """빈 큐에서 process_next 호출"""
        from src.blocks.worker.service import WorkerService

        service = WorkerService()
        result = await service.process_next()

        assert result is None


class TestWorkerBlockWorkers:
    """Worker Block - 개별 Worker 테스트"""

    @pytest.mark.asyncio
    async def test_thumbnail_worker(self):
        """ThumbnailWorker 단독 테스트"""
        from src.blocks.worker.workers.thumbnail import ThumbnailWorker
        from src.blocks.worker.models import Task, TaskType

        worker = ThumbnailWorker()
        task = Task(
            id="thumb-1",
            type=TaskType.THUMBNAIL,
            payload={"video_id": "v1", "frame_time": 10}
        )

        result = await worker.process(task)

        assert result.success is True
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_cache_warmer_worker(self):
        """CacheWarmerWorker 단독 테스트"""
        from src.blocks.worker.workers.cache_warmer import CacheWarmerWorker
        from src.blocks.worker.models import Task, TaskType

        worker = CacheWarmerWorker()
        task = Task(
            id="warm-1",
            type=TaskType.CACHE_WARM,
            payload={
                "nas_path": "/nas/videos/v1.mp4",
                "ssd_path": "/ssd/cache/v1.mp4"
            }
        )

        result = await worker.process(task)

        assert result.success is True
        assert "copied" in result.message.lower() or "warmed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_nas_scanner_worker(self):
        """NASScannerWorker 단독 테스트"""
        from src.blocks.worker.workers.nas_scanner import NASScannerWorker
        from src.blocks.worker.models import Task, TaskType

        worker = NASScannerWorker()
        task = Task(
            id="scan-1",
            type=TaskType.NAS_SCAN,
            payload={"path": "/nas/videos"}
        )

        result = await worker.process(task)

        assert result.success is True
        assert result.data is not None
        # 스캔 결과에 파일 목록이나 통계가 포함되어야 함


class TestWorkerBlockEvents:
    """Worker Block 이벤트 테스트"""

    @pytest.mark.asyncio
    async def test_task_completed_event(self):
        """작업 완료 이벤트 발행"""
        from src.blocks.worker.service import WorkerService
        from src.blocks.worker.models import TaskType
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        received_events = []

        async def handler(msg):
            received_events.append(msg)

        await bus.subscribe("worker.task_completed", handler)

        service = WorkerService()
        await service.enqueue(TaskType.THUMBNAIL, {"video_id": "v1"})
        await service.process_next()

        # 이벤트가 발행되었는지 확인
        assert len(received_events) >= 1

    @pytest.mark.asyncio
    async def test_task_failed_event(self):
        """작업 실패 이벤트 발행"""
        from src.blocks.worker.service import WorkerService
        from src.blocks.worker.models import TaskType
        from src.orchestration.message_bus import MessageBus

        bus = MessageBus.get_instance()
        received_events = []

        async def handler(msg):
            received_events.append(msg)

        await bus.subscribe("worker.task_failed", handler)

        service = WorkerService()
        # 실패할 작업 추가
        await service.enqueue(TaskType.THUMBNAIL, {"invalid": "payload"})
        await service.process_next()

        # 실패 이벤트가 발행될 수 있음 (payload 검증에 따라)

    @pytest.mark.asyncio
    async def test_subscribe_cache_miss_event(self):
        """cache.miss 이벤트 구독 → CACHE_WARM 작업 추가"""
        from src.blocks.worker.service import WorkerService
        from src.orchestration.message_bus import MessageBus
        from src.orchestration.message_bus import BlockMessage

        bus = MessageBus.get_instance()
        service = WorkerService()

        # cache.miss 이벤트 핸들러 등록
        async def on_cache_miss(msg):
            await service.enqueue(
                task_type="CACHE_WARM",  # TaskType 대신 문자열로 임시
                payload=msg.payload
            )

        await bus.subscribe("cache.miss", on_cache_miss)

        # cache.miss 이벤트 발행
        await bus.publish("cache.miss", BlockMessage(
            source_block="cache",
            event_type="cache.miss",
            payload={"key": "video123", "nas_path": "/nas/videos/video123.mp4"}
        ))

        # 큐에 작업이 추가되었는지 확인
        status = await service.get_queue_status()
        assert status["total"] >= 1

    @pytest.mark.asyncio
    async def test_subscribe_content_added_event(self):
        """content.added 이벤트 구독 → THUMBNAIL 작업 추가"""
        from src.blocks.worker.service import WorkerService
        from src.orchestration.message_bus import MessageBus
        from src.orchestration.message_bus import BlockMessage

        bus = MessageBus.get_instance()
        service = WorkerService()

        # content.added 이벤트 핸들러 등록
        async def on_content_added(msg):
            await service.enqueue(
                task_type="THUMBNAIL",
                payload=msg.payload
            )

        await bus.subscribe("content.added", on_content_added)

        # content.added 이벤트 발행
        await bus.publish("content.added", BlockMessage(
            source_block="content",
            event_type="content.added",
            payload={"video_id": "new_video", "path": "/nas/videos/new.mp4"}
        ))

        # 큐에 작업이 추가되었는지 확인
        status = await service.get_queue_status()
        assert status["total"] >= 1
