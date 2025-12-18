"""
Block G: Title Generator

파일명을 분석하여 Netflix 스타일의 표시 제목을 생성하는 블럭.
"""

from src.blocks.title_generator.models import (
    GeneratedTitle,
    ParsedMetadata,
    ProjectCode,
)
from src.blocks.title_generator.service import TitleGeneratorService
from src.blocks.title_generator.patterns import PatternRegistry

__all__ = [
    "GeneratedTitle",
    "ParsedMetadata",
    "ProjectCode",
    "TitleGeneratorService",
    "PatternRegistry",
]
