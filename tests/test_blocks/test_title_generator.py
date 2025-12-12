"""
Block G: Title Generator 단위 테스트

TDD 방식으로 작성된 테스트 케이스.
"""

import pytest
from decimal import Decimal

from src.blocks.title_generator.models import (
    GeneratedTitle,
    ParsedMetadata,
    ProjectCode,
    GameType,
    ContentType,
)
from src.blocks.title_generator.patterns import PatternRegistry, get_pattern_registry
from src.blocks.title_generator.service import TitleGeneratorService


class TestProjectCode:
    """ProjectCode enum 테스트"""

    def test_from_string_exact_match(self):
        """정확한 문자열 매칭"""
        assert ProjectCode.from_string("WSOP") == ProjectCode.WSOP
        assert ProjectCode.from_string("HCL") == ProjectCode.HCL
        assert ProjectCode.from_string("GGMILLIONS") == ProjectCode.GGMILLIONS

    def test_from_string_case_insensitive(self):
        """대소문자 무시"""
        assert ProjectCode.from_string("wsop") == ProjectCode.WSOP
        assert ProjectCode.from_string("Wsop") == ProjectCode.WSOP
        assert ProjectCode.from_string("hcl") == ProjectCode.HCL

    def test_from_string_unknown(self):
        """알 수 없는 프로젝트는 OTHER"""
        assert ProjectCode.from_string("UNKNOWN") == ProjectCode.OTHER
        assert ProjectCode.from_string("random") == ProjectCode.OTHER


class TestParsedMetadata:
    """ParsedMetadata 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        meta = ParsedMetadata(
            project_code=ProjectCode.WSOP,
            year=2024,
            event_number=5,
            game_type=GameType.NLHE,
        )
        result = meta.to_dict()

        assert result["project_code"] == "WSOP"
        assert result["year"] == 2024
        assert result["event_number"] == 5
        assert result["game_type"] == "No-Limit Hold'em"

    def test_to_dict_with_none_values(self):
        """None 값 처리"""
        meta = ParsedMetadata()
        result = meta.to_dict()

        assert result["project_code"] is None
        assert result["year"] is None


class TestGeneratedTitle:
    """GeneratedTitle 테스트"""

    def test_confidence_validation(self):
        """신뢰도 범위 검증"""
        # 유효한 범위
        title = GeneratedTitle(
            display_title="Test",
            short_title="Test",
            confidence=0.5,
            metadata=ParsedMetadata(),
        )
        assert title.confidence == 0.5

        # 범위 초과
        with pytest.raises(ValueError):
            GeneratedTitle(
                display_title="Test",
                short_title="Test",
                confidence=1.5,
                metadata=ParsedMetadata(),
            )

    def test_fallback(self):
        """Fallback 제목 생성"""
        result = GeneratedTitle.fallback("random_video_file.mp4")

        assert result.display_title == "random video file"
        assert result.confidence == 0.1
        assert result.metadata.project_code is None

    def test_fallback_removes_extension(self):
        """확장자 제거"""
        result = GeneratedTitle.fallback("test_video.mkv")
        assert result.display_title == "test video"

    def test_to_dict(self):
        """딕셔너리 변환"""
        title = GeneratedTitle(
            display_title="WSOP 2024 Event #5",
            short_title="WSOP 2024 Event #5",
            confidence=0.95,
            metadata=ParsedMetadata(project_code=ProjectCode.WSOP, year=2024),
        )
        result = title.to_dict()

        assert result["display_title"] == "WSOP 2024 Event #5"
        assert result["confidence"] == 0.95
        assert result["metadata"]["project_code"] == "WSOP"


class TestPatternRegistry:
    """PatternRegistry 테스트"""

    def test_singleton(self):
        """싱글톤 패턴"""
        registry1 = get_pattern_registry()
        registry2 = get_pattern_registry()
        assert registry1 is registry2

    def test_wsop_patterns_registered(self):
        """WSOP 패턴 등록 확인"""
        registry = PatternRegistry()
        patterns = registry.get_patterns_for_project(ProjectCode.WSOP)
        assert len(patterns) > 0

    def test_match_wsop_event_day(self):
        """WSOP 이벤트+일차 패턴 매칭"""
        registry = PatternRegistry()
        result = registry.match("WSOP_2024_Event5_Day1.mp4")

        assert result is not None
        pattern, match = result
        assert pattern.project == ProjectCode.WSOP
        assert match.group("year") == "2024"
        assert match.group("event") == "5"
        assert match.group("day") == "1"

    def test_match_wsop_event_day_part(self):
        """WSOP 이벤트+일차+파트 패턴 매칭"""
        registry = PatternRegistry()
        result = registry.match("WSOP_2024_Event10_Day2_Part3.mp4")

        assert result is not None
        pattern, match = result
        assert match.group("part") == "3"

    def test_match_hcl_season_episode(self):
        """HCL 시즌+에피소드 패턴 매칭"""
        registry = PatternRegistry()
        result = registry.match("HCL_S12E05_HighStakes.mp4")

        assert result is not None
        pattern, match = result
        assert pattern.project == ProjectCode.HCL
        assert match.group("season") == "12"
        assert match.group("episode") == "05"

    def test_match_no_pattern(self):
        """매칭 실패"""
        registry = PatternRegistry()
        result = registry.match("completely_random_file.mp4")

        assert result is None

    def test_format_title_wsop(self):
        """WSOP 제목 포맷팅"""
        registry = PatternRegistry()
        result = registry.match("WSOP_2024_Event5_Day1.mp4")
        assert result is not None

        pattern, match = result
        title = PatternRegistry.format_title(pattern.title_template, match)

        assert "WSOP" in title
        assert "2024" in title
        assert "Day 1" in title

    def test_parse_buy_in(self):
        """바이인 파싱"""
        assert PatternRegistry.parse_buy_in("10K") == Decimal(10000)
        assert PatternRegistry.parse_buy_in("1M") == Decimal(1000000)
        assert PatternRegistry.parse_buy_in("$5K") == Decimal(5000)
        assert PatternRegistry.parse_buy_in("") is None

    def test_parse_game_type(self):
        """게임 타입 파싱"""
        assert PatternRegistry.parse_game_type("NLHE") == GameType.NLHE
        assert PatternRegistry.parse_game_type("PLO") == GameType.PLO
        assert PatternRegistry.parse_game_type("unknown") == GameType.OTHER
        assert PatternRegistry.parse_game_type(None) is None


class TestTitleGeneratorService:
    """TitleGeneratorService 테스트"""

    def test_generate_wsop_standard(self):
        """WSOP 표준 형식 제목 생성"""
        service = TitleGeneratorService()
        result = service.generate("WSOP_2024_Event5_Day1.mp4")

        assert "WSOP" in result.display_title
        assert "2024" in result.display_title
        assert result.confidence >= 0.9
        assert result.metadata.project_code == ProjectCode.WSOP
        assert result.metadata.year == 2024
        assert result.metadata.event_number == 5
        assert result.metadata.day_number == 1

    def test_generate_wsop_main_event(self):
        """WSOP Main Event 제목 생성"""
        service = TitleGeneratorService()
        result = service.generate("WSOP_2024_MainEvent_FinalTable.mp4")

        assert "Main Event" in result.display_title
        assert result.metadata.content_type == ContentType.FINAL_TABLE

    def test_generate_hcl_season_episode(self):
        """HCL 시즌+에피소드 제목 생성"""
        service = TitleGeneratorService()
        result = service.generate("HCL_S12E05.mp4")

        assert "HCL" in result.display_title
        assert "Season 12" in result.display_title
        assert "Episode" in result.display_title  # Episode 05 또는 Episode 5
        assert result.metadata.season_number == 12
        assert result.metadata.episode_number == 5

    def test_generate_ggmillions(self):
        """GGMillions 제목 생성"""
        service = TitleGeneratorService()
        result = service.generate("GGMillions_SuperHighRoller_2024.mp4")

        assert "GGMillions" in result.display_title
        assert result.metadata.project_code == ProjectCode.GGMILLIONS

    def test_generate_gog(self):
        """Game of Gold 제목 생성"""
        service = TitleGeneratorService()
        result = service.generate("GOG_S1E5.mp4")

        assert "Game of Gold" in result.display_title
        assert result.metadata.project_code == ProjectCode.GOG

    def test_generate_pad(self):
        """Poker After Dark 제목 생성"""
        service = TitleGeneratorService()
        result = service.generate("PAD_S3E10.mp4")

        assert "Poker After Dark" in result.display_title
        assert result.metadata.project_code == ProjectCode.PAD

    def test_generate_fallback(self):
        """패턴 미매칭 시 Fallback"""
        service = TitleGeneratorService()
        result = service.generate("random_poker_video.mp4")

        assert result.display_title == "random poker video"
        assert result.confidence < 0.5

    def test_generate_with_path(self):
        """경로 정보 활용"""
        service = TitleGeneratorService()
        # 파일명 자체가 매칭되는 경우에만 경로 보강이 동작
        result = service.generate(
            "WSOP_2024_Event5_Day1.mp4",
            file_path="/nas/videos/WSOP/2024/WSOP_2024_Event5_Day1.mp4",
        )

        # 경로에서 프로젝트 코드와 연도 추출
        assert result.metadata.project_code == ProjectCode.WSOP
        assert result.metadata.year == 2024

    def test_parse_metadata(self):
        """메타데이터만 파싱"""
        service = TitleGeneratorService()
        result = service.parse_metadata("WSOP_2024_Event5_Day1.mp4")

        assert result.project_code == ProjectCode.WSOP
        assert result.year == 2024
        assert result.event_number == 5

    def test_extract_project_from_path(self):
        """경로에서 프로젝트 추출"""
        service = TitleGeneratorService()

        assert (
            service.extract_project_from_path("/nas/videos/WSOP/2024/event.mp4")
            == ProjectCode.WSOP
        )
        assert (
            service.extract_project_from_path("/nas/HCL/season12/ep5.mp4")
            == ProjectCode.HCL
        )
        assert (
            service.extract_project_from_path("/nas/random/video.mp4")
            == ProjectCode.OTHER
        )

    def test_batch_generate(self):
        """배치 제목 생성"""
        service = TitleGeneratorService()
        files = [
            {"file_name": "WSOP_2024_Event5_Day1.mp4"},
            {"file_name": "HCL_S12E05.mp4"},
            {"file_name": "random.mp4"},
        ]
        results = service.batch_generate(files)

        assert len(results) == 3
        assert results[0].metadata.project_code == ProjectCode.WSOP
        assert results[1].metadata.project_code == ProjectCode.HCL
        assert results[2].confidence < 0.5

    def test_short_title_generation(self):
        """축약 제목 생성"""
        service = TitleGeneratorService()
        result = service.generate(
            "WSOP_2024_MainEvent_Day1_Part1_FeatureTable_ExtendedCoverage.mp4"
        )

        # 축약 제목은 원본보다 짧거나 같아야 함
        assert len(result.short_title) <= 50


class TestPatternPriority:
    """패턴 우선순위 테스트"""

    def test_more_specific_pattern_wins(self):
        """구체적인 패턴이 우선"""
        registry = PatternRegistry()

        # 구체적인 패턴 (event_day_part)
        result1 = registry.match("WSOP_2024_Event5_Day1_Part2.mp4")
        # 덜 구체적인 패턴 (generic)
        result2 = registry.match("WSOP_2024_SomeEvent.mp4")

        assert result1 is not None
        assert result2 is not None
        # 구체적인 패턴이 더 높은 신뢰도
        assert result1[0].confidence >= result2[0].confidence


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_filename(self):
        """빈 파일명"""
        service = TitleGeneratorService()
        result = service.generate("")

        assert result.confidence < 0.5

    def test_special_characters(self):
        """특수 문자 포함"""
        service = TitleGeneratorService()
        result = service.generate("WSOP_2024_Event#5_(Day1).mp4")

        # 파싱은 실패할 수 있지만 에러 없이 처리
        assert result is not None

    def test_unicode_filename(self):
        """유니코드 파일명"""
        service = TitleGeneratorService()
        result = service.generate("WSOP_2024_이벤트5.mp4")

        assert result is not None

    def test_very_long_filename(self):
        """매우 긴 파일명"""
        service = TitleGeneratorService()
        long_name = "WSOP_2024_" + "A" * 200 + ".mp4"
        result = service.generate(long_name)

        # 축약 제목은 적절한 길이로 제한
        assert len(result.short_title) <= 50
