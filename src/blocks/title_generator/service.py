"""
Block G: Title Generator - 서비스

파일명을 분석하여 Netflix 스타일의 표시 제목을 생성하는 핵심 서비스.
"""

from __future__ import annotations

from pathlib import Path

from src.blocks.title_generator.models import (
    ContentType,
    GeneratedTitle,
    ParsedMetadata,
    ProjectCode,
)
from src.blocks.title_generator.patterns import (
    PatternRegistry,
    get_pattern_registry,
)


class TitleGeneratorService:
    """
    Title Generator 핵심 서비스

    파일명을 분석하여 표시 제목과 메타데이터를 생성.
    Block G의 모든 기능을 제공.
    """

    def __init__(self, registry: PatternRegistry | None = None) -> None:
        """
        서비스 초기화

        Args:
            registry: 패턴 레지스트리 (None이면 기본 레지스트리 사용)
        """
        self._registry = registry or get_pattern_registry()

    def generate(
        self,
        file_name: str,
        file_path: str | None = None,
    ) -> GeneratedTitle:
        """
        파일명에서 표시 제목 생성

        Args:
            file_name: 파일명 (예: "WSOP_2024_Event5_Day1.mp4")
            file_path: 파일 경로 (선택, 추가 컨텍스트 제공)

        Returns:
            GeneratedTitle: 생성된 제목 및 메타데이터
        """
        # 패턴 매칭 시도
        match_result = self._registry.match(file_name)

        if match_result is None:
            # 매칭 실패 시 Fallback
            result = GeneratedTitle.fallback(file_name)
            # 경로에서 프로젝트/연도 추출 시도
            if file_path:
                self._enrich_from_path(result.metadata, file_path)
            return result

        pattern, match = match_result

        # 제목 포맷팅
        display_title = PatternRegistry.format_title(pattern.title_template, match)

        # 메타데이터 추출
        metadata = self._extract_metadata(match, pattern.project)

        # 경로에서 추가 정보 추출
        if file_path:
            self._enrich_from_path(metadata, file_path)

        # 축약 제목 생성
        short_title = self._generate_short_title(display_title)

        return GeneratedTitle(
            display_title=display_title,
            short_title=short_title,
            confidence=pattern.confidence,
            metadata=metadata,
        )

    def parse_metadata(self, file_name: str) -> ParsedMetadata:
        """
        파일명에서 메타데이터만 추출

        Args:
            file_name: 파일명

        Returns:
            ParsedMetadata: 추출된 메타데이터
        """
        match_result = self._registry.match(file_name)

        if match_result is None:
            return ParsedMetadata()

        pattern, match = match_result
        return self._extract_metadata(match, pattern.project)

    def _extract_metadata(
        self,
        match,
        project: ProjectCode,
    ) -> ParsedMetadata:
        """매칭 결과에서 메타데이터 추출"""
        groups = match.groupdict()

        metadata = ParsedMetadata(project_code=project)

        # 연도
        if "year" in groups and groups["year"]:
            try:
                metadata.year = int(groups["year"])
            except ValueError:
                pass

        # 이벤트 번호
        if "event" in groups and groups["event"]:
            try:
                metadata.event_number = int(groups["event"])
            except ValueError:
                pass

        # 이벤트 이름
        if "event_name" in groups and groups["event_name"]:
            metadata.event_name = groups["event_name"].replace("_", " ").strip()

        # 에피소드 번호
        if "episode" in groups and groups["episode"]:
            try:
                metadata.episode_number = int(groups["episode"])
            except ValueError:
                pass

        # 시즌 번호
        if "season" in groups and groups["season"]:
            try:
                metadata.season_number = int(groups["season"])
            except ValueError:
                pass

        # 일차 (Day)
        if "day" in groups and groups["day"]:
            try:
                metadata.day_number = int(groups["day"])
            except ValueError:
                pass

        # 파트 번호
        if "part" in groups and groups["part"]:
            try:
                metadata.part_number = int(groups["part"])
            except ValueError:
                pass

        # 바이인
        if "buyin" in groups and groups["buyin"]:
            metadata.buy_in = PatternRegistry.parse_buy_in(groups["buyin"])

        # 게임 타입
        if "game" in groups and groups["game"]:
            metadata.game_type = PatternRegistry.parse_game_type(groups["game"])

        # 콘텐츠 타입 추론
        if "stage" in groups and groups["stage"]:
            stage = groups["stage"].upper()
            if "FINAL" in stage or stage == "FT":
                metadata.content_type = ContentType.FINAL_TABLE
            elif "HEADSUP" in stage or "HEADS" in stage:
                metadata.content_type = ContentType.HEADS_UP

        return metadata

    def _enrich_from_path(self, metadata: ParsedMetadata, file_path: str) -> None:
        """파일 경로에서 추가 정보 추출"""
        import re
        # Windows/Linux 경로 호환성: 백슬래시를 슬래시로 변환 후 분할
        normalized_path = file_path.replace("\\", "/")
        path = Path(normalized_path)
        parts = path.parts

        # 프로젝트 코드가 없거나 OTHER이면 경로에서 추출
        if metadata.project_code is None or metadata.project_code == ProjectCode.OTHER:
            # 폴더명과 ProjectCode 매핑
            folder_mapping = {
                "WSOP": ProjectCode.WSOP,
                "HCL": ProjectCode.HCL,
                "GGMILLIONS": ProjectCode.GGMILLIONS,
                "GOG": ProjectCode.GOG,
                "MPP": ProjectCode.MPP,
                "PAD": ProjectCode.PAD,
            }
            for part in parts:
                # 정규화: 공백, 특수문자 제거 후 대문자 변환
                normalized = re.sub(r'[^A-Za-z0-9]', '', part).upper()
                if normalized in folder_mapping:
                    metadata.project_code = folder_mapping[normalized]
                    break
                # "GOG 최종" 같은 케이스 처리
                if normalized.startswith("GOG"):
                    metadata.project_code = ProjectCode.GOG
                    break

        # 연도가 없으면 경로와 파일명에서 추출
        if metadata.year is None:
            full_path = str(path)
            # 4자리 연도 패턴 (2000-2099)
            year_match = re.search(r'20[0-9]{2}', full_path)
            if year_match:
                metadata.year = int(year_match.group())
            else:
                # YYMMDD 형식에서 연도 추출 (25XXXX = 2025)
                yymmdd_match = re.search(r'\b(2[0-5])(\d{2})(\d{2})\b', path.stem)
                if yymmdd_match:
                    yy = int(yymmdd_match.group(1))
                    metadata.year = 2000 + yy

    def _generate_short_title(self, display_title: str, max_length: int = 40) -> str:
        """축약 제목 생성"""
        if len(display_title) <= max_length:
            return display_title

        # 하이픈 이후 부분 생략
        if " - " in display_title:
            parts = display_title.split(" - ")
            short = parts[0]
            if len(short) <= max_length:
                return short

        # 단순 잘라내기
        return display_title[: max_length - 3] + "..."

    def extract_project_from_path(self, file_path: str) -> ProjectCode:
        """
        파일 경로에서 프로젝트 코드 추출

        /nas/videos/WSOP/2024/event.mp4 → ProjectCode.WSOP
        """
        path = Path(file_path)
        parts = path.parts

        known_projects = {p.value for p in ProjectCode if p != ProjectCode.OTHER}

        for part in parts:
            upper = part.upper()
            if upper in known_projects:
                return ProjectCode(upper)

        return ProjectCode.OTHER

    def batch_generate(
        self,
        files: list[dict[str, str]],
    ) -> list[GeneratedTitle]:
        """
        배치 제목 생성

        Args:
            files: [{"file_name": "...", "file_path": "..."}] 형식의 리스트

        Returns:
            GeneratedTitle 리스트
        """
        results = []
        for file_info in files:
            file_name = file_info.get("file_name", "")
            file_path = file_info.get("file_path")
            results.append(self.generate(file_name, file_path))
        return results


# 싱글톤 인스턴스
_service: TitleGeneratorService | None = None


def get_title_generator_service() -> TitleGeneratorService:
    """TitleGeneratorService 싱글톤 반환"""
    global _service
    if _service is None:
        _service = TitleGeneratorService()
    return _service
