"""
Block F: Flat Catalog 이벤트 핸들러 테스트
"""

import pytest
from uuid import uuid4

from src.orchestration.message_bus import BlockMessage, MessageBus
from src.blocks.flat_catalog.events import (
    CatalogEventHandler,
    NAS_FILE_CREATED,
    NAS_FILE_UPDATED,
    NAS_FILE_DELETED,
    NAS_SCAN_COMPLETED,
    CATALOG_ITEM_CREATED,
    CATALOG_ITEM_UPDATED,
    CATALOG_ITEM_DELETED,
)
from src.blocks.flat_catalog.service import FlatCatalogService


class TestCatalogEventHandler:
    """CatalogEventHandler 테스트"""

    @pytest.fixture
    def bus(self):
        """테스트용 MessageBus"""
        MessageBus.reset_instance()
        return MessageBus.get_instance()

    @pytest.fixture
    def service(self):
        """테스트용 서비스"""
        return FlatCatalogService()

    @pytest.fixture
    def handler(self, service):
        """테스트용 핸들러"""
        handler = CatalogEventHandler()
        handler._service = service
        return handler

    @pytest.mark.asyncio
    async def test_subscribe_all(self, bus, handler):
        """모든 이벤트 구독"""
        await handler.subscribe_all()

        assert len(bus.get_subscribers(NAS_FILE_CREATED)) == 1
        assert len(bus.get_subscribers(NAS_FILE_UPDATED)) == 1
        assert len(bus.get_subscribers(NAS_FILE_DELETED)) == 1
        assert len(bus.get_subscribers(NAS_SCAN_COMPLETED)) == 1

    @pytest.mark.asyncio
    async def test_subscribe_all_idempotent(self, bus, handler):
        """중복 구독 방지"""
        await handler.subscribe_all()
        await handler.subscribe_all()

        assert len(bus.get_subscribers(NAS_FILE_CREATED)) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_all(self, bus, handler):
        """모든 이벤트 구독 해제"""
        await handler.subscribe_all()
        await handler.unsubscribe_all()

        assert len(bus.get_subscribers(NAS_FILE_CREATED)) == 0
        assert len(bus.get_subscribers(NAS_FILE_UPDATED)) == 0

    @pytest.mark.asyncio
    async def test_handle_file_created(self, handler, service):
        """파일 생성 이벤트 처리"""
        nas_file_id = uuid4()
        message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_CREATED,
            payload={
                "id": str(nas_file_id),
                "file_path": "/nas/videos/WSOP_2024_Event1_Day1.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            },
        )

        await handler.handle_file_created(message)

        # 카탈로그 아이템이 생성되었는지 확인
        item = service.get_by_nas_file_id(nas_file_id)
        assert item is not None
        assert "WSOP" in item.display_title

    @pytest.mark.asyncio
    async def test_handle_file_created_skip_non_video(self, handler, service):
        """비디오가 아닌 파일 건너뛰기"""
        message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_CREATED,
            payload={
                "id": str(uuid4()),
                "file_path": "/nas/data/metadata.json",
                "file_name": "metadata.json",
                "file_size_bytes": 1000,
                "file_extension": ".json",
                "file_category": "METADATA",
            },
        )

        await handler.handle_file_created(message)

        assert service.count(visible_only=False) == 0

    @pytest.mark.asyncio
    async def test_handle_file_created_skip_hidden(self, handler, service):
        """숨김 파일 건너뛰기"""
        message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_CREATED,
            payload={
                "id": str(uuid4()),
                "file_path": "/nas/videos/.hidden.mp4",
                "file_name": ".hidden.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
                "is_hidden_file": True,
            },
        )

        await handler.handle_file_created(message)

        assert service.count(visible_only=False) == 0

    @pytest.mark.asyncio
    async def test_handle_file_updated(self, handler, service):
        """파일 업데이트 이벤트 처리"""
        nas_file_id = uuid4()

        # 먼저 파일 생성
        create_message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_CREATED,
            payload={
                "id": str(nas_file_id),
                "file_path": "/nas/videos/test.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            },
        )
        await handler.handle_file_created(create_message)

        # 파일 크기 업데이트
        update_message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_UPDATED,
            payload={
                "id": str(nas_file_id),
                "file_path": "/nas/videos/test.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 2000000,  # 크기 변경
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            },
        )
        await handler.handle_file_updated(update_message)

        # 업데이트 확인
        item = service.get_by_nas_file_id(nas_file_id)
        assert item is not None
        assert item.file_size_bytes == 2000000

    @pytest.mark.asyncio
    async def test_handle_file_updated_creates_if_not_exists(self, handler, service):
        """업데이트 시 아이템이 없으면 생성"""
        nas_file_id = uuid4()
        message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_UPDATED,
            payload={
                "id": str(nas_file_id),
                "file_path": "/nas/videos/test.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            },
        )

        await handler.handle_file_updated(message)

        # 아이템이 생성되었는지 확인
        item = service.get_by_nas_file_id(nas_file_id)
        assert item is not None

    @pytest.mark.asyncio
    async def test_handle_file_deleted(self, handler, service):
        """파일 삭제 이벤트 처리"""
        nas_file_id = uuid4()

        # 먼저 파일 생성
        create_message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_CREATED,
            payload={
                "id": str(nas_file_id),
                "file_path": "/nas/videos/test.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            },
        )
        await handler.handle_file_created(create_message)
        assert service.count(visible_only=False) == 1

        # 파일 삭제
        delete_message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_DELETED,
            payload={
                "id": str(nas_file_id),
            },
        )
        await handler.handle_file_deleted(delete_message)

        # 삭제 확인
        assert service.count(visible_only=False) == 0

    @pytest.mark.asyncio
    async def test_handle_file_deleted_not_exists(self, handler, service):
        """존재하지 않는 파일 삭제 (에러 없이 처리)"""
        message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_DELETED,
            payload={
                "id": str(uuid4()),
            },
        )

        # 에러 없이 처리
        await handler.handle_file_deleted(message)

    @pytest.mark.asyncio
    async def test_handle_scan_completed(self, handler, service):
        """스캔 완료 이벤트 처리"""
        files = [
            {
                "id": str(uuid4()),
                "file_path": f"/nas/videos/WSOP_2024_Event{i}_Day1.mp4",
                "file_name": f"WSOP_2024_Event{i}_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            }
            for i in range(3)
        ]

        message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_SCAN_COMPLETED,
            payload={
                "files": files,
            },
        )

        await handler.handle_scan_completed(message)

        # 모든 파일이 동기화되었는지 확인
        assert service.count(visible_only=False) == 3


class TestEventIntegration:
    """이벤트 통합 테스트"""

    @pytest.fixture
    def bus(self):
        """테스트용 MessageBus"""
        MessageBus.reset_instance()
        return MessageBus.get_instance()

    @pytest.fixture
    def service(self):
        """테스트용 서비스"""
        return FlatCatalogService()

    @pytest.fixture
    def handler(self, service):
        """테스트용 핸들러"""
        handler = CatalogEventHandler()
        handler._service = service
        return handler

    @pytest.mark.asyncio
    async def test_catalog_event_published_on_create(self, bus, handler):
        """아이템 생성 시 이벤트 발행"""
        received_events = []

        async def capture_event(msg: BlockMessage):
            received_events.append(msg)

        await bus.subscribe(CATALOG_ITEM_CREATED, capture_event)

        nas_file_id = uuid4()
        message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_CREATED,
            payload={
                "id": str(nas_file_id),
                "file_path": "/nas/videos/WSOP_2024_Event1_Day1.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            },
        )

        await handler.handle_file_created(message)

        assert len(received_events) == 1
        assert received_events[0].event_type == CATALOG_ITEM_CREATED

    @pytest.mark.asyncio
    async def test_catalog_event_published_on_update(self, bus, handler, service):
        """아이템 업데이트 시 이벤트 발행"""
        received_events = []

        async def capture_event(msg: BlockMessage):
            received_events.append(msg)

        await bus.subscribe(CATALOG_ITEM_UPDATED, capture_event)

        # 먼저 생성
        nas_file_id = uuid4()
        create_message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_CREATED,
            payload={
                "id": str(nas_file_id),
                "file_path": "/nas/videos/test.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            },
        )
        await handler.handle_file_created(create_message)

        # 업데이트
        update_message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_UPDATED,
            payload={
                "id": str(nas_file_id),
                "file_path": "/nas/videos/test.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 2000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            },
        )
        await handler.handle_file_updated(update_message)

        assert len(received_events) == 1
        assert received_events[0].event_type == CATALOG_ITEM_UPDATED

    @pytest.mark.asyncio
    async def test_catalog_event_published_on_delete(self, bus, handler):
        """아이템 삭제 시 이벤트 발행"""
        received_events = []

        async def capture_event(msg: BlockMessage):
            received_events.append(msg)

        await bus.subscribe(CATALOG_ITEM_DELETED, capture_event)

        # 먼저 생성
        nas_file_id = uuid4()
        create_message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_CREATED,
            payload={
                "id": str(nas_file_id),
                "file_path": "/nas/videos/test.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
                "file_category": "VIDEO",
            },
        )
        await handler.handle_file_created(create_message)

        # 삭제
        delete_message = BlockMessage(
            source_block="nas_scanner",
            event_type=NAS_FILE_DELETED,
            payload={
                "id": str(nas_file_id),
            },
        )
        await handler.handle_file_deleted(delete_message)

        assert len(received_events) == 1
        assert received_events[0].event_type == CATALOG_ITEM_DELETED
