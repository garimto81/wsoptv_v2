"""
Contract Validator - 블럭 간 인터페이스 계약 검증

블럭 간 통신은 명시적 Contract를 통해서만 이루어짐.
Contract는 버전 관리되며, 호환성 검증을 통해 안정성 확보.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Contract:
    """블럭 간 계약 정의"""

    name: str
    version: str
    input_schema: dict[str, str]
    output_schema: dict[str, str]
    description: str = ""


class ContractValidator:
    """
    Contract 검증기

    - 버전 호환성 검증 (Semantic Versioning)
    - 입/출력 스키마 검증
    """

    def __init__(self) -> None:
        self._contracts: dict[str, Contract] = {}

    def register_contract(self, contract: Contract) -> None:
        """Contract 등록"""
        key = f"{contract.name}:{contract.version}"
        self._contracts[key] = contract

    def is_compatible(self, version1: str, version2: str) -> bool:
        """
        버전 호환성 검증 (Semantic Versioning)

        같은 메이저 버전이면 호환됨.
        예: 1.0.0 ↔ 1.2.0 (호환), 1.0.0 ↔ 2.0.0 (비호환)
        """
        try:
            major1 = int(version1.split(".")[0])
            major2 = int(version2.split(".")[0])
            return major1 == major2
        except (ValueError, IndexError):
            return False

    def validate_input(
        self, contract: dict[str, Any], input_data: dict[str, Any]
    ) -> bool:
        """
        입력 스키마 검증

        Args:
            contract: Contract 정의 (dict 형태)
            input_data: 검증할 입력 데이터

        Returns:
            스키마 일치 여부
        """
        input_schema = contract.get("input", {})

        for field_name, field_type in input_schema.items():
            if field_name not in input_data:
                return False

            # 타입 검증 (단순 검증)
            value = input_data[field_name]
            if not self._check_type(value, field_type):
                return False

        return True

    def validate_output(
        self, contract: dict[str, Any], output_data: dict[str, Any]
    ) -> bool:
        """출력 스키마 검증"""
        output_schema = contract.get("output", {})

        for field_name, field_type in output_schema.items():
            # None 허용 타입 처리 (예: "str | None")
            if "| None" in field_type or "| null" in field_type:
                if field_name not in output_data:
                    continue
                if output_data[field_name] is None:
                    continue

            if field_name not in output_data:
                return False

            value = output_data[field_name]
            base_type = field_type.split("|")[0].strip()
            if value is not None and not self._check_type(value, base_type):
                return False

        return True

    def _check_type(self, value: Any, type_str: str) -> bool:
        """단순 타입 검증"""
        type_map = {
            "str": str,
            "int": int,
            "float": (int, float),
            "bool": bool,
            "list": list,
            "dict": dict,
        }

        expected_type = type_map.get(type_str)
        if expected_type is None:
            return True  # 알 수 없는 타입은 통과

        return isinstance(value, expected_type)

    def get_contract(self, name: str, version: str) -> Contract | None:
        """Contract 조회"""
        key = f"{name}:{version}"
        return self._contracts.get(key)
