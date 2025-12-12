"""
Block F: Flat Catalog - 마이그레이션

기존 Episode 모델에서 CatalogItem으로 마이그레이션.
4단계 계층(Project → Season → Event → Episode)을 단일 계층으로 변환.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any
from uuid import UUID, uuid4

from src.blocks.flat_catalog.models import CatalogItem, NASFileInfo
from src.blocks.flat_catalog.service import FlatCatalogService, get_flat_catalog_service
from src.blocks.title_generator.service import TitleGeneratorService


logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """마이그레이션 결과"""

    total_episodes: int = 0
    migrated: int = 0
    skipped: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    error_messages: list[str] = None

    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_episodes": self.total_episodes,
            "migrated": self.migrated,
            "skipped": self.skipped,
            "errors": self.errors,
            "success_rate": (
                f"{(self.migrated / self.total_episodes * 100):.1f}%"
                if self.total_episodes > 0
                else "0%"
            ),
            "duration_seconds": self.duration_seconds,
            "error_messages": self.error_messages[:10],
        }


class EpisodeMigrator:
    """
    Episode → CatalogItem 마이그레이터

    기존 4단계 계층 데이터를 단일 계층으로 변환.
    """

    def __init__(
        self,
        catalog_service: FlatCatalogService | None = None,
        title_generator: TitleGeneratorService | None = None,
    ) -> None:
        self._catalog = catalog_service or get_flat_catalog_service()
        self._title_gen = title_generator or TitleGeneratorService()

    def migrate_episode(
        self,
        episode_data: dict[str, Any],
        project_data: dict[str, Any] | None = None,
        season_data: dict[str, Any] | None = None,
        event_data: dict[str, Any] | None = None,
    ) -> CatalogItem | None:
        """
        단일 Episode를 CatalogItem으로 변환

        Args:
            episode_data: 에피소드 데이터
            project_data: 프로젝트 데이터 (선택)
            season_data: 시즌 데이터 (선택)
            event_data: 이벤트 데이터 (선택)

        Returns:
            생성된 CatalogItem 또는 None
        """
        try:
            file_path = episode_data.get("file_path", "")
            file_name = episode_data.get("file_name", "")

            # 제목 생성
            generated = self._title_gen.generate(file_name, file_path)

            # 프로젝트 코드 결정 (기존 데이터 우선)
            project_code = "OTHER"
            if project_data and project_data.get("code"):
                project_code = project_data["code"]
            elif generated.metadata.project_code:
                project_code = generated.metadata.project_code.value

            # 연도 결정 (기존 데이터 우선)
            year = None
            if season_data and season_data.get("year"):
                year = season_data["year"]
            elif generated.metadata.year:
                year = generated.metadata.year

            # CatalogItem 생성
            item = CatalogItem(
                id=uuid4(),
                nas_file_id=UUID(episode_data["nas_file_id"])
                if episode_data.get("nas_file_id")
                else None,
                display_title=generated.display_title,
                short_title=generated.short_title,
                thumbnail_url=episode_data.get("thumbnail_url"),
                project_code=project_code,
                year=year,
                file_path=file_path,
                file_name=file_name,
                file_size_bytes=episode_data.get("file_size_bytes", 0),
                file_extension=episode_data.get("file_extension", ""),
                duration_seconds=episode_data.get("duration_seconds"),
                quality=episode_data.get("quality"),
                is_visible=episode_data.get("is_visible", True),
                confidence=generated.confidence,
            )

            # 카테고리 태그 추가
            if event_data and event_data.get("event_name"):
                item.category_tags.append(event_data["event_name"])
            if generated.metadata.game_type:
                item.category_tags.append(generated.metadata.game_type.value)
            if generated.metadata.content_type:
                item.category_tags.append(generated.metadata.content_type.value)

            # 기존 타임스탬프 보존
            if episode_data.get("created_at"):
                if isinstance(episode_data["created_at"], str):
                    item.created_at = datetime.fromisoformat(episode_data["created_at"])
                else:
                    item.created_at = episode_data["created_at"]

            # 인메모리 저장
            self._catalog._items[item.id] = item

            return item

        except Exception as e:
            logger.error(f"Migration error for episode: {e}")
            return None

    def migrate_all(
        self,
        episodes: list[dict[str, Any]],
        projects: dict[str, dict[str, Any]] | None = None,
        seasons: dict[str, dict[str, Any]] | None = None,
        events: dict[str, dict[str, Any]] | None = None,
    ) -> MigrationResult:
        """
        전체 Episode 목록을 마이그레이션

        Args:
            episodes: 에피소드 데이터 목록
            projects: 프로젝트 ID → 데이터 매핑 (선택)
            seasons: 시즌 ID → 데이터 매핑 (선택)
            events: 이벤트 ID → 데이터 매핑 (선택)

        Returns:
            MigrationResult: 마이그레이션 결과
        """
        import time

        start_time = time.time()
        result = MigrationResult(total_episodes=len(episodes))

        projects = projects or {}
        seasons = seasons or {}
        events = events or {}

        for episode in episodes:
            try:
                # 관련 데이터 조회
                project_id = episode.get("project_id")
                season_id = episode.get("season_id")
                event_id = episode.get("event_id")

                project_data = projects.get(str(project_id)) if project_id else None
                season_data = seasons.get(str(season_id)) if season_id else None
                event_data = events.get(str(event_id)) if event_id else None

                # 마이그레이션
                item = self.migrate_episode(
                    episode_data=episode,
                    project_data=project_data,
                    season_data=season_data,
                    event_data=event_data,
                )

                if item:
                    result.migrated += 1
                else:
                    result.skipped += 1

            except Exception as e:
                result.errors += 1
                result.error_messages.append(
                    f"Episode {episode.get('id', 'unknown')}: {str(e)}"
                )

        result.duration_seconds = time.time() - start_time
        return result

    def migrate_from_nas_files(
        self,
        nas_files: list[NASFileInfo],
    ) -> MigrationResult:
        """
        NAS 파일 목록에서 직접 마이그레이션

        기존 Episode 데이터 없이 NAS 파일만으로 카탈로그 생성.
        """
        import time

        start_time = time.time()
        result = MigrationResult(total_episodes=len(nas_files))

        for nas_file in nas_files:
            try:
                if nas_file.file_category != "VIDEO":
                    result.skipped += 1
                    continue

                if nas_file.is_hidden_file:
                    result.skipped += 1
                    continue

                # NAS 파일에서 카탈로그 아이템 생성
                item = self._catalog.create_from_nas_file(nas_file)
                if item:
                    result.migrated += 1
                else:
                    result.skipped += 1

            except Exception as e:
                result.errors += 1
                result.error_messages.append(f"{nas_file.file_name}: {str(e)}")

        result.duration_seconds = time.time() - start_time
        return result


def run_migration(
    episodes: list[dict[str, Any]],
    projects: dict[str, dict[str, Any]] | None = None,
    seasons: dict[str, dict[str, Any]] | None = None,
    events: dict[str, dict[str, Any]] | None = None,
) -> MigrationResult:
    """
    마이그레이션 실행 헬퍼 함수

    Args:
        episodes: 에피소드 데이터 목록
        projects: 프로젝트 매핑 (선택)
        seasons: 시즌 매핑 (선택)
        events: 이벤트 매핑 (선택)

    Returns:
        MigrationResult: 마이그레이션 결과
    """
    migrator = EpisodeMigrator()
    return migrator.migrate_all(
        episodes=episodes,
        projects=projects,
        seasons=seasons,
        events=events,
    )
