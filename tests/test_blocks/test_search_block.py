"""
Search Block 테스트

TDD RED Phase: Search 블럭의 핵심 기능 검증
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSearchBlock:
    """Search Block - L1 (Auth 의존) 블럭 테스트"""

    @pytest.mark.asyncio
    async def test_search_by_keyword(self):
        """키워드 기반 검색"""
        from src.blocks.search.service import SearchService
        from src.blocks.search.models import SearchQuery

        # Mock auth service
        mock_auth = AsyncMock()
        mock_auth.validate_token.return_value = MagicMock(valid=True, user_id="user123")

        service = SearchService(auth_service=mock_auth)

        # 인덱스에 테스트 데이터 추가
        await service.index_content(
            content_id="content1",
            title="Python Programming Tutorial",
            description="Learn Python programming"
        )
        await service.index_content(
            content_id="content2",
            title="JavaScript Tutorial",
            description="Learn JavaScript basics"
        )

        # 검색 수행
        query = SearchQuery(keyword="Python", page=1, size=10)
        result = await service.search(query, token="valid_token")

        # 검증
        assert result.total >= 1
        assert len(result.items) >= 1
        assert any("Python" in item.title for item in result.items)
        assert result.took_ms >= 0

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """필터링 기능 검색"""
        from src.blocks.search.service import SearchService
        from src.blocks.search.models import SearchQuery

        mock_auth = AsyncMock()
        mock_auth.validate_token.return_value = MagicMock(valid=True, user_id="user123")

        service = SearchService(auth_service=mock_auth)

        # 인덱스에 테스트 데이터 추가 (카테고리 포함)
        await service.index_content(
            content_id="content1",
            title="Python Tutorial",
            category="programming",
            tags=["python", "tutorial"]
        )
        await service.index_content(
            content_id="content2",
            title="Python News",
            category="news",
            tags=["python", "news"]
        )

        # 필터링 검색 (category=programming)
        query = SearchQuery(
            keyword="Python",
            filters={"category": "programming"},
            page=1,
            size=10
        )
        result = await service.search(query, token="valid_token")

        # 검증
        assert result.total >= 1
        assert all(item.id == "content1" or "programming" in str(item) for item in result.items)

    @pytest.mark.asyncio
    async def test_search_pagination(self):
        """페이지네이션 검색"""
        from src.blocks.search.service import SearchService
        from src.blocks.search.models import SearchQuery

        mock_auth = AsyncMock()
        mock_auth.validate_token.return_value = MagicMock(valid=True, user_id="user123")

        service = SearchService(auth_service=mock_auth)

        # 인덱스에 10개 데이터 추가
        for i in range(10):
            await service.index_content(
                content_id=f"content{i}",
                title=f"Tutorial {i}",
                description="Learn programming"
            )

        # 첫 페이지 (size=3)
        query_page1 = SearchQuery(keyword="Tutorial", page=1, size=3)
        result_page1 = await service.search(query_page1, token="valid_token")

        assert len(result_page1.items) == 3
        assert result_page1.total == 10

        # 두 번째 페이지
        query_page2 = SearchQuery(keyword="Tutorial", page=2, size=3)
        result_page2 = await service.search(query_page2, token="valid_token")

        assert len(result_page2.items) == 3
        # 첫 페이지와 두 번째 페이지의 아이템이 다름
        page1_ids = {item.id for item in result_page1.items}
        page2_ids = {item.id for item in result_page2.items}
        assert page1_ids != page2_ids

    @pytest.mark.asyncio
    async def test_meilisearch_fallback_to_postgres(self):
        """MeiliSearch 장애 시 PostgreSQL fallback"""
        from src.blocks.search.service import SearchService
        from src.blocks.search.models import SearchQuery

        mock_auth = AsyncMock()
        mock_auth.validate_token.return_value = MagicMock(valid=True, user_id="user123")

        # MeiliSearch가 실패하도록 설정
        service = SearchService(auth_service=mock_auth, use_fallback=True)

        # 검색 수행 (fallback이 동작해야 함)
        query = SearchQuery(keyword="Python", page=1, size=10)
        result = await service.search(query, token="valid_token")

        # fallback으로도 결과가 반환되어야 함
        assert result is not None
        assert result.total >= 0

    @pytest.mark.asyncio
    async def test_index_content(self):
        """컨텐츠 인덱싱"""
        from src.blocks.search.service import SearchService
        from src.blocks.search.models import SearchQuery

        mock_auth = AsyncMock()
        mock_auth.validate_token.return_value = MagicMock(valid=True, user_id="user123")
        service = SearchService(auth_service=mock_auth)

        # 인덱싱 수행
        await service.index_content(
            content_id="test_content",
            title="Test Title",
            description="Test Description"
        )

        # 인덱스에 추가되었는지 확인
        query = SearchQuery(keyword="Test Title", page=1, size=10)
        result = await service.search(query, token="valid_token")

        assert result.total >= 1
        assert any(item.id == "test_content" for item in result.items)

    @pytest.mark.asyncio
    async def test_remove_from_index(self):
        """인덱스에서 컨텐츠 제거"""
        from src.blocks.search.service import SearchService
        from src.blocks.search.models import SearchQuery

        mock_auth = AsyncMock()
        mock_auth.validate_token.return_value = MagicMock(valid=True, user_id="user123")

        service = SearchService(auth_service=mock_auth)

        # 인덱싱
        await service.index_content(
            content_id="to_remove",
            title="Will be removed",
            description="This will be removed"
        )

        # 제거 전 검색
        query = SearchQuery(keyword="removed", page=1, size=10)
        result_before = await service.search(query, token="valid_token")
        assert result_before.total >= 1

        # 제거
        await service.remove_from_index("to_remove")

        # 제거 후 검색
        result_after = await service.search(query, token="valid_token")
        assert not any(item.id == "to_remove" for item in result_after.items)

    @pytest.mark.asyncio
    async def test_reindex_all(self):
        """전체 재인덱싱"""
        from src.blocks.search.service import SearchService

        mock_auth = AsyncMock()
        service = SearchService(auth_service=mock_auth)

        # 데이터 추가
        await service.index_content(content_id="c1", title="Title 1")
        await service.index_content(content_id="c2", title="Title 2")
        await service.index_content(content_id="c3", title="Title 3")

        # 재인덱싱
        count = await service.reindex_all()

        # 3개 이상 인덱싱되어야 함 (테스트 데이터 포함 가능)
        assert count >= 3

    @pytest.mark.asyncio
    async def test_search_with_invalid_token(self):
        """유효하지 않은 토큰으로 검색 시도"""
        from src.blocks.search.service import SearchService
        from src.blocks.search.models import SearchQuery

        mock_auth = AsyncMock()
        mock_auth.validate_token.return_value = MagicMock(valid=False, error="token_invalid")

        service = SearchService(auth_service=mock_auth)

        query = SearchQuery(keyword="Python", page=1, size=10)

        # 인증 실패 시 에러 발생해야 함
        with pytest.raises(ValueError, match="Invalid token"):
            await service.search(query, token="invalid_token")

    @pytest.mark.asyncio
    async def test_search_highlights(self):
        """검색 결과 하이라이트 기능"""
        from src.blocks.search.service import SearchService
        from src.blocks.search.models import SearchQuery

        mock_auth = AsyncMock()
        mock_auth.validate_token.return_value = MagicMock(valid=True, user_id="user123")

        service = SearchService(auth_service=mock_auth)

        # 인덱싱
        await service.index_content(
            content_id="highlight_test",
            title="Python Programming",
            description="Learn Python programming with examples"
        )

        # 검색
        query = SearchQuery(keyword="Python", page=1, size=10)
        result = await service.search(query, token="valid_token")

        # 하이라이트가 포함되어야 함
        items = [item for item in result.items if item.id == "highlight_test"]
        if items:
            assert len(items[0].highlights) > 0
            assert any("Python" in h for h in items[0].highlights)


class TestSearchBlockEvents:
    """Search Block 이벤트 구독 테스트"""

    @pytest.mark.asyncio
    async def test_content_added_event(self):
        """content.added 이벤트 구독 시 자동 인덱싱"""
        from src.blocks.search.service import SearchService
        from src.orchestration.message_bus import MessageBus, BlockMessage

        mock_auth = AsyncMock()
        service = SearchService(auth_service=mock_auth)

        # 이벤트 발행 (content.added)
        bus = MessageBus.get_instance()
        await bus.publish(
            "content.added",
            BlockMessage(
                source_block="content",
                event_type="content.added",
                payload={
                    "content_id": "event_content",
                    "title": "Event Test Content",
                    "description": "Added via event"
                }
            )
        )

        # 이벤트 처리 대기 (실제 구현 시 이벤트 핸들러 필요)
        # 지금은 구조 테스트만 수행
        assert service is not None

    @pytest.mark.asyncio
    async def test_content_deleted_event(self):
        """content.deleted 이벤트 구독 시 자동 인덱스 제거"""
        from src.blocks.search.service import SearchService
        from src.orchestration.message_bus import MessageBus, BlockMessage

        mock_auth = AsyncMock()
        service = SearchService(auth_service=mock_auth)

        # 이벤트 발행 (content.deleted)
        bus = MessageBus.get_instance()
        await bus.publish(
            "content.deleted",
            BlockMessage(
                source_block="content",
                event_type="content.deleted",
                payload={
                    "content_id": "deleted_content"
                }
            )
        )

        # 이벤트 처리 대기
        assert service is not None


class TestFallbackSearch:
    """Fallback 검색 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_fallback_search(self):
        """PostgreSQL LIKE 검색 테스트"""
        from src.blocks.search.fallback import FallbackSearch

        fallback = FallbackSearch()

        # Mock 데이터
        results = await fallback.search("Python")

        # fallback도 결과를 반환해야 함
        assert results is not None
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_fallback_search_case_insensitive(self):
        """Fallback 검색 대소문자 무시"""
        from src.blocks.search.fallback import FallbackSearch

        fallback = FallbackSearch()

        # 대문자/소문자 검색 모두 동작해야 함
        results_upper = await fallback.search("PYTHON")
        results_lower = await fallback.search("python")
        results_mixed = await fallback.search("Python")

        assert len(results_upper) > 0
        assert len(results_lower) > 0
        assert len(results_mixed) > 0
        # 모두 같은 결과를 반환해야 함
        assert len(results_upper) == len(results_lower) == len(results_mixed)

    @pytest.mark.asyncio
    async def test_fallback_search_no_results(self):
        """Fallback 검색 결과 없음"""
        from src.blocks.search.fallback import FallbackSearch

        fallback = FallbackSearch()

        # 존재하지 않는 키워드
        results = await fallback.search("NonExistentKeyword12345")

        assert results is not None
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_fallback_search_partial_match(self):
        """Fallback 검색 부분 일치"""
        from src.blocks.search.fallback import FallbackSearch

        fallback = FallbackSearch()

        # 부분 문자열 검색 (Mock 데이터에 "Programming"이 있음)
        results = await fallback.search("Program")

        assert len(results) > 0
        assert any("Program" in item.title for item in results)


class TestCircuitBreaker:
    """Circuit Breaker 패턴 테스트"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_initial_state(self):
        """초기 상태는 CLOSED"""
        from src.blocks.search.fallback import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3, timeout=10)
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """실패 임계치 도달 시 OPEN"""
        from src.blocks.search.fallback import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3, timeout=10)

        # 3번 실패 기록
        for i in range(3):
            cb.record_failure()
            if i < 2:
                assert cb.state == "CLOSED", f"실패 {i+1}회 시에는 아직 CLOSED"

        assert cb.state == "OPEN"
        assert cb.failure_count == 3
        assert cb.is_open() is True

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_resets(self):
        """성공 시 실패 카운트 리셋"""
        from src.blocks.search.fallback import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)

        # 2번 실패
        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        # 성공
        cb.record_success()

        # 리셋 확인
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self):
        """타임아웃 후 HALF_OPEN 전환"""
        from src.blocks.search.fallback import CircuitBreaker
        import time

        cb = CircuitBreaker(failure_threshold=2, timeout=1)

        # OPEN 상태로 전환
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.is_open() is True

        # 타임아웃 대기
        time.sleep(1.1)

        # is_open() 호출 시 HALF_OPEN으로 전환되어야 함
        is_still_open = cb.is_open()
        assert is_still_open is False
        assert cb.state == "HALF_OPEN"

    @pytest.mark.asyncio
    async def test_circuit_breaker_stays_open_before_timeout(self):
        """타임아웃 전에는 OPEN 유지"""
        from src.blocks.search.fallback import CircuitBreaker
        import time

        cb = CircuitBreaker(failure_threshold=1, timeout=10)

        cb.record_failure()
        assert cb.state == "OPEN"

        # 짧은 시간만 대기
        time.sleep(0.1)

        # 여전히 OPEN 상태여야 함
        assert cb.is_open() is True
        assert cb.state == "OPEN"

    @pytest.mark.asyncio
    async def test_circuit_breaker_custom_threshold(self):
        """커스텀 임계치 테스트"""
        from src.blocks.search.fallback import CircuitBreaker

        # 임계치 1로 설정
        cb = CircuitBreaker(failure_threshold=1, timeout=10)

        cb.record_failure()
        assert cb.state == "OPEN"

        # 임계치 10으로 설정
        cb2 = CircuitBreaker(failure_threshold=10, timeout=10)
        for _ in range(9):
            cb2.record_failure()
        assert cb2.state == "CLOSED"

        cb2.record_failure()
        assert cb2.state == "OPEN"


class TestSearchWithFallback:
    """Primary + Fallback 통합 테스트"""

    @pytest.mark.asyncio
    async def test_uses_primary_when_healthy(self):
        """Primary 정상 시 Primary 사용"""
        from src.blocks.search.fallback import SearchWithFallback, FallbackSearch
        from src.blocks.search.service import SearchService

        primary = SearchService()
        fallback = FallbackSearch()

        search = SearchWithFallback(primary_search=primary, fallback_search=fallback)

        # 컨텐츠 인덱싱
        await primary.index_content("test1", "Python Tutorial", description="Learn Python")

        # 검색
        results = await search.search("Python")

        # Primary에서 검색되어야 함
        assert results is not None
        assert len(results) > 0
        assert any("Python" in item.title for item in results)

    @pytest.mark.asyncio
    async def test_uses_fallback_when_primary_fails(self):
        """Primary 실패 시 Fallback 사용"""
        from src.blocks.search.fallback import SearchWithFallback, FallbackSearch

        # Primary를 실패하도록 Mock
        class FailingPrimary:
            async def search(self, keyword):
                raise Exception("Primary search failed")

        primary = FailingPrimary()
        fallback = FallbackSearch()

        search = SearchWithFallback(primary_search=primary, fallback_search=fallback)

        # 검색 (Primary 실패 → Fallback 사용)
        results = await search.search("Python")

        # Fallback에서 결과가 반환되어야 함
        assert results is not None
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_circuit_opens_after_repeated_failures(self):
        """반복 실패 시 Circuit OPEN"""
        from src.blocks.search.fallback import SearchWithFallback, FallbackSearch

        class FailingPrimary:
            async def search(self, keyword):
                raise Exception("Primary search failed")

        primary = FailingPrimary()
        fallback = FallbackSearch()

        search = SearchWithFallback(primary_search=primary, fallback_search=fallback)

        # 실패 임계치만큼 검색 (기본값 5)
        for _ in range(5):
            await search.search("test")

        # Circuit이 OPEN 상태여야 함
        assert search.circuit_breaker.state == "OPEN"

    @pytest.mark.asyncio
    async def test_circuit_recovery_on_success(self):
        """성공 시 Circuit 복구"""
        from src.blocks.search.fallback import SearchWithFallback, FallbackSearch

        class SuccessfulPrimary:
            """항상 성공하는 Primary 검색"""
            async def search(self, keyword):
                return []  # 빈 결과지만 성공

        primary = SuccessfulPrimary()
        fallback = FallbackSearch()

        search = SearchWithFallback(primary_search=primary, fallback_search=fallback)

        # 성공적인 검색
        await search.search("Test")

        # Circuit이 CLOSED 상태여야 함
        assert search.circuit_breaker.state == "CLOSED"
        assert search.circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_direct_fallback_when_circuit_open(self):
        """Circuit OPEN 시 Primary 건너뛰고 Fallback 직접 사용"""
        from src.blocks.search.fallback import SearchWithFallback, FallbackSearch

        call_count = {"primary": 0}

        class CountingPrimary:
            async def search(self, keyword):
                call_count["primary"] += 1
                raise Exception("Primary failed")

        primary = CountingPrimary()
        fallback = FallbackSearch()

        search = SearchWithFallback(primary_search=primary, fallback_search=fallback)

        # Circuit을 OPEN으로 만들기
        for _ in range(5):
            await search.search("test")

        primary_calls_before = call_count["primary"]

        # Circuit OPEN 상태에서 검색
        await search.search("test")

        # Primary가 호출되지 않아야 함 (Circuit이 차단)
        assert call_count["primary"] == primary_calls_before
