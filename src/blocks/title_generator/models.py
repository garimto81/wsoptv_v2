"""
Block G: Title Generator - 데이터 모델

파일명 파싱 결과 및 생성된 제목을 표현하는 데이터클래스.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any


class ProjectCode(str, Enum):
    """포커 시리즈 프로젝트 코드"""

    WSOP = "WSOP"
    HCL = "HCL"
    GGMILLIONS = "GGMILLIONS"
    GOG = "GOG"
    MPP = "MPP"
    PAD = "PAD"
    OTHER = "OTHER"

    @classmethod
    def from_string(cls, value: str) -> ProjectCode:
        """문자열에서 ProjectCode 변환 (대소문자 무시)"""
        normalized = value.upper().replace(" ", "").replace("_", "")
        for member in cls:
            if member.value == normalized:
                return member
            # 별칭 처리
            aliases = {
                "WORLDSERIESOFPOKER": cls.WSOP,
                "HIGHCARDLINEUP": cls.HCL,
                "HIGHCARDLlineup": cls.HCL,
                "GGPOKERMILLIONS": cls.GGMILLIONS,
                "GAMEOFGOLD": cls.GOG,
                "MYSTERYPOKERPLAYERS": cls.MPP,
                "POKERAFTERDARK": cls.PAD,
            }
            if normalized in aliases:
                return aliases[normalized]
        return cls.OTHER


class ContentType(str, Enum):
    """콘텐츠 유형"""

    MAIN_TABLE = "main_table"
    FEATURE_TABLE = "feature_table"
    FINAL_TABLE = "final_table"
    HEADS_UP = "heads_up"
    CASH_GAME = "cash_game"
    TOURNAMENT = "tournament"
    HIGHLIGHT = "highlight"
    INTERVIEW = "interview"
    OTHER = "other"


class GameType(str, Enum):
    """포커 게임 유형"""

    NLHE = "No-Limit Hold'em"
    PLO = "Pot-Limit Omaha"
    PLO5 = "5-Card PLO"
    MIXED = "Mixed Games"
    STUD = "Stud"
    RAZZ = "Razz"
    HORSE = "H.O.R.S.E."
    OTHER = "Other"


@dataclass
class ParsedMetadata:
    """
    파일명에서 추출된 메타데이터

    파일명을 분석하여 다양한 정보를 추출한 결과.
    None 값은 해당 정보를 추출하지 못했음을 의미.
    """

    project_code: ProjectCode | None = None
    year: int | None = None
    event_number: int | None = None
    event_name: str | None = None
    episode_number: int | None = None
    season_number: int | None = None
    day_number: int | None = None
    part_number: int | None = None
    game_type: GameType | None = None
    buy_in: Decimal | None = None
    content_type: ContentType | None = None
    extra_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "project_code": self.project_code.value if self.project_code else None,
            "year": self.year,
            "event_number": self.event_number,
            "event_name": self.event_name,
            "episode_number": self.episode_number,
            "season_number": self.season_number,
            "day_number": self.day_number,
            "part_number": self.part_number,
            "game_type": self.game_type.value if self.game_type else None,
            "buy_in": str(self.buy_in) if self.buy_in else None,
            "content_type": self.content_type.value if self.content_type else None,
            "extra_tags": self.extra_tags,
        }


@dataclass
class GeneratedTitle:
    """
    생성된 표시 제목

    파일명을 분석하여 사람이 읽기 좋은 제목으로 변환한 결과.
    """

    display_title: str  # 전체 표시 제목
    short_title: str  # 축약 제목 (UI용)
    confidence: float  # 파싱 신뢰도 (0.0 ~ 1.0)
    metadata: ParsedMetadata  # 추출된 메타데이터

    def __post_init__(self) -> None:
        """신뢰도 값 검증"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "display_title": self.display_title,
            "short_title": self.short_title,
            "confidence": self.confidence,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def fallback(cls, file_name: str) -> GeneratedTitle:
        """
        패턴 매칭 실패 시 Fallback 제목 생성

        파일 확장자를 제거하고 언더스코어를 공백으로 변환.
        """
        # 확장자 제거
        name = file_name
        for ext in [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"]:
            if name.lower().endswith(ext):
                name = name[: -len(ext)]
                break

        # 언더스코어/하이픈을 공백으로
        display_title = name.replace("_", " ").replace("-", " ")

        return cls(
            display_title=display_title,
            short_title=display_title[:50] if len(display_title) > 50 else display_title,
            confidence=0.1,  # 낮은 신뢰도
            metadata=ParsedMetadata(),
        )
