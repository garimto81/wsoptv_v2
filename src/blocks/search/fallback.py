"""
Search Block Fallback

MeiliSearch 장애 시 PostgreSQL LIKE 검색 (Circuit Breaker 패턴)
"""

from typing import List
from datetime import datetime, timedelta

from .models import SearchItem


class CircuitBreaker:
    """
    Circuit Breaker 패턴 구현

    상태:
    - CLOSED: 정상 동작
    - OPEN: 장애 감지 (fallback 사용)
    - HALF_OPEN: 복구 테스트
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        초기화

        Args:
            failure_threshold: 장애 판정 임계값
            timeout: OPEN 상태 유지 시간 (초)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        """Circuit이 OPEN 상태인지 확인"""
        if self.state == "OPEN":
            # timeout 경과 시 HALF_OPEN으로 전환
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    self.state = "HALF_OPEN"
                    return False
            return True
        return False

    def record_success(self):
        """성공 기록"""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        """실패 기록"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class FallbackSearch:
    """
    Fallback 검색 엔진

    MeiliSearch 장애 시 PostgreSQL LIKE 쿼리로 대체
    """

    def __init__(self):
        """초기화"""
        # 실제로는 DB 연결 필요
        # 테스트용 Mock 데이터
        self._mock_data = [
            {
                "id": "fallback1",
                "title": "Python Programming",
                "description": "Learn Python",
                "score": 1.0
            },
            {
                "id": "fallback2",
                "title": "JavaScript Basics",
                "description": "Learn JavaScript",
                "score": 0.8
            }
        ]

    async def search(self, keyword: str) -> List[SearchItem]:
        """
        PostgreSQL LIKE 검색

        Args:
            keyword: 검색 키워드

        Returns:
            검색 결과 아이템 리스트
        """
        # 실제로는 PostgreSQL LIKE 쿼리 실행
        # SELECT * FROM contents WHERE title LIKE '%keyword%' OR description LIKE '%keyword%'

        results = []
        keyword_lower = keyword.lower()

        for data in self._mock_data:
            title = data.get("title", "").lower()
            description = data.get("description", "").lower()

            if keyword_lower in title or keyword_lower in description:
                item = SearchItem(
                    id=data["id"],
                    title=data["title"],
                    score=data.get("score", 1.0),
                    highlights=[],
                    description=data.get("description")
                )
                results.append(item)

        return results


class SearchWithFallback:
    """
    Circuit Breaker 패턴을 적용한 검색 서비스

    MeiliSearch 장애 시 자동으로 PostgreSQL fallback 사용
    """

    def __init__(self, primary_search, fallback_search: FallbackSearch):
        """
        초기화

        Args:
            primary_search: 주 검색 엔진 (MeiliSearch)
            fallback_search: 대체 검색 엔진 (PostgreSQL)
        """
        self.primary_search = primary_search
        self.fallback_search = fallback_search
        self.circuit_breaker = CircuitBreaker()

    async def search(self, keyword: str) -> List[SearchItem]:
        """
        Circuit Breaker 패턴 적용 검색

        Args:
            keyword: 검색 키워드

        Returns:
            검색 결과 아이템 리스트
        """
        # Circuit이 OPEN이면 바로 fallback 사용
        if self.circuit_breaker.is_open():
            return await self.fallback_search.search(keyword)

        try:
            # Primary 검색 시도
            results = await self.primary_search.search(keyword)
            self.circuit_breaker.record_success()
            return results

        except Exception as e:
            # 실패 시 Circuit Breaker 기록
            self.circuit_breaker.record_failure()

            # Fallback 사용
            return await self.fallback_search.search(keyword)
