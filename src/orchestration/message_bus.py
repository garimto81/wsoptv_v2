"""
Message Bus - 블럭 간 비동기 통신

Redis Pub/Sub 기반 메시지 버스로 블럭 간 느슨한 결합 유지.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class BlockMessage:
    """블럭 간 메시지"""

    source_block: str
    event_type: str
    payload: dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_block": self.source_block,
            "event_type": self.event_type,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlockMessage:
        return cls(
            source_block=data["source_block"],
            event_type=data["event_type"],
            payload=data["payload"],
            correlation_id=data.get("correlation_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.now(UTC),
        )


MessageHandler = Callable[[BlockMessage], Awaitable[None]]


class MessageBus:
    """
    Singleton Message Bus

    블럭 간 통신의 중심으로, 모든 이벤트가 이곳을 통해 전달됨.
    직접 import 대신 메시지를 통해 블럭 간 협력.
    """

    _instance: MessageBus | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        self._subscribers: dict[str, list[MessageHandler]] = {}
        self._message_queue: asyncio.Queue[tuple[str, BlockMessage]] = asyncio.Queue()

    @classmethod
    def get_instance(cls) -> MessageBus:
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """테스트용: 인스턴스 초기화"""
        cls._instance = None

    async def subscribe(self, channel: str, handler: MessageHandler) -> None:
        """
        채널 구독

        Args:
            channel: 이벤트 채널 (예: "auth.user_login")
            handler: 메시지 수신 시 호출될 비동기 핸들러
        """
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(handler)

    async def unsubscribe(self, channel: str, handler: MessageHandler) -> None:
        """채널 구독 해제"""
        if channel in self._subscribers:
            self._subscribers[channel] = [
                h for h in self._subscribers[channel] if h != handler
            ]

    async def publish(self, channel: str, message: BlockMessage) -> None:
        """
        메시지 발행

        Args:
            channel: 발행할 채널
            message: 발행할 메시지
        """
        if channel in self._subscribers:
            for handler in self._subscribers[channel]:
                # 비동기로 핸들러 실행 (에러 격리)
                try:
                    await handler(message)
                except Exception as e:
                    # 로깅 (실제로는 structured logging 사용)
                    print(f"Handler error on {channel}: {e}")

    async def request_response(
        self, channel: str, message: BlockMessage, timeout: float = 5.0
    ) -> BlockMessage | None:
        """
        동기적 요청-응답 패턴

        Args:
            channel: 요청 채널
            message: 요청 메시지
            timeout: 응답 대기 시간 (초)

        Returns:
            응답 메시지 또는 None (타임아웃)
        """
        response_channel = f"{channel}.response.{message.correlation_id}"
        response_event = asyncio.Event()
        response_message: BlockMessage | None = None

        async def response_handler(msg: BlockMessage) -> None:
            nonlocal response_message
            response_message = msg
            response_event.set()

        await self.subscribe(response_channel, response_handler)
        await self.publish(channel, message)

        try:
            await asyncio.wait_for(response_event.wait(), timeout=timeout)
        except TimeoutError:
            pass
        finally:
            await self.unsubscribe(response_channel, response_handler)

        return response_message

    def get_subscribers(self, channel: str) -> list[MessageHandler]:
        """채널의 구독자 목록 반환"""
        return self._subscribers.get(channel, [])
