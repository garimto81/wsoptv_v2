"""
Block G: Title Generator - 패턴 레지스트리

시리즈별 파일명 패턴을 정의하고 매칭하는 모듈.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from src.blocks.title_generator.models import (
    GameType,
    ProjectCode,
)


@dataclass
class TitlePattern:
    """제목 파싱 패턴"""

    name: str  # 패턴 이름 (디버깅용)
    project: ProjectCode  # 대상 프로젝트
    regex: re.Pattern[str]  # 정규식 패턴
    priority: int  # 우선순위 (높을수록 먼저 매칭)
    confidence: float  # 매칭 시 기본 신뢰도
    title_template: str  # 제목 템플릿 (f-string 형식)


class PatternRegistry:
    """
    패턴 레지스트리

    시리즈별 파일명 패턴을 관리하고 매칭을 수행.
    """

    def __init__(self) -> None:
        self._patterns: list[TitlePattern] = []
        self._register_default_patterns()

    def _register_default_patterns(self) -> None:
        """기본 패턴 등록"""
        # WSOP 패턴들
        self._register_wsop_patterns()
        # HCL 패턴들
        self._register_hcl_patterns()
        # GGMillions 패턴들
        self._register_ggmillions_patterns()
        # GOG 패턴들
        self._register_gog_patterns()
        # MPP 패턴들
        self._register_mpp_patterns()
        # PAD 패턴들
        self._register_pad_patterns()

        # 우선순위로 정렬
        self._patterns.sort(key=lambda p: -p.priority)

    def _register_wsop_patterns(self) -> None:
        """WSOP (World Series of Poker) 패턴"""
        patterns = [
            # WSOP_2024_Event5_Day1_Part2.mp4
            TitlePattern(
                name="wsop_event_day_part",
                project=ProjectCode.WSOP,
                regex=re.compile(
                    r"WSOP[_\s-]*(?P<year>\d{4})[_\s-]*"
                    r"Event[_\s-]*(?P<event>\d+)[_\s-]*"
                    r"Day[_\s-]*(?P<day>\d+)"
                    r"(?:[_\s-]*Part[_\s-]*(?P<part>\d+))?",
                    re.IGNORECASE,
                ),
                priority=100,
                confidence=0.95,
                title_template="WSOP {year} Event #{event} - Day {day}{part_suffix}",
            ),
            # WSOP_2024_MainEvent_FinalTable.mp4
            TitlePattern(
                name="wsop_main_event",
                project=ProjectCode.WSOP,
                regex=re.compile(
                    r"WSOP[_\s-]*(?P<year>\d{4})[_\s-]*"
                    r"Main[_\s-]*Event[_\s-]*"
                    r"(?P<stage>FinalTable|FT|Day\d+|HeadsUp)?",
                    re.IGNORECASE,
                ),
                priority=95,
                confidence=0.95,
                title_template="WSOP {year} Main Event{stage_suffix}",
            ),
            # WSOP_Bracelet_2024_Event10.mp4
            TitlePattern(
                name="wsop_bracelet",
                project=ProjectCode.WSOP,
                regex=re.compile(
                    r"WSOP[_\s-]*Bracelet[_\s-]*(?P<year>\d{4})[_\s-]*"
                    r"Event[_\s-]*(?P<event>\d+)",
                    re.IGNORECASE,
                ),
                priority=90,
                confidence=0.9,
                title_template="WSOP {year} Bracelet Event #{event}",
            ),
            # WSOP_2024_10K_NLHE.mp4 (buy-in based)
            TitlePattern(
                name="wsop_buyin",
                project=ProjectCode.WSOP,
                regex=re.compile(
                    r"WSOP[_\s-]*(?P<year>\d{4})[_\s-]*"
                    r"(?P<buyin>\d+)[Kk][_\s-]*"
                    r"(?P<game>NLHE|PLO|PLO5|HORSE|MIXED)?",
                    re.IGNORECASE,
                ),
                priority=85,
                confidence=0.85,
                title_template="WSOP {year} ${buyin}K {game}",
            ),
            # 일반 WSOP 패턴
            TitlePattern(
                name="wsop_generic",
                project=ProjectCode.WSOP,
                regex=re.compile(
                    r"WSOP[_\s-]*(?P<year>\d{4})?[_\s-]*(?P<rest>.*)",
                    re.IGNORECASE,
                ),
                priority=50,
                confidence=0.7,
                title_template="WSOP{year_suffix}{rest_suffix}",
            ),
        ]
        self._patterns.extend(patterns)

    def _register_hcl_patterns(self) -> None:
        """HCL (High Card Lineup / Hustler Casino Live) 패턴"""
        patterns = [
            # HCL_S12E05_HighStakes.mp4
            TitlePattern(
                name="hcl_season_episode",
                project=ProjectCode.HCL,
                regex=re.compile(
                    r"HCL[_\s-]*S(?P<season>\d+)E(?P<episode>\d+)"
                    r"(?:[_\s-]*(?P<title>[\w\s]+))?",
                    re.IGNORECASE,
                ),
                priority=100,
                confidence=0.95,
                title_template="HCL Season {season} Episode {episode}{title_suffix}",
            ),
            # HighCardLineup_Episode_25.mp4
            TitlePattern(
                name="hcl_episode_only",
                project=ProjectCode.HCL,
                regex=re.compile(
                    r"(?:High[_\s-]*Card[_\s-]*Lineup|HCL)[_\s-]*"
                    r"Episode[_\s-]*(?P<episode>\d+)",
                    re.IGNORECASE,
                ),
                priority=90,
                confidence=0.9,
                title_template="HCL Episode {episode}",
            ),
            # HCL_2024_MilionDollarGame.mp4
            TitlePattern(
                name="hcl_special",
                project=ProjectCode.HCL,
                regex=re.compile(
                    r"HCL[_\s-]*(?P<year>\d{4})?[_\s-]*"
                    r"(?P<special>Million[_\s-]*Dollar|High[_\s-]*Stakes|"
                    r"All[_\s-]*In|Super[_\s-]*High[_\s-]*Roller)",
                    re.IGNORECASE,
                ),
                priority=85,
                confidence=0.85,
                title_template="HCL{year_suffix} {special}",
            ),
            # 일반 HCL
            TitlePattern(
                name="hcl_generic",
                project=ProjectCode.HCL,
                regex=re.compile(
                    r"(?:High[_\s-]*Card[_\s-]*Lineup|HCL)[_\s-]*(?P<rest>.*)",
                    re.IGNORECASE,
                ),
                priority=50,
                confidence=0.7,
                title_template="HCL{rest_suffix}",
            ),
        ]
        self._patterns.extend(patterns)

    def _register_ggmillions_patterns(self) -> None:
        """GGMillions 패턴"""
        patterns = [
            # GGMillions_SuperHighRoller_2024_FT.mp4
            TitlePattern(
                name="ggmillions_shr",
                project=ProjectCode.GGMILLIONS,
                regex=re.compile(
                    r"GG[_\s-]*(?:Poker[_\s-]*)?Millions[_\s-]*"
                    r"(?P<event>Super[_\s-]*High[_\s-]*Roller|SHR|Main[_\s-]*Event)[_\s-]*"
                    r"(?P<year>\d{4})?[_\s-]*"
                    r"(?P<stage>FT|Final[_\s-]*Table|Day\d+)?",
                    re.IGNORECASE,
                ),
                priority=100,
                confidence=0.95,
                title_template="GGMillions {event}{year_suffix}{stage_suffix}",
            ),
            # GGMillions_Event5_2024.mp4
            TitlePattern(
                name="ggmillions_event",
                project=ProjectCode.GGMILLIONS,
                regex=re.compile(
                    r"GG[_\s-]*(?:Poker[_\s-]*)?Millions[_\s-]*"
                    r"Event[_\s-]*(?P<event>\d+)[_\s-]*"
                    r"(?P<year>\d{4})?",
                    re.IGNORECASE,
                ),
                priority=90,
                confidence=0.9,
                title_template="GGMillions Event #{event}{year_suffix}",
            ),
            # 일반 GGMillions
            TitlePattern(
                name="ggmillions_generic",
                project=ProjectCode.GGMILLIONS,
                regex=re.compile(
                    r"GG[_\s-]*(?:Poker[_\s-]*)?Millions[_\s-]*(?P<rest>.*)",
                    re.IGNORECASE,
                ),
                priority=50,
                confidence=0.7,
                title_template="GGMillions{rest_suffix}",
            ),
        ]
        self._patterns.extend(patterns)

    def _register_gog_patterns(self) -> None:
        """GOG (Game of Gold) 패턴"""
        patterns = [
            # GOG_S1E5.mp4
            TitlePattern(
                name="gog_season_episode",
                project=ProjectCode.GOG,
                regex=re.compile(
                    r"(?:Game[_\s-]*of[_\s-]*Gold|GOG)[_\s-]*"
                    r"S(?P<season>\d+)E(?P<episode>\d+)",
                    re.IGNORECASE,
                ),
                priority=100,
                confidence=0.95,
                title_template="Game of Gold S{season}E{episode}",
            ),
            # GOG_Episode_10.mp4
            TitlePattern(
                name="gog_episode",
                project=ProjectCode.GOG,
                regex=re.compile(
                    r"(?:Game[_\s-]*of[_\s-]*Gold|GOG)[_\s-]*"
                    r"Episode[_\s-]*(?P<episode>\d+)",
                    re.IGNORECASE,
                ),
                priority=90,
                confidence=0.9,
                title_template="Game of Gold Episode {episode}",
            ),
            # 일반 GOG
            TitlePattern(
                name="gog_generic",
                project=ProjectCode.GOG,
                regex=re.compile(
                    r"(?:Game[_\s-]*of[_\s-]*Gold|GOG)[_\s-]*(?P<rest>.*)",
                    re.IGNORECASE,
                ),
                priority=50,
                confidence=0.7,
                title_template="Game of Gold{rest_suffix}",
            ),
        ]
        self._patterns.extend(patterns)

    def _register_mpp_patterns(self) -> None:
        """MPP (Mystery Poker Players / ?) 패턴"""
        patterns = [
            # MPP_2024_Event5.mp4
            TitlePattern(
                name="mpp_event",
                project=ProjectCode.MPP,
                regex=re.compile(
                    r"MPP[_\s-]*(?P<year>\d{4})?[_\s-]*"
                    r"Event[_\s-]*(?P<event>\d+)",
                    re.IGNORECASE,
                ),
                priority=100,
                confidence=0.9,
                title_template="MPP{year_suffix} Event #{event}",
            ),
            # 일반 MPP
            TitlePattern(
                name="mpp_generic",
                project=ProjectCode.MPP,
                regex=re.compile(r"MPP[_\s-]*(?P<rest>.*)", re.IGNORECASE),
                priority=50,
                confidence=0.7,
                title_template="MPP{rest_suffix}",
            ),
        ]
        self._patterns.extend(patterns)

    def _register_pad_patterns(self) -> None:
        """PAD (Poker After Dark) 패턴"""
        patterns = [
            # PAD_S3E10.mp4
            TitlePattern(
                name="pad_season_episode",
                project=ProjectCode.PAD,
                regex=re.compile(
                    r"(?:Poker[_\s-]*After[_\s-]*Dark|PAD)[_\s-]*"
                    r"S(?P<season>\d+)E(?P<episode>\d+)",
                    re.IGNORECASE,
                ),
                priority=100,
                confidence=0.95,
                title_template="Poker After Dark S{season}E{episode}",
            ),
            # PokerAfterDark_Week5_2024.mp4
            TitlePattern(
                name="pad_week",
                project=ProjectCode.PAD,
                regex=re.compile(
                    r"(?:Poker[_\s-]*After[_\s-]*Dark|PAD)[_\s-]*"
                    r"Week[_\s-]*(?P<week>\d+)[_\s-]*"
                    r"(?P<year>\d{4})?",
                    re.IGNORECASE,
                ),
                priority=90,
                confidence=0.9,
                title_template="Poker After Dark Week {week}{year_suffix}",
            ),
            # 일반 PAD
            TitlePattern(
                name="pad_generic",
                project=ProjectCode.PAD,
                regex=re.compile(
                    r"(?:Poker[_\s-]*After[_\s-]*Dark|PAD)[_\s-]*(?P<rest>.*)",
                    re.IGNORECASE,
                ),
                priority=50,
                confidence=0.7,
                title_template="Poker After Dark{rest_suffix}",
            ),
        ]
        self._patterns.extend(patterns)

    def register(self, pattern: TitlePattern) -> None:
        """패턴 등록"""
        self._patterns.append(pattern)
        self._patterns.sort(key=lambda p: -p.priority)

    def match(self, file_name: str) -> tuple[TitlePattern, re.Match[str]] | None:
        """
        파일명에 매칭되는 패턴 검색

        우선순위가 높은 패턴부터 시도하여 첫 번째 매칭을 반환.
        """
        for pattern in self._patterns:
            match = pattern.regex.search(file_name)
            if match:
                return (pattern, match)
        return None

    def get_patterns_for_project(self, project: ProjectCode) -> list[TitlePattern]:
        """프로젝트별 패턴 목록 조회"""
        return [p for p in self._patterns if p.project == project]

    @staticmethod
    def format_title(template: str, match: re.Match[str]) -> str:
        """
        템플릿과 매칭 결과로 제목 포맷팅

        suffix 변수들을 자동으로 처리.
        """
        groups = match.groupdict()
        format_vars: dict[str, str] = {}

        for key, value in groups.items():
            if value is not None:
                # 기본 값
                format_vars[key] = value

                # suffix 버전 추가
                if key in ("year", "part", "stage", "title", "rest", "special"):
                    suffix_key = f"{key}_suffix"
                    if key == "year":
                        format_vars[suffix_key] = f" {value}"
                    elif key == "part":
                        format_vars[suffix_key] = f" Part {value}"
                    elif key == "stage":
                        # FinalTable/FT 등을 보기 좋게
                        stage = value.replace("_", " ").replace("-", " ")
                        if stage.upper() == "FT":
                            stage = "Final Table"
                        format_vars[suffix_key] = f" - {stage}"
                    elif key == "title":
                        format_vars[suffix_key] = f" - {value.strip()}"
                    elif key == "rest":
                        rest = value.strip().replace("_", " ").replace("-", " ")
                        format_vars[suffix_key] = f" {rest}" if rest else ""
                    elif key == "special":
                        special = value.replace("_", " ").replace("-", " ")
                        format_vars[suffix_key] = special
            else:
                # None인 경우 빈 문자열로 suffix 설정
                format_vars[key] = ""
                format_vars[f"{key}_suffix"] = ""

        # 템플릿 포맷팅
        try:
            return template.format(**format_vars).strip()
        except KeyError:
            # 포맷팅 실패 시 원본 템플릿 반환
            return template

    @staticmethod
    def parse_buy_in(value: str) -> Decimal | None:
        """바이인 문자열 파싱 (예: "10K" → 10000)"""
        if not value:
            return None

        value = value.upper().replace(",", "").replace("$", "")

        multiplier = Decimal(1)
        if value.endswith("K"):
            multiplier = Decimal(1000)
            value = value[:-1]
        elif value.endswith("M"):
            multiplier = Decimal(1000000)
            value = value[:-1]

        try:
            return Decimal(value) * multiplier
        except Exception:
            return None

    @staticmethod
    def parse_game_type(value: str | None) -> GameType | None:
        """게임 타입 문자열 파싱"""
        if not value:
            return None

        value = value.upper().replace(" ", "").replace("-", "").replace("_", "")

        mapping = {
            "NLHE": GameType.NLHE,
            "NOLIMITHOLDEM": GameType.NLHE,
            "PLO": GameType.PLO,
            "POTLIMITOMAHA": GameType.PLO,
            "PLO5": GameType.PLO5,
            "5CARDPLO": GameType.PLO5,
            "MIXED": GameType.MIXED,
            "MIXEDGAMES": GameType.MIXED,
            "STUD": GameType.STUD,
            "RAZZ": GameType.RAZZ,
            "HORSE": GameType.HORSE,
        }

        return mapping.get(value, GameType.OTHER)


# 싱글톤 인스턴스
_registry: PatternRegistry | None = None


def get_pattern_registry() -> PatternRegistry:
    """패턴 레지스트리 싱글톤 반환"""
    global _registry
    if _registry is None:
        _registry = PatternRegistry()
    return _registry
