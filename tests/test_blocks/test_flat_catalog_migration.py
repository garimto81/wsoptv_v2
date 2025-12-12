"""
Block F: Flat Catalog 마이그레이션 테스트
"""

import pytest
from uuid import uuid4

from src.blocks.flat_catalog.models import NASFileInfo
from src.blocks.flat_catalog.service import FlatCatalogService
from src.blocks.flat_catalog.migration import (
    EpisodeMigrator,
    MigrationResult,
    run_migration,
)


class TestMigrationResult:
    """MigrationResult 테스트"""

    def test_default_values(self):
        """기본값"""
        result = MigrationResult()

        assert result.total_episodes == 0
        assert result.migrated == 0
        assert result.error_messages == []

    def test_to_dict(self):
        """딕셔너리 변환"""
        result = MigrationResult(
            total_episodes=100,
            migrated=95,
            skipped=3,
            errors=2,
            duration_seconds=5.5,
            error_messages=["Error 1", "Error 2"],
        )
        data = result.to_dict()

        assert data["total_episodes"] == 100
        assert data["migrated"] == 95
        assert data["success_rate"] == "95.0%"

    def test_to_dict_empty(self):
        """빈 결과"""
        result = MigrationResult()
        data = result.to_dict()

        assert data["success_rate"] == "0%"


class TestEpisodeMigrator:
    """EpisodeMigrator 테스트"""

    @pytest.fixture
    def service(self):
        """테스트용 서비스"""
        return FlatCatalogService()

    @pytest.fixture
    def migrator(self, service):
        """테스트용 마이그레이터"""
        return EpisodeMigrator(catalog_service=service)

    def test_migrate_episode_basic(self, migrator, service):
        """기본 에피소드 마이그레이션"""
        episode_data = {
            "id": str(uuid4()),
            "file_path": "/nas/videos/WSOP/2024/WSOP_2024_Event5_Day1.mp4",
            "file_name": "WSOP_2024_Event5_Day1.mp4",
            "file_size_bytes": 2000000000,
            "file_extension": ".mp4",
        }

        item = migrator.migrate_episode(episode_data)

        assert item is not None
        assert "WSOP" in item.display_title
        assert item.project_code == "WSOP"
        assert item.year == 2024

    def test_migrate_episode_with_project_data(self, migrator):
        """프로젝트 데이터 포함 마이그레이션"""
        episode_data = {
            "id": str(uuid4()),
            "file_path": "/nas/videos/test.mp4",
            "file_name": "random_video.mp4",
            "file_size_bytes": 1000000,
            "file_extension": ".mp4",
        }
        project_data = {
            "code": "HCL",
            "name": "Hustler Casino Live",
        }

        item = migrator.migrate_episode(
            episode_data=episode_data,
            project_data=project_data,
        )

        assert item is not None
        assert item.project_code == "HCL"

    def test_migrate_episode_with_season_data(self, migrator):
        """시즌 데이터 포함 마이그레이션"""
        episode_data = {
            "id": str(uuid4()),
            "file_path": "/nas/videos/test.mp4",
            "file_name": "episode_01.mp4",
            "file_size_bytes": 1000000,
            "file_extension": ".mp4",
        }
        season_data = {
            "year": 2023,
            "season_number": 5,
        }

        item = migrator.migrate_episode(
            episode_data=episode_data,
            season_data=season_data,
        )

        assert item is not None
        assert item.year == 2023

    def test_migrate_episode_with_event_tags(self, migrator):
        """이벤트 태그 포함 마이그레이션"""
        episode_data = {
            "id": str(uuid4()),
            "file_path": "/nas/videos/test.mp4",
            "file_name": "test.mp4",
            "file_size_bytes": 1000000,
            "file_extension": ".mp4",
        }
        event_data = {
            "event_name": "Main Event",
        }

        item = migrator.migrate_episode(
            episode_data=episode_data,
            event_data=event_data,
        )

        assert item is not None
        assert "Main Event" in item.category_tags

    def test_migrate_episode_preserves_nas_file_id(self, migrator):
        """NAS 파일 ID 보존"""
        nas_file_id = uuid4()
        episode_data = {
            "id": str(uuid4()),
            "nas_file_id": str(nas_file_id),
            "file_path": "/nas/videos/test.mp4",
            "file_name": "test.mp4",
            "file_size_bytes": 1000000,
            "file_extension": ".mp4",
        }

        item = migrator.migrate_episode(episode_data)

        assert item is not None
        assert item.nas_file_id == nas_file_id

    def test_migrate_episode_preserves_thumbnail(self, migrator):
        """썸네일 URL 보존"""
        episode_data = {
            "id": str(uuid4()),
            "file_path": "/nas/videos/test.mp4",
            "file_name": "test.mp4",
            "file_size_bytes": 1000000,
            "file_extension": ".mp4",
            "thumbnail_url": "/thumbnails/test.jpg",
        }

        item = migrator.migrate_episode(episode_data)

        assert item is not None
        assert item.thumbnail_url == "/thumbnails/test.jpg"

    def test_migrate_all_basic(self, migrator, service):
        """전체 마이그레이션"""
        episodes = [
            {
                "id": str(uuid4()),
                "file_path": f"/nas/videos/WSOP_2024_Event{i}_Day1.mp4",
                "file_name": f"WSOP_2024_Event{i}_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
            }
            for i in range(5)
        ]

        result = migrator.migrate_all(episodes)

        assert result.total_episodes == 5
        assert result.migrated == 5
        assert result.errors == 0
        assert service.count(visible_only=False) == 5

    def test_migrate_all_with_mappings(self, migrator, service):
        """매핑 데이터 포함 마이그레이션"""
        project_id = str(uuid4())
        season_id = str(uuid4())
        event_id = str(uuid4())

        episodes = [
            {
                "id": str(uuid4()),
                "project_id": project_id,
                "season_id": season_id,
                "event_id": event_id,
                "file_path": "/nas/videos/test.mp4",
                "file_name": "test.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
            }
        ]

        projects = {project_id: {"code": "WSOP"}}
        seasons = {season_id: {"year": 2024}}
        events = {event_id: {"event_name": "Main Event"}}

        result = migrator.migrate_all(
            episodes=episodes,
            projects=projects,
            seasons=seasons,
            events=events,
        )

        assert result.migrated == 1
        item = list(service._items.values())[0]
        assert item.project_code == "WSOP"
        assert item.year == 2024
        assert "Main Event" in item.category_tags

    def test_migrate_from_nas_files(self, migrator, service):
        """NAS 파일에서 직접 마이그레이션"""
        nas_files = [
            NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/WSOP_2024_Event{i}_Day1.mp4",
                file_name=f"WSOP_2024_Event{i}_Day1.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            for i in range(3)
        ]

        result = migrator.migrate_from_nas_files(nas_files)

        assert result.total_episodes == 3
        assert result.migrated == 3
        assert service.count(visible_only=False) == 3

    def test_migrate_from_nas_files_skip_non_video(self, migrator, service):
        """비디오가 아닌 파일 건너뛰기"""
        nas_files = [
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/data/metadata.json",
                file_name="metadata.json",
                file_size_bytes=1000,
                file_extension=".json",
                file_category="METADATA",
            ),
        ]

        result = migrator.migrate_from_nas_files(nas_files)

        assert result.skipped == 1
        assert result.migrated == 0

    def test_migrate_from_nas_files_skip_hidden(self, migrator, service):
        """숨김 파일 건너뛰기"""
        nas_files = [
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/.hidden.mp4",
                file_name=".hidden.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
                is_hidden_file=True,
            ),
        ]

        result = migrator.migrate_from_nas_files(nas_files)

        assert result.skipped == 1
        assert result.migrated == 0


class TestRunMigration:
    """run_migration 헬퍼 함수 테스트"""

    def test_run_migration(self):
        """헬퍼 함수 테스트"""
        episodes = [
            {
                "id": str(uuid4()),
                "file_path": "/nas/videos/test.mp4",
                "file_name": "WSOP_2024_Event1_Day1.mp4",
                "file_size_bytes": 1000000,
                "file_extension": ".mp4",
            }
        ]

        result = run_migration(episodes)

        assert result.migrated == 1
