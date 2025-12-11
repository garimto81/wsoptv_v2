"""
Block Isolation - 블럭 격리 및 코드 오염 방지

핵심 규칙:
1. 블럭 간 직접 import 금지
2. 모든 통신은 orchestration을 통해서만
3. 각 블럭은 독립적인 컨텍스트 유지
"""

from __future__ import annotations

from typing import Any


class ImportChecker:
    """
    Import 규칙 검증기

    블럭 간 직접 import를 방지하여 코드 오염 차단.
    """

    # 항상 허용되는 경로
    ALWAYS_ALLOWED = [
        "src.orchestration",
        "src.common",
        "src.shared",
    ]

    def __init__(self) -> None:
        self._violations: list[dict[str, str]] = []

    def is_allowed_import(self, from_block: str, import_path: str) -> bool:
        """
        Import 허용 여부 확인

        규칙:
        1. 자기 블럭 내 import: 허용
        2. orchestration import: 허용
        3. 다른 블럭 직접 import: 금지

        Args:
            from_block: import를 시도하는 블럭 ID
            import_path: import 경로 (예: "src.blocks.auth.models")

        Returns:
            허용 여부
        """
        # orchestration, common은 항상 허용
        for allowed in self.ALWAYS_ALLOWED:
            if import_path.startswith(allowed):
                return True

        # 블럭 경로 분석
        if not import_path.startswith("src.blocks."):
            return True  # 블럭이 아닌 경로는 허용

        # src.blocks.{block_id}.* 형식에서 block_id 추출
        parts = import_path.split(".")
        if len(parts) < 3:
            return True

        target_block = parts[2]

        # 자기 블럭이면 허용
        if target_block == from_block:
            return True

        # 다른 블럭 직접 import는 금지
        self._violations.append(
            {
                "from_block": from_block,
                "import_path": import_path,
                "target_block": target_block,
            }
        )
        return False

    def get_violations(self) -> list[dict[str, str]]:
        """위반 목록 반환"""
        return self._violations.copy()

    def clear_violations(self) -> None:
        """위반 목록 초기화"""
        self._violations.clear()


class BlockContext:
    """
    블럭별 독립 컨텍스트

    각 블럭은 자신만의 상태 공간을 가지며,
    다른 블럭의 상태에 직접 접근할 수 없음.
    """

    # 블럭별 컨텍스트 저장소 (블럭 격리)
    _contexts: dict[str, dict[str, Any]] = {}

    def __init__(self, block_id: str) -> None:
        self.block_id = block_id
        if block_id not in BlockContext._contexts:
            BlockContext._contexts[block_id] = {}

    def set(self, key: str, value: Any) -> None:
        """컨텍스트에 값 저장"""
        BlockContext._contexts[self.block_id][key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """컨텍스트에서 값 조회"""
        return BlockContext._contexts[self.block_id].get(key, default)

    def delete(self, key: str) -> None:
        """컨텍스트에서 값 삭제"""
        BlockContext._contexts[self.block_id].pop(key, None)

    def clear(self) -> None:
        """컨텍스트 초기화"""
        BlockContext._contexts[self.block_id] = {}

    @classmethod
    def reset_all(cls) -> None:
        """모든 컨텍스트 초기화 (테스트용)"""
        cls._contexts = {}

    def __contains__(self, key: str) -> bool:
        return key in BlockContext._contexts[self.block_id]

    def keys(self) -> list[str]:
        """컨텍스트의 모든 키"""
        return list(BlockContext._contexts[self.block_id].keys())
