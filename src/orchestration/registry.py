"""
Block Registry - 블럭 등록 및 의존성 관리

모든 블럭은 이곳에 등록되어야 하며, 의존성 검증을 통과해야 활성화됨.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any


class BlockStatus(Enum):
    """블럭 상태"""

    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    STOPPED = "stopped"


@dataclass
class BlockInfo:
    """블럭 정보"""

    block_id: str
    version: str
    provides: list[str]  # 이 블럭이 제공하는 기능 목록
    requires: list[str]  # 이 블럭이 필요로 하는 기능 목록 (block.function 형식)
    status: BlockStatus = BlockStatus.INITIALIZING
    registered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_health_check: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_required_blocks(self) -> set[str]:
        """의존하는 블럭 ID 목록"""
        return {req.split(".")[0] for req in self.requires}


class BlockRegistry:
    """
    블럭 레지스트리

    - 블럭 등록/해제
    - 의존성 검증
    - 헬스 체크 관리
    """

    def __init__(self) -> None:
        self._blocks: dict[str, BlockInfo] = {}
        self._provided_functions: dict[str, str] = {}  # function -> block_id

    def register(self, block: BlockInfo) -> None:
        """
        블럭 등록

        Args:
            block: 등록할 블럭 정보

        Raises:
            ValueError: 이미 등록된 블럭이거나 의존성 미충족 시
        """
        if block.block_id in self._blocks:
            raise ValueError(f"Block '{block.block_id}' is already registered")

        if not self.can_register(block):
            missing = self._get_missing_dependencies(block)
            raise ValueError(
                f"Cannot register '{block.block_id}': missing dependencies {missing}"
            )

        self._blocks[block.block_id] = block

        # 제공 기능 등록
        for func in block.provides:
            full_name = f"{block.block_id}.{func}"
            self._provided_functions[full_name] = block.block_id

        # 상태를 healthy로 변경
        block.status = BlockStatus.HEALTHY
        block.last_health_check = datetime.now(UTC)

    def unregister(self, block_id: str) -> None:
        """블럭 등록 해제"""
        if block_id not in self._blocks:
            return

        block = self._blocks[block_id]

        # 다른 블럭이 이 블럭에 의존하는지 확인
        dependents = self._get_dependent_blocks(block_id)
        if dependents:
            raise ValueError(
                f"Cannot unregister '{block_id}': required by {dependents}"
            )

        # 제공 기능 제거
        for func in block.provides:
            full_name = f"{block.block_id}.{func}"
            self._provided_functions.pop(full_name, None)

        del self._blocks[block_id]

    def get_block(self, block_id: str) -> BlockInfo | None:
        """블럭 정보 조회"""
        return self._blocks.get(block_id)

    def can_register(self, block: BlockInfo) -> bool:
        """의존성 충족 여부 확인"""
        return len(self._get_missing_dependencies(block)) == 0

    def _get_missing_dependencies(self, block: BlockInfo) -> list[str]:
        """누락된 의존성 목록"""
        missing = []
        for req in block.requires:
            if req not in self._provided_functions:
                missing.append(req)
        return missing

    def _get_dependent_blocks(self, block_id: str) -> list[str]:
        """이 블럭에 의존하는 블럭 목록"""
        dependents = []
        for other_id, other_block in self._blocks.items():
            if other_id == block_id:
                continue
            if block_id in other_block.get_required_blocks():
                dependents.append(other_id)
        return dependents

    def is_healthy(self, block_id: str) -> bool:
        """블럭 헬스 상태 확인"""
        block = self._blocks.get(block_id)
        if block is None:
            return False
        return block.status == BlockStatus.HEALTHY

    def update_health(self, block_id: str, status: BlockStatus) -> None:
        """블럭 헬스 상태 업데이트"""
        if block_id in self._blocks:
            self._blocks[block_id].status = status
            self._blocks[block_id].last_health_check = datetime.now(UTC)

    def get_all_blocks(self) -> list[BlockInfo]:
        """모든 등록된 블럭 목록"""
        return list(self._blocks.values())

    def get_dependency_order(self) -> list[str]:
        """
        의존성 순서로 정렬된 블럭 ID 목록

        L0 (무의존) 블럭부터 시작하여 의존성 순서대로 반환.
        """
        result: list[str] = []
        remaining = set(self._blocks.keys())

        while remaining:
            # 현재 result에 의존성이 모두 충족된 블럭 찾기
            ready = []
            for block_id in remaining:
                block = self._blocks[block_id]
                required_blocks = block.get_required_blocks()
                if required_blocks.issubset(set(result)):
                    ready.append(block_id)

            if not ready:
                # 순환 의존성 감지
                raise ValueError(f"Circular dependency detected: {remaining}")

            result.extend(sorted(ready))  # 정렬하여 일관성 유지
            remaining -= set(ready)

        return result
