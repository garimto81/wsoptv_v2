"""
Block F + Block G 통합 테스트

Flat Catalog와 Title Generator 간의 통합 동작 검증.
"""

import pytest
from uuid import uuid4

from src.blocks.flat_catalog.models import CatalogItem, NASFileInfo
from src.blocks.flat_catalog.service import FlatCatalogService
from src.blocks.title_generator.models import ProjectCode
from src.blocks.title_generator.service import TitleGeneratorService


class TestCatalogTitleIntegration:
    """카탈로그-제목 생성 통합 테스트"""

    @pytest.fixture
    def title_service(self):
        """Title Generator 서비스"""
        return TitleGeneratorService()

    @pytest.fixture
    def catalog_service(self, title_service):
        """Flat Catalog 서비스 (Title Generator 주입)"""
        return FlatCatalogService(title_generator=title_service)

    def test_nas_file_to_catalog_item_wsop(self, catalog_service):
        """WSOP 파일 → 카탈로그 아이템 변환"""
        nas_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/WSOP/2024/WSOP_2024_Event5_Day1.mp4",
            file_name="WSOP_2024_Event5_Day1.mp4",
            file_size_bytes=2000000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )

        item = catalog_service.create_from_nas_file(nas_file)

        assert item is not None
        assert "WSOP" in item.display_title
        assert "2024" in item.display_title
        assert item.project_code == "WSOP"
        assert item.year == 2024
        assert item.confidence >= 0.8

    def test_nas_file_to_catalog_item_hcl(self, catalog_service):
        """HCL 파일 → 카탈로그 아이템 변환"""
        nas_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/HCL/Season12/HCL_S12E05.mp4",
            file_name="HCL_S12E05.mp4",
            file_size_bytes=1500000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )

        item = catalog_service.create_from_nas_file(nas_file)

        assert item is not None
        assert "HCL" in item.display_title
        assert item.project_code == "HCL"
        assert item.confidence >= 0.8

    def test_nas_file_to_catalog_item_ggmillions(self, catalog_service):
        """GGMillions 파일 → 카탈로그 아이템 변환"""
        nas_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/GGMillions/GGMillions_SuperHighRoller_2024.mp4",
            file_name="GGMillions_SuperHighRoller_2024.mp4",
            file_size_bytes=1800000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )

        item = catalog_service.create_from_nas_file(nas_file)

        assert item is not None
        assert "GGMillions" in item.display_title
        assert item.project_code == "GGMILLIONS"

    def test_batch_sync_multiple_projects(self, catalog_service):
        """여러 프로젝트 파일 배치 동기화"""
        nas_files = [
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/WSOP_2024_Event1_Day1.mp4",
                file_name="WSOP_2024_Event1_Day1.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/HCL_S10E01.mp4",
                file_name="HCL_S10E01.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/GOG_S1E5.mp4",
                file_name="GOG_S1E5.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
        ]

        result = catalog_service.sync_from_nas_files(nas_files)

        assert result.created == 3
        assert result.errors == 0

        # 프로젝트별 조회
        projects = catalog_service.get_projects()
        project_codes = [p["code"] for p in projects]

        assert "WSOP" in project_codes
        assert "HCL" in project_codes
        assert "GOG" in project_codes

    def test_search_by_title(self, catalog_service):
        """제목 검색"""
        # 데이터 추가
        nas_files = [
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/WSOP_2024_MainEvent_FinalTable.mp4",
                file_name="WSOP_2024_MainEvent_FinalTable.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/WSOP_2024_Event5_Day1.mp4",
                file_name="WSOP_2024_Event5_Day1.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
        ]
        catalog_service.sync_from_nas_files(nas_files)

        # 검색
        results = catalog_service.search("Main Event")

        assert len(results) >= 1
        assert any("Main Event" in r.display_title for r in results)

    def test_filter_by_project_and_year(self, catalog_service):
        """프로젝트 및 연도 필터"""
        nas_files = [
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/WSOP_2024_Event1_Day1.mp4",
                file_name="WSOP_2024_Event1_Day1.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/WSOP_2023_Event1_Day1.mp4",
                file_name="WSOP_2023_Event1_Day1.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/HCL_S12E01.mp4",
                file_name="HCL_S12E01.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
        ]
        catalog_service.sync_from_nas_files(nas_files)

        # 프로젝트 필터
        wsop_items = catalog_service.get_all(project_code="WSOP")
        assert len(wsop_items) == 2

        # 연도 필터
        items_2024 = catalog_service.get_all(year=2024)
        assert len(items_2024) == 1

        # 복합 필터
        wsop_2024 = catalog_service.get_all(project_code="WSOP", year=2024)
        assert len(wsop_2024) == 1


class TestCatalogStats:
    """카탈로그 통계 통합 테스트"""

    @pytest.fixture
    def catalog_service(self):
        """테스트용 카탈로그 서비스"""
        return FlatCatalogService()

    def test_get_projects_with_counts(self, catalog_service):
        """프로젝트별 통계"""
        # 데이터 추가: WSOP 3개, HCL 2개
        files = []
        for i in range(3):
            files.append(
                NASFileInfo(
                    id=uuid4(),
                    file_path=f"/nas/videos/WSOP_2024_Event{i}_Day1.mp4",
                    file_name=f"WSOP_2024_Event{i}_Day1.mp4",
                    file_size_bytes=1000000000,
                    file_extension=".mp4",
                    file_category="VIDEO",
                )
            )
        for i in range(2):
            files.append(
                NASFileInfo(
                    id=uuid4(),
                    file_path=f"/nas/videos/HCL_S12E0{i}.mp4",
                    file_name=f"HCL_S12E0{i}.mp4",
                    file_size_bytes=1000000000,
                    file_extension=".mp4",
                    file_category="VIDEO",
                )
            )

        catalog_service.sync_from_nas_files(files)

        # 통계 확인
        projects = catalog_service.get_projects()

        assert len(projects) == 2
        assert projects[0]["code"] == "WSOP"
        assert projects[0]["count"] == 3
        assert projects[1]["code"] == "HCL"
        assert projects[1]["count"] == 2

    def test_get_years(self, catalog_service):
        """연도 목록"""
        files = [
            NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/WSOP_{year}_Event1_Day1.mp4",
                file_name=f"WSOP_{year}_Event1_Day1.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            for year in [2024, 2023, 2022]
        ]
        catalog_service.sync_from_nas_files(files)

        years = catalog_service.get_years()

        assert years == [2024, 2023, 2022]  # 내림차순

    def test_count_visible_vs_all(self, catalog_service):
        """가시성 기준 개수"""
        files = [
            NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/test_{i}.mp4",
                file_name=f"WSOP_2024_Event{i}_Day1.mp4",
                file_size_bytes=1000000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            for i in range(5)
        ]
        catalog_service.sync_from_nas_files(files)

        # 하나 숨김 처리
        items = catalog_service.get_all()
        catalog_service.set_visibility(items[0].id, False)

        assert catalog_service.count(visible_only=True) == 4
        assert catalog_service.count(visible_only=False) == 5


class TestTitleGeneratorEdgeCases:
    """Title Generator 엣지 케이스 통합 테스트"""

    @pytest.fixture
    def catalog_service(self):
        return FlatCatalogService()

    def test_unknown_format_fallback(self, catalog_service):
        """알 수 없는 형식 Fallback"""
        nas_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/random_poker_video_2024.mp4",
            file_name="random_poker_video_2024.mp4",
            file_size_bytes=1000000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )

        item = catalog_service.create_from_nas_file(nas_file)

        assert item is not None
        assert item.project_code == "OTHER"
        assert item.confidence < 0.5  # Fallback 시 낮은 신뢰도

    def test_unicode_filename(self, catalog_service):
        """유니코드 파일명"""
        nas_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/WSOP_2024_이벤트5_Day1.mp4",
            file_name="WSOP_2024_이벤트5_Day1.mp4",
            file_size_bytes=1000000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )

        item = catalog_service.create_from_nas_file(nas_file)

        # 에러 없이 처리됨
        assert item is not None

    def test_very_long_title_truncation(self, catalog_service):
        """긴 제목 축약"""
        nas_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/WSOP_2024_MainEvent_Day1_Part1_FeatureTable_ExtendedCoverage.mp4",
            file_name="WSOP_2024_MainEvent_Day1_Part1_FeatureTable_ExtendedCoverage.mp4",
            file_size_bytes=1000000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )

        item = catalog_service.create_from_nas_file(nas_file)

        assert item is not None
        assert len(item.short_title) <= 50
