"""
Block F: Flat Catalog 단위 테스트

TDD 방식으로 작성된 테스트 케이스.
"""

import pytest
from uuid import uuid4, UUID

from src.blocks.flat_catalog.models import (
    CatalogItem,
    CatalogSyncResult,
    NASFileInfo,
)
from src.blocks.flat_catalog.service import FlatCatalogService, get_flat_catalog_service


class TestCatalogItem:
    """CatalogItem 모델 테스트"""

    def test_default_values(self):
        """기본값 테스트"""
        item = CatalogItem()

        assert item.id is not None
        assert item.nas_file_id is None
        assert item.display_title == ""
        assert item.project_code == "OTHER"
        assert item.is_visible is True
        assert item.confidence == 0.0
        assert item.category_tags == []

    def test_to_dict(self):
        """딕셔너리 변환"""
        item = CatalogItem(
            display_title="Test Video",
            project_code="WSOP",
            year=2024,
        )
        result = item.to_dict()

        assert result["display_title"] == "Test Video"
        assert result["project_code"] == "WSOP"
        assert result["year"] == 2024
        assert "id" in result
        assert "created_at" in result

    def test_from_dict(self):
        """딕셔너리에서 생성"""
        data = {
            "id": str(uuid4()),
            "display_title": "WSOP 2024 Event #5",
            "project_code": "WSOP",
            "year": 2024,
            "category_tags": ["NLHE", "Main Event"],
        }
        item = CatalogItem.from_dict(data)

        assert item.display_title == "WSOP 2024 Event #5"
        assert item.project_code == "WSOP"
        assert item.year == 2024
        assert "NLHE" in item.category_tags

    def test_format_file_size(self):
        """파일 크기 포맷팅"""
        item = CatalogItem(file_size_bytes=1536000000)  # 약 1.43 GB
        result = item.format_file_size()

        assert "GB" in result
        assert "1." in result

    def test_format_file_size_small(self):
        """작은 파일 크기 포맷팅"""
        item = CatalogItem(file_size_bytes=500)
        result = item.format_file_size()

        assert "B" in result

    def test_update_timestamp(self):
        """타임스탬프 업데이트"""
        item = CatalogItem()
        original_updated = item.updated_at

        import time
        time.sleep(0.01)  # 작은 지연
        item.update_timestamp()

        assert item.updated_at > original_updated


class TestCatalogSyncResult:
    """CatalogSyncResult 테스트"""

    def test_total_processed(self):
        """총 처리 개수 계산"""
        result = CatalogSyncResult(
            created=10,
            updated=5,
            deleted=2,
            skipped=3,
        )

        assert result.total_processed == 20

    def test_to_dict(self):
        """딕셔너리 변환"""
        result = CatalogSyncResult(
            created=10,
            errors=2,
            error_messages=["Error 1", "Error 2"],
        )
        data = result.to_dict()

        assert data["created"] == 10
        assert data["errors"] == 2
        assert len(data["error_messages"]) == 2


class TestNASFileInfo:
    """NASFileInfo 테스트"""

    def test_from_dict(self):
        """딕셔너리에서 생성"""
        data = {
            "id": str(uuid4()),
            "file_path": "/nas/videos/test.mp4",
            "file_name": "test.mp4",
            "file_size_bytes": 1000000,
            "file_extension": ".mp4",
            "file_category": "VIDEO",
        }
        info = NASFileInfo.from_dict(data)

        assert info.file_name == "test.mp4"
        assert info.file_category == "VIDEO"
        assert info.is_hidden_file is False


class TestFlatCatalogService:
    """FlatCatalogService 테스트"""

    @pytest.fixture
    def service(self):
        """새 서비스 인스턴스 (테스트 격리)"""
        return FlatCatalogService()

    @pytest.fixture
    def sample_nas_file(self) -> NASFileInfo:
        """샘플 NAS 파일"""
        return NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/WSOP/2024/WSOP_2024_Event5_Day1.mp4",
            file_name="WSOP_2024_Event5_Day1.mp4",
            file_size_bytes=2000000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )

    def test_create_from_nas_file(self, service: FlatCatalogService, sample_nas_file: NASFileInfo):
        """NAS 파일에서 카탈로그 아이템 생성"""
        item = service.create_from_nas_file(sample_nas_file)

        assert item is not None
        assert item.nas_file_id == sample_nas_file.id
        assert "WSOP" in item.display_title
        assert "2024" in item.display_title
        assert item.project_code == "WSOP"
        assert item.confidence >= 0.8  # 패턴 매칭 시 높은 신뢰도

    def test_get_by_id(self, service: FlatCatalogService, sample_nas_file: NASFileInfo):
        """ID로 조회"""
        created = service.create_from_nas_file(sample_nas_file)
        found = service.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    def test_get_by_id_not_found(self, service: FlatCatalogService):
        """존재하지 않는 ID"""
        result = service.get_by_id(uuid4())
        assert result is None

    def test_get_by_nas_file_id(self, service: FlatCatalogService, sample_nas_file: NASFileInfo):
        """NAS 파일 ID로 조회"""
        created = service.create_from_nas_file(sample_nas_file)
        found = service.get_by_nas_file_id(sample_nas_file.id)

        assert found is not None
        assert found.nas_file_id == sample_nas_file.id

    def test_get_all_empty(self, service: FlatCatalogService):
        """빈 카탈로그"""
        items = service.get_all()
        assert len(items) == 0

    def test_get_all_with_items(self, service: FlatCatalogService):
        """카탈로그 목록 조회"""
        # 여러 아이템 생성
        for i in range(5):
            nas_file = NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/test_{i}.mp4",
                file_name=f"WSOP_2024_Event{i}_Day1.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            service.create_from_nas_file(nas_file)

        items = service.get_all()
        assert len(items) == 5

    def test_get_all_filter_by_project(self, service: FlatCatalogService):
        """프로젝트 코드 필터"""
        # WSOP 파일
        wsop_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/WSOP_2024_Event1_Day1.mp4",
            file_name="WSOP_2024_Event1_Day1.mp4",
            file_size_bytes=1000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )
        service.create_from_nas_file(wsop_file)

        # HCL 파일
        hcl_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/HCL_S12E05.mp4",
            file_name="HCL_S12E05.mp4",
            file_size_bytes=1000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )
        service.create_from_nas_file(hcl_file)

        wsop_items = service.get_all(project_code="WSOP")
        hcl_items = service.get_all(project_code="HCL")

        assert len(wsop_items) == 1
        assert len(hcl_items) == 1

    def test_get_all_filter_by_year(self, service: FlatCatalogService):
        """연도 필터"""
        nas_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/WSOP_2024_Event1_Day1.mp4",
            file_name="WSOP_2024_Event1_Day1.mp4",
            file_size_bytes=1000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )
        service.create_from_nas_file(nas_file)

        items_2024 = service.get_all(year=2024)
        items_2023 = service.get_all(year=2023)

        assert len(items_2024) == 1
        assert len(items_2023) == 0

    def test_get_all_pagination(self, service: FlatCatalogService):
        """페이지네이션"""
        # 10개 생성
        for i in range(10):
            nas_file = NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/test_{i}.mp4",
                file_name=f"test_{i}.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            service.create_from_nas_file(nas_file)

        page1 = service.get_all(skip=0, limit=3)
        page2 = service.get_all(skip=3, limit=3)

        assert len(page1) == 3
        assert len(page2) == 3
        assert page1[0].id != page2[0].id

    def test_search(self, service: FlatCatalogService):
        """검색"""
        nas_file = NASFileInfo(
            id=uuid4(),
            file_path="/nas/videos/WSOP_2024_MainEvent_FinalTable.mp4",
            file_name="WSOP_2024_MainEvent_FinalTable.mp4",
            file_size_bytes=1000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )
        service.create_from_nas_file(nas_file)

        results = service.search("Main Event")
        assert len(results) >= 1

    def test_search_no_results(self, service: FlatCatalogService):
        """검색 결과 없음"""
        results = service.search("nonexistent query")
        assert len(results) == 0

    def test_update(self, service: FlatCatalogService, sample_nas_file: NASFileInfo):
        """업데이트"""
        created = service.create_from_nas_file(sample_nas_file)
        original_title = created.display_title

        updated = service.update(created.id, display_title="New Title")

        assert updated is not None
        assert updated.display_title == "New Title"
        assert updated.display_title != original_title

    def test_update_not_found(self, service: FlatCatalogService):
        """존재하지 않는 아이템 업데이트"""
        result = service.update(uuid4(), display_title="Test")
        assert result is None

    def test_delete(self, service: FlatCatalogService, sample_nas_file: NASFileInfo):
        """삭제"""
        created = service.create_from_nas_file(sample_nas_file)

        success = service.delete(created.id)
        assert success is True

        found = service.get_by_id(created.id)
        assert found is None

    def test_delete_not_found(self, service: FlatCatalogService):
        """존재하지 않는 아이템 삭제"""
        success = service.delete(uuid4())
        assert success is False

    def test_set_visibility(self, service: FlatCatalogService, sample_nas_file: NASFileInfo):
        """가시성 설정"""
        created = service.create_from_nas_file(sample_nas_file)
        assert created.is_visible is True

        updated = service.set_visibility(created.id, False)
        assert updated is not None
        assert updated.is_visible is False

        # 숨김 처리된 아이템은 기본 조회에서 제외
        visible_items = service.get_all(visible_only=True)
        all_items = service.get_all(visible_only=False)

        assert len(visible_items) == 0
        assert len(all_items) == 1

    def test_count(self, service: FlatCatalogService):
        """개수 조회"""
        for i in range(5):
            nas_file = NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/WSOP_2024_Event{i}_Day1.mp4",
                file_name=f"WSOP_2024_Event{i}_Day1.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            service.create_from_nas_file(nas_file)

        assert service.count() == 5
        assert service.count(project_code="WSOP") == 5

    def test_get_projects(self, service: FlatCatalogService):
        """프로젝트 통계"""
        # WSOP 파일 3개
        for i in range(3):
            nas_file = NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/WSOP_2024_Event{i}_Day1.mp4",
                file_name=f"WSOP_2024_Event{i}_Day1.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            service.create_from_nas_file(nas_file)

        # HCL 파일 2개
        for i in range(2):
            nas_file = NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/HCL_S12E0{i}.mp4",
                file_name=f"HCL_S12E0{i}.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            service.create_from_nas_file(nas_file)

        projects = service.get_projects()

        assert len(projects) == 2
        # 개수 기준 내림차순
        assert projects[0]["code"] == "WSOP"
        assert projects[0]["count"] == 3
        assert projects[1]["code"] == "HCL"
        assert projects[1]["count"] == 2

    def test_get_years(self, service: FlatCatalogService):
        """연도 목록"""
        for year in [2024, 2023, 2022]:
            nas_file = NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/WSOP_{year}_Event1_Day1.mp4",
                file_name=f"WSOP_{year}_Event1_Day1.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            service.create_from_nas_file(nas_file)

        years = service.get_years()

        assert years == [2024, 2023, 2022]  # 내림차순

    def test_clear(self, service: FlatCatalogService):
        """전체 삭제"""
        for i in range(5):
            nas_file = NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/test_{i}.mp4",
                file_name=f"test_{i}.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            service.create_from_nas_file(nas_file)

        count = service.clear()

        assert count == 5
        assert service.count(visible_only=False) == 0


class TestCatalogSync:
    """카탈로그 동기화 테스트"""

    @pytest.fixture
    def service(self):
        """새 서비스 인스턴스"""
        return FlatCatalogService()

    def test_sync_create_new(self, service: FlatCatalogService):
        """새 파일 동기화"""
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

        result = service.sync_from_nas_files(nas_files)

        assert result.created == 3
        assert result.updated == 0
        assert result.errors == 0

    def test_sync_skip_non_video(self, service: FlatCatalogService):
        """비디오가 아닌 파일 건너뛰기"""
        nas_files = [
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/metadata.json",
                file_name="metadata.json",
                file_size_bytes=1000,
                file_extension=".json",
                file_category="METADATA",
            ),
        ]

        result = service.sync_from_nas_files(nas_files)

        assert result.skipped == 1
        assert result.created == 0

    def test_sync_skip_hidden(self, service: FlatCatalogService):
        """숨김 파일 건너뛰기"""
        nas_files = [
            NASFileInfo(
                id=uuid4(),
                file_path="/nas/videos/.hidden_video.mp4",
                file_name=".hidden_video.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
                is_hidden_file=True,
            ),
        ]

        result = service.sync_from_nas_files(nas_files)

        assert result.skipped == 1
        assert result.created == 0

    def test_sync_update_existing(self, service: FlatCatalogService):
        """기존 파일 업데이트"""
        nas_file_id = uuid4()
        original_file = NASFileInfo(
            id=nas_file_id,
            file_path="/nas/videos/test.mp4",
            file_name="WSOP_2024_Event1_Day1.mp4",
            file_size_bytes=1000000,
            file_extension=".mp4",
            file_category="VIDEO",
        )

        # 먼저 생성
        service.sync_from_nas_files([original_file])

        # 파일 크기가 변경된 경우
        updated_file = NASFileInfo(
            id=nas_file_id,
            file_path="/nas/videos/test.mp4",
            file_name="WSOP_2024_Event1_Day1.mp4",
            file_size_bytes=2000000,  # 크기 변경
            file_extension=".mp4",
            file_category="VIDEO",
        )

        result = service.sync_from_nas_files([updated_file])

        assert result.updated == 1
        assert result.created == 0

    def test_sync_delete_removed(self, service: FlatCatalogService):
        """삭제된 파일 처리"""
        file1_id = uuid4()
        file2_id = uuid4()

        # 두 파일 생성
        files = [
            NASFileInfo(
                id=file1_id,
                file_path="/nas/videos/file1.mp4",
                file_name="WSOP_2024_Event1_Day1.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
            NASFileInfo(
                id=file2_id,
                file_path="/nas/videos/file2.mp4",
                file_name="WSOP_2024_Event2_Day1.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
        ]
        service.sync_from_nas_files(files)

        # 하나만 남김
        remaining_files = [
            NASFileInfo(
                id=file1_id,
                file_path="/nas/videos/file1.mp4",
                file_name="WSOP_2024_Event1_Day1.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            ),
        ]
        result = service.sync_from_nas_files(remaining_files)

        assert result.deleted == 1
        assert service.count(visible_only=False) == 1

    def test_sync_progress_callback(self, service: FlatCatalogService):
        """진행 상황 콜백"""
        progress_calls = []

        def on_progress(current: int, total: int):
            progress_calls.append((current, total))

        nas_files = [
            NASFileInfo(
                id=uuid4(),
                file_path=f"/nas/videos/test_{i}.mp4",
                file_name=f"WSOP_2024_Event{i}_Day1.mp4",
                file_size_bytes=1000000,
                file_extension=".mp4",
                file_category="VIDEO",
            )
            for i in range(3)
        ]

        service.sync_from_nas_files(nas_files, on_progress=on_progress)

        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)


class TestSingleton:
    """싱글톤 패턴 테스트"""

    def test_get_flat_catalog_service_singleton(self):
        """싱글톤 반환"""
        # 싱글톤 리셋을 위해 import
        import src.blocks.flat_catalog.service as service_module

        service_module._service = None  # 리셋

        service1 = get_flat_catalog_service()
        service2 = get_flat_catalog_service()

        assert service1 is service2
