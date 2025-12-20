"""
Block F: Flat Catalog

NAS 파일을 단일 계층 카탈로그로 변환하는 블럭.
Netflix 스타일의 간단한 카탈로그 구조를 제공.
"""

from src.blocks.flat_catalog.events import (
    CATALOG_ITEM_CREATED,
    CATALOG_ITEM_DELETED,
    CATALOG_ITEM_UPDATED,
    CATALOG_SYNC_COMPLETED,
    get_catalog_event_handler,
    setup_catalog_events,
    teardown_catalog_events,
)
from src.blocks.flat_catalog.models import CatalogItem, CatalogSyncResult, NASFileInfo
from src.blocks.flat_catalog.router import router
from src.blocks.flat_catalog.service import FlatCatalogService, get_flat_catalog_service

__all__ = [
    # Models
    "CatalogItem",
    "CatalogSyncResult",
    "NASFileInfo",
    # Service
    "FlatCatalogService",
    "get_flat_catalog_service",
    # Router
    "router",
    # Events
    "setup_catalog_events",
    "teardown_catalog_events",
    "get_catalog_event_handler",
    "CATALOG_ITEM_CREATED",
    "CATALOG_ITEM_UPDATED",
    "CATALOG_ITEM_DELETED",
    "CATALOG_SYNC_COMPLETED",
]
