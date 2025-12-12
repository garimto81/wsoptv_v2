"""
Block F: Flat Catalog - 이벤트 핸들러

Block A (NAS Scanner)의 이벤트를 구독하여 카탈로그를 자동 업데이트.
"""

from __future__ import annotations

import logging
from uuid import UUID

from src.orchestration.message_bus import BlockMessage, MessageBus
from src.blocks.flat_catalog.models import NASFileInfo
from src.blocks.flat_catalog.service import get_flat_catalog_service


logger = logging.getLogger(__name__)


# 이벤트 채널 정의
NAS_FILE_CREATED = "nas.file.created"
NAS_FILE_UPDATED = "nas.file.updated"
NAS_FILE_DELETED = "nas.file.deleted"
NAS_SCAN_COMPLETED = "nas.scan.completed"

# Flat Catalog 이벤트 (다른 블럭에서 구독 가능)
CATALOG_ITEM_CREATED = "catalog.item.created"
CATALOG_ITEM_UPDATED = "catalog.item.updated"
CATALOG_ITEM_DELETED = "catalog.item.deleted"
CATALOG_SYNC_COMPLETED = "catalog.sync.completed"


class CatalogEventHandler:
    """
    카탈로그 이벤트 핸들러

    NAS 이벤트를 수신하여 카탈로그를 자동으로 업데이트.
    """

    def __init__(self) -> None:
        self._bus = MessageBus.get_instance()
        self._service = get_flat_catalog_service()
        self._subscribed = False

    async def subscribe_all(self) -> None:
        """모든 NAS 이벤트 구독"""
        if self._subscribed:
            return

        await self._bus.subscribe(NAS_FILE_CREATED, self.handle_file_created)
        await self._bus.subscribe(NAS_FILE_UPDATED, self.handle_file_updated)
        await self._bus.subscribe(NAS_FILE_DELETED, self.handle_file_deleted)
        await self._bus.subscribe(NAS_SCAN_COMPLETED, self.handle_scan_completed)

        self._subscribed = True
        logger.info("Catalog event handler subscribed to NAS events")

    async def unsubscribe_all(self) -> None:
        """모든 이벤트 구독 해제"""
        if not self._subscribed:
            return

        await self._bus.unsubscribe(NAS_FILE_CREATED, self.handle_file_created)
        await self._bus.unsubscribe(NAS_FILE_UPDATED, self.handle_file_updated)
        await self._bus.unsubscribe(NAS_FILE_DELETED, self.handle_file_deleted)
        await self._bus.unsubscribe(NAS_SCAN_COMPLETED, self.handle_scan_completed)

        self._subscribed = False
        logger.info("Catalog event handler unsubscribed from NAS events")

    async def handle_file_created(self, message: BlockMessage) -> None:
        """
        NAS 파일 생성 이벤트 처리

        새 파일이 감지되면 카탈로그 아이템 생성.
        """
        try:
            payload = message.payload

            # 비디오 파일만 처리
            if payload.get("file_category") != "VIDEO":
                return

            # 숨김 파일 건너뛰기
            if payload.get("is_hidden_file", False):
                return

            nas_file = NASFileInfo(
                id=UUID(payload["id"]),
                file_path=payload["file_path"],
                file_name=payload["file_name"],
                file_size_bytes=payload.get("file_size_bytes", 0),
                file_extension=payload.get("file_extension", ""),
                file_category=payload.get("file_category", "VIDEO"),
                is_hidden_file=payload.get("is_hidden_file", False),
            )

            # 카탈로그 아이템 생성
            item = self._service.create_from_nas_file(nas_file)

            # 카탈로그 아이템 생성 이벤트 발행
            await self._bus.publish(
                CATALOG_ITEM_CREATED,
                BlockMessage(
                    source_block="flat_catalog",
                    event_type=CATALOG_ITEM_CREATED,
                    payload=item.to_dict(),
                    correlation_id=message.correlation_id,
                ),
            )

            logger.info(f"Created catalog item: {item.display_title}")

        except Exception as e:
            logger.error(f"Error handling file created: {e}")

    async def handle_file_updated(self, message: BlockMessage) -> None:
        """
        NAS 파일 업데이트 이벤트 처리

        파일 변경 시 카탈로그 아이템 업데이트.
        """
        try:
            payload = message.payload
            nas_file_id = UUID(payload["id"])

            # 기존 아이템 조회
            item = self._service.get_by_nas_file_id(nas_file_id)
            if not item:
                # 기존 아이템이 없으면 생성
                await self.handle_file_created(message)
                return

            # 업데이트
            updated = self._service.update(
                item.id,
                file_size_bytes=payload.get("file_size_bytes", item.file_size_bytes),
            )

            if updated:
                # 업데이트 이벤트 발행
                await self._bus.publish(
                    CATALOG_ITEM_UPDATED,
                    BlockMessage(
                        source_block="flat_catalog",
                        event_type=CATALOG_ITEM_UPDATED,
                        payload=updated.to_dict(),
                        correlation_id=message.correlation_id,
                    ),
                )

                logger.info(f"Updated catalog item: {updated.display_title}")

        except Exception as e:
            logger.error(f"Error handling file updated: {e}")

    async def handle_file_deleted(self, message: BlockMessage) -> None:
        """
        NAS 파일 삭제 이벤트 처리

        파일 삭제 시 카탈로그 아이템 삭제.
        """
        try:
            payload = message.payload
            nas_file_id = UUID(payload["id"])

            # 기존 아이템 조회
            item = self._service.get_by_nas_file_id(nas_file_id)
            if not item:
                return

            # 삭제
            self._service.delete(item.id)

            # 삭제 이벤트 발행
            await self._bus.publish(
                CATALOG_ITEM_DELETED,
                BlockMessage(
                    source_block="flat_catalog",
                    event_type=CATALOG_ITEM_DELETED,
                    payload={
                        "id": str(item.id),
                        "nas_file_id": str(nas_file_id),
                        "display_title": item.display_title,
                    },
                    correlation_id=message.correlation_id,
                ),
            )

            logger.info(f"Deleted catalog item: {item.display_title}")

        except Exception as e:
            logger.error(f"Error handling file deleted: {e}")

    async def handle_scan_completed(self, message: BlockMessage) -> None:
        """
        NAS 스캔 완료 이벤트 처리

        전체 스캔 완료 시 동기화 결과 리포트.
        """
        try:
            payload = message.payload

            # 스캔된 파일 목록으로 동기화
            files_data = payload.get("files", [])
            if not files_data:
                return

            nas_files = [
                NASFileInfo(
                    id=UUID(f["id"]),
                    file_path=f["file_path"],
                    file_name=f["file_name"],
                    file_size_bytes=f.get("file_size_bytes", 0),
                    file_extension=f.get("file_extension", ""),
                    file_category=f.get("file_category", "OTHER"),
                    is_hidden_file=f.get("is_hidden_file", False),
                )
                for f in files_data
            ]

            result = self._service.sync_from_nas_files(nas_files)

            # 동기화 완료 이벤트 발행
            await self._bus.publish(
                CATALOG_SYNC_COMPLETED,
                BlockMessage(
                    source_block="flat_catalog",
                    event_type=CATALOG_SYNC_COMPLETED,
                    payload=result.to_dict(),
                    correlation_id=message.correlation_id,
                ),
            )

            logger.info(
                f"Catalog sync completed: "
                f"created={result.created}, "
                f"updated={result.updated}, "
                f"deleted={result.deleted}"
            )

        except Exception as e:
            logger.error(f"Error handling scan completed: {e}")


# 싱글톤 인스턴스
_handler: CatalogEventHandler | None = None


def get_catalog_event_handler() -> CatalogEventHandler:
    """CatalogEventHandler 싱글톤 반환"""
    global _handler
    if _handler is None:
        _handler = CatalogEventHandler()
    return _handler


async def setup_catalog_events() -> None:
    """카탈로그 이벤트 설정 (앱 시작 시 호출)"""
    handler = get_catalog_event_handler()
    await handler.subscribe_all()


async def teardown_catalog_events() -> None:
    """카탈로그 이벤트 해제 (앱 종료 시 호출)"""
    handler = get_catalog_event_handler()
    await handler.unsubscribe_all()
