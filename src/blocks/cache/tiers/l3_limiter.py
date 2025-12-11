"""
L3 Rate Limiter - 동시 스트리밍 제한 및 대역폭 관리
"""

from datetime import datetime
from typing import Dict, List, Optional
from ..models import StreamSlot, BandwidthInfo


class L3Limiter:
    """Rate Limiter - 동시 스트리밍 제한 (사용자당 최대 3개)"""

    def __init__(self, max_streams_per_user: int = 3, bandwidth_limit_mbps: float = 100.0):
        """초기화"""
        self.max_streams = max_streams_per_user
        self.bandwidth_limit = bandwidth_limit_mbps
        self._user_slots: Dict[str, List[StreamSlot]] = {}
        self._user_bandwidth: Dict[str, float] = {}

    async def acquire_slot(self, user_id: str, content_id: str) -> tuple[bool, Optional[str]]:
        """
        스트리밍 슬롯 획득

        Returns:
            (성공 여부, 실패 사유)
        """
        # 사용자별 현재 스트리밍 수 확인
        if user_id not in self._user_slots:
            self._user_slots[user_id] = []

        current_streams = len(self._user_slots[user_id])

        if current_streams >= self.max_streams:
            return False, f"Max {self.max_streams} concurrent streams exceeded"

        # 슬롯 할당
        slot = StreamSlot(
            user_id=user_id,
            content_id=content_id,
            acquired_at=datetime.now()
        )
        self._user_slots[user_id].append(slot)

        return True, None

    async def release_slot(self, user_id: str) -> None:
        """스트리밍 슬롯 해제 (가장 오래된 슬롯 1개)"""
        if user_id in self._user_slots and self._user_slots[user_id]:
            self._user_slots[user_id].pop(0)

    async def get_active_streams(self, user_id: str) -> int:
        """사용자의 현재 활성 스트리밍 수"""
        if user_id not in self._user_slots:
            return 0
        return len(self._user_slots[user_id])

    async def get_bandwidth_info(self, user_id: str) -> BandwidthInfo:
        """사용자 대역폭 정보"""
        current = self._user_bandwidth.get(user_id, 0.0)
        return BandwidthInfo(
            limit_mbps=self.bandwidth_limit,
            current_mbps=current
        )

    async def record_bandwidth_usage(self, user_id: str, mbps: float) -> None:
        """대역폭 사용량 기록"""
        self._user_bandwidth[user_id] = mbps

    async def clear_user(self, user_id: str) -> None:
        """사용자의 모든 슬롯 및 대역폭 정보 삭제"""
        if user_id in self._user_slots:
            del self._user_slots[user_id]
        if user_id in self._user_bandwidth:
            del self._user_bandwidth[user_id]
