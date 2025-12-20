"""
Block F: Flat Catalog - 서비스

NAS 파일을 단일 계층 카탈로그로 변환하는 핵심 서비스.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from uuid import UUID

from src.blocks.flat_catalog.models import (
    CatalogItem,
    CatalogSyncResult,
    NASFileInfo,
)
from src.blocks.title_generator.service import (
    TitleGeneratorService,
    get_title_generator_service,
)


class FlatCatalogService:
    """
    Flat Catalog 핵심 서비스

    NAS 파일을 단일 계층 카탈로그로 변환하고 관리.
    Block F의 모든 기능을 제공.
    """

    def __init__(
        self,
        title_generator: TitleGeneratorService | None = None,
    ) -> None:
        """
        서비스 초기화

        Args:
            title_generator: Title Generator 서비스 (None이면 기본 서비스 사용)
        """
        self._title_generator = title_generator or get_title_generator_service()
        self._items: dict[UUID, CatalogItem] = {}  # 인메모리 저장소 (추후 DB 연동)

    def create_from_nas_file(
        self,
        nas_file: NASFileInfo,
    ) -> CatalogItem:
        """
        NAS 파일에서 카탈로그 아이템 생성

        Args:
            nas_file: NAS 파일 정보

        Returns:
            CatalogItem: 생성된 카탈로그 아이템
        """
        # 제목 생성
        generated = self._title_generator.generate(
            nas_file.file_name,
            nas_file.file_path,
        )

        # 프로젝트 코드 추출
        project_code = "OTHER"
        if generated.metadata.project_code:
            project_code = generated.metadata.project_code.value

        # 카탈로그 아이템 생성
        item = CatalogItem(
            nas_file_id=nas_file.id,
            display_title=generated.display_title,
            short_title=generated.short_title,
            project_code=project_code,
            year=generated.metadata.year,
            file_path=nas_file.file_path,
            file_name=nas_file.file_name,
            file_size_bytes=nas_file.file_size_bytes,
            file_extension=nas_file.file_extension,
            confidence=generated.confidence,
        )

        # 카테고리 태그 추가
        if generated.metadata.game_type:
            item.category_tags.append(generated.metadata.game_type.value)
        if generated.metadata.content_type:
            item.category_tags.append(generated.metadata.content_type.value)

        # 저장
        self._items[item.id] = item

        return item

    def get_by_id(self, item_id: UUID) -> CatalogItem | None:
        """ID로 카탈로그 아이템 조회"""
        return self._items.get(item_id)

    def get_by_nas_file_id(self, nas_file_id: UUID) -> CatalogItem | None:
        """NAS 파일 ID로 카탈로그 아이템 조회"""
        for item in self._items.values():
            if item.nas_file_id == nas_file_id:
                return item
        return None

    def get_all(
        self,
        project_code: str | None = None,
        year: int | None = None,
        visible_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CatalogItem]:
        """
        카탈로그 조회 (필터링 지원)

        Args:
            project_code: 프로젝트 코드 필터
            year: 연도 필터
            visible_only: 표시 가능한 항목만
            skip: 스킵할 개수
            limit: 반환할 최대 개수

        Returns:
            CatalogItem 리스트
        """
        items = list(self._items.values())

        # 필터링
        if visible_only:
            items = [i for i in items if i.is_visible]

        if project_code:
            items = [i for i in items if i.project_code == project_code]

        if year:
            items = [i for i in items if i.year == year]

        # 정렬 (최신순)
        items.sort(key=lambda x: x.created_at, reverse=True)

        # 페이지네이션
        return items[skip : skip + limit]

    def search(
        self,
        query: str,
        limit: int = 50,
    ) -> list[CatalogItem]:
        """
        제목/태그 검색

        Args:
            query: 검색어
            limit: 반환할 최대 개수

        Returns:
            CatalogItem 리스트
        """
        query_lower = query.lower()
        results = []

        for item in self._items.values():
            if not item.is_visible:
                continue

            # 제목 검색
            if query_lower in item.display_title.lower():
                results.append(item)
                continue

            # 태그 검색
            for tag in item.category_tags:
                if query_lower in tag.lower():
                    results.append(item)
                    break

        # 신뢰도 기준 정렬
        results.sort(key=lambda x: x.confidence, reverse=True)

        return results[:limit]

    def update(
        self,
        item_id: UUID,
        **kwargs,
    ) -> CatalogItem | None:
        """
        카탈로그 아이템 업데이트

        Args:
            item_id: 아이템 ID
            **kwargs: 업데이트할 필드

        Returns:
            업데이트된 CatalogItem 또는 None
        """
        item = self._items.get(item_id)
        if not item:
            return None

        # 필드 업데이트
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)

        item.update_timestamp()
        return item

    def delete(self, item_id: UUID) -> bool:
        """
        카탈로그 아이템 삭제

        Args:
            item_id: 아이템 ID

        Returns:
            삭제 성공 여부
        """
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False

    def set_visibility(self, item_id: UUID, visible: bool) -> CatalogItem | None:
        """가시성 설정"""
        return self.update(item_id, is_visible=visible)

    def count(
        self,
        project_code: str | None = None,
        visible_only: bool = True,
    ) -> int:
        """
        카탈로그 아이템 개수

        Args:
            project_code: 프로젝트 코드 필터
            visible_only: 표시 가능한 항목만

        Returns:
            개수
        """
        items = list(self._items.values())

        if visible_only:
            items = [i for i in items if i.is_visible]

        if project_code:
            items = [i for i in items if i.project_code == project_code]

        return len(items)

    def get_projects(self) -> list[dict[str, int]]:
        """
        프로젝트별 통계

        Returns:
            [{"code": "WSOP", "count": 100}, ...]
        """
        project_counts: dict[str, int] = {}

        for item in self._items.values():
            if not item.is_visible:
                continue
            project_counts[item.project_code] = project_counts.get(item.project_code, 0) + 1

        return [
            {"code": code, "count": count}
            for code, count in sorted(project_counts.items(), key=lambda x: -x[1])
        ]

    def get_years(self, project_code: str | None = None) -> list[int]:
        """
        연도 목록

        Args:
            project_code: 프로젝트 코드 필터

        Returns:
            연도 리스트 (내림차순)
        """
        years = set()

        for item in self._items.values():
            if not item.is_visible:
                continue
            if project_code and item.project_code != project_code:
                continue
            if item.year:
                years.add(item.year)

        return sorted(years, reverse=True)

    def sync_from_nas_files(
        self,
        nas_files: list[NASFileInfo],
        on_progress: Callable[[int, int], None] | None = None,
    ) -> CatalogSyncResult:
        """
        NAS 파일 목록에서 카탈로그 동기화

        Args:
            nas_files: NAS 파일 목록
            on_progress: 진행 상황 콜백 (current, total)

        Returns:
            CatalogSyncResult: 동기화 결과
        """
        start_time = time.time()
        result = CatalogSyncResult()
        total = len(nas_files)

        # NAS 파일 ID 집합
        new_nas_ids = {f.id for f in nas_files}

        for idx, nas_file in enumerate(nas_files):
            try:
                # 비디오 파일만 처리
                if nas_file.file_category != "VIDEO":
                    result.skipped += 1
                    continue

                # 숨김 파일 건너뛰기
                if nas_file.is_hidden_file:
                    result.skipped += 1
                    continue

                # 기존 항목 확인
                existing = self.get_by_nas_file_id(nas_file.id)

                if existing:
                    # 업데이트 (파일 크기 변경 등)
                    if existing.file_size_bytes != nas_file.file_size_bytes:
                        self.update(
                            existing.id,
                            file_size_bytes=nas_file.file_size_bytes,
                        )
                        result.updated += 1
                    else:
                        result.skipped += 1
                else:
                    # 새로 생성
                    self.create_from_nas_file(nas_file)
                    result.created += 1

            except Exception as e:
                result.errors += 1
                result.error_messages.append(f"{nas_file.file_name}: {str(e)}")

            # 진행 상황 콜백
            if on_progress:
                on_progress(idx + 1, total)

        # 삭제된 파일 처리 (NAS에 없는 항목 삭제)
        for item in list(self._items.values()):
            if item.nas_file_id and item.nas_file_id not in new_nas_ids:
                self.delete(item.id)
                result.deleted += 1

        result.duration_seconds = time.time() - start_time
        return result

    def clear(self) -> int:
        """모든 카탈로그 아이템 삭제"""
        count = len(self._items)
        self._items.clear()
        return count


# 싱글톤 인스턴스
_service: FlatCatalogService | None = None


def get_flat_catalog_service() -> FlatCatalogService:
    """FlatCatalogService 싱글톤 반환"""
    global _service
    if _service is None:
        _service = FlatCatalogService()
    return _service
