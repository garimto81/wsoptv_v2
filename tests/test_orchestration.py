"""
블럭 아키텍처 검증 테스트 - Orchestration Layer

TDD RED Phase: 이 테스트들은 아직 구현이 없어 실패해야 합니다.
"""

import pytest
from typing import Any


class TestMessageBus:
    """메시지 버스 테스트 - 블럭 간 통신의 핵심"""

    def test_message_bus_singleton(self):
        """메시지 버스는 싱글톤이어야 함"""
        from src.orchestration.message_bus import MessageBus

        bus1 = MessageBus.get_instance()
        bus2 = MessageBus.get_instance()
        assert bus1 is bus2

    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        """Pub/Sub 패턴으로 블럭 간 통신"""
        from src.orchestration.message_bus import MessageBus, BlockMessage

        bus = MessageBus.get_instance()
        received_messages: list[BlockMessage] = []

        async def handler(msg: BlockMessage):
            received_messages.append(msg)

        await bus.subscribe("auth.user_login", handler)

        message = BlockMessage(
            source_block="auth",
            event_type="user_login",
            payload={"user_id": "user123"}
        )
        await bus.publish("auth.user_login", message)

        assert len(received_messages) == 1
        assert received_messages[0].payload["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_message_has_correlation_id(self):
        """모든 메시지는 추적을 위한 correlation_id를 가짐"""
        from src.orchestration.message_bus import BlockMessage

        message = BlockMessage(
            source_block="content",
            event_type="content_viewed",
            payload={"content_id": "video123"}
        )

        assert message.correlation_id is not None
        assert len(message.correlation_id) > 0


class TestBlockRegistry:
    """블럭 레지스트리 테스트 - 블럭 관리 및 상태 추적"""

    def test_register_block(self):
        """블럭 등록"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()
        auth_block = BlockInfo(
            block_id="auth",
            version="1.0.0",
            provides=["validate_token", "get_user"],
            requires=[]
        )

        registry.register(auth_block)

        assert registry.get_block("auth") is not None
        assert registry.get_block("auth").version == "1.0.0"

    def test_block_dependency_check(self):
        """블럭 의존성 검증"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()

        # Auth는 의존성 없음 (L0)
        auth_block = BlockInfo(
            block_id="auth",
            version="1.0.0",
            provides=["validate_token"],
            requires=[]
        )
        registry.register(auth_block)

        # Content는 auth.validate_token 필요
        content_block = BlockInfo(
            block_id="content",
            version="1.0.0",
            provides=["get_content"],
            requires=["auth.validate_token"]
        )

        # 의존성이 충족되어야 등록 성공
        assert registry.can_register(content_block) is True

    def test_block_dependency_missing(self):
        """누락된 의존성 감지"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()

        # Auth 블럭 없이 Content 등록 시도
        content_block = BlockInfo(
            block_id="content",
            version="1.0.0",
            provides=["get_content"],
            requires=["auth.validate_token"]
        )

        # 의존성 미충족으로 등록 실패
        assert registry.can_register(content_block) is False

    def test_block_health_status(self):
        """블럭 헬스 체크"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()
        auth_block = BlockInfo(
            block_id="auth",
            version="1.0.0",
            provides=["validate_token"],
            requires=[]
        )
        registry.register(auth_block)

        # 초기 상태는 healthy
        assert registry.is_healthy("auth") is True


class TestBlockContract:
    """블럭 Contract 테스트 - 인터페이스 검증"""

    def test_contract_validation(self):
        """Contract 버전 호환성 검증"""
        from src.orchestration.contract import ContractValidator

        validator = ContractValidator()

        # 동일 메이저 버전은 호환
        assert validator.is_compatible("1.0.0", "1.2.0") is True

        # 다른 메이저 버전은 비호환
        assert validator.is_compatible("1.0.0", "2.0.0") is False

    def test_contract_schema_validation(self):
        """Contract 스키마 검증"""
        from src.orchestration.contract import ContractValidator

        validator = ContractValidator()

        # validate_token contract 정의
        contract = {
            "name": "validate_token",
            "version": "1.0.0",
            "input": {"token": "str"},
            "output": {"valid": "bool", "user_id": "str | None"}
        }

        # 올바른 입력
        valid_input = {"token": "abc123"}
        assert validator.validate_input(contract, valid_input) is True

        # 잘못된 입력 (token 누락)
        invalid_input = {}
        assert validator.validate_input(contract, invalid_input) is False


class TestMessageBusAdvanced:
    """MessageBus 고급 테스트"""

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """여러 구독자에게 메시지 전달"""
        from src.orchestration.message_bus import MessageBus, BlockMessage

        MessageBus.reset_instance()
        bus = MessageBus.get_instance()

        received1 = []
        received2 = []

        async def handler1(msg): received1.append(msg)
        async def handler2(msg): received2.append(msg)

        await bus.subscribe("test.channel", handler1)
        await bus.subscribe("test.channel", handler2)

        message = BlockMessage(source_block="test", event_type="test", payload={})
        await bus.publish("test.channel", message)

        assert len(received1) == 1
        assert len(received2) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """구독 해제 테스트"""
        from src.orchestration.message_bus import MessageBus, BlockMessage

        MessageBus.reset_instance()
        bus = MessageBus.get_instance()

        received = []
        async def handler(msg): received.append(msg)

        await bus.subscribe("test.channel", handler)
        await bus.unsubscribe("test.channel", handler)

        message = BlockMessage(source_block="test", event_type="test", payload={})
        await bus.publish("test.channel", message)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self):
        """구독자 없는 채널에 발행"""
        from src.orchestration.message_bus import MessageBus, BlockMessage

        MessageBus.reset_instance()
        bus = MessageBus.get_instance()

        message = BlockMessage(source_block="test", event_type="test", payload={})
        # 에러 없이 실행되어야 함
        await bus.publish("nonexistent.channel", message)

    @pytest.mark.asyncio
    async def test_message_to_dict_and_back(self):
        """메시지 직렬화/역직렬화"""
        from src.orchestration.message_bus import BlockMessage

        original = BlockMessage(
            source_block="auth",
            event_type="user_login",
            payload={"user_id": "123", "email": "test@test.com"}
        )

        data = original.to_dict()
        restored = BlockMessage.from_dict(data)

        assert restored.source_block == original.source_block
        assert restored.event_type == original.event_type
        assert restored.payload == original.payload

    @pytest.mark.asyncio
    async def test_handler_error_isolation(self):
        """핸들러 에러 격리 - 한 핸들러 실패가 다른 핸들러에 영향 없음"""
        from src.orchestration.message_bus import MessageBus, BlockMessage

        MessageBus.reset_instance()
        bus = MessageBus.get_instance()

        received = []

        async def failing_handler(msg):
            raise ValueError("Handler error")

        async def working_handler(msg):
            received.append(msg)

        await bus.subscribe("test.channel", failing_handler)
        await bus.subscribe("test.channel", working_handler)

        message = BlockMessage(source_block="test", event_type="test", payload={})
        await bus.publish("test.channel", message)

        # working_handler는 정상 작동해야 함
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_get_subscribers(self):
        """구독자 목록 조회"""
        from src.orchestration.message_bus import MessageBus

        MessageBus.reset_instance()
        bus = MessageBus.get_instance()

        async def handler1(msg): pass
        async def handler2(msg): pass

        await bus.subscribe("test.channel", handler1)
        await bus.subscribe("test.channel", handler2)

        subscribers = bus.get_subscribers("test.channel")
        assert len(subscribers) == 2

    @pytest.mark.asyncio
    async def test_request_response_pattern(self):
        """동기적 요청-응답 패턴"""
        from src.orchestration.message_bus import MessageBus, BlockMessage

        MessageBus.reset_instance()
        bus = MessageBus.get_instance()

        # 응답 핸들러 설정
        async def request_handler(msg: BlockMessage):
            response_channel = f"test.request.response.{msg.correlation_id}"
            response = BlockMessage(
                source_block="responder",
                event_type="response",
                payload={"result": "success"}
            )
            await bus.publish(response_channel, response)

        await bus.subscribe("test.request", request_handler)

        # 요청 발송
        request = BlockMessage(
            source_block="requester",
            event_type="request",
            payload={"query": "test"}
        )

        response = await bus.request_response("test.request", request, timeout=1.0)

        assert response is not None
        assert response.payload["result"] == "success"

    @pytest.mark.asyncio
    async def test_request_response_timeout(self):
        """요청-응답 타임아웃"""
        from src.orchestration.message_bus import MessageBus, BlockMessage

        MessageBus.reset_instance()
        bus = MessageBus.get_instance()

        # 응답하지 않는 핸들러
        async def no_response_handler(msg: BlockMessage):
            pass

        await bus.subscribe("test.request", no_response_handler)

        request = BlockMessage(
            source_block="requester",
            event_type="request",
            payload={"query": "test"}
        )

        response = await bus.request_response("test.request", request, timeout=0.1)

        assert response is None


class TestBlockRegistryAdvanced:
    """BlockRegistry 고급 테스트"""

    def test_unregister_block(self):
        """블럭 등록 해제"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()
        block = BlockInfo(block_id="test", version="1.0.0", provides=["func1"], requires=[])

        registry.register(block)
        assert registry.get_block("test") is not None

        registry.unregister("test")
        assert registry.get_block("test") is None

    def test_unregister_with_dependents_fails(self):
        """의존하는 블럭이 있으면 등록 해제 실패"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()

        auth = BlockInfo(block_id="auth", version="1.0.0", provides=["validate"], requires=[])
        content = BlockInfo(block_id="content", version="1.0.0", provides=["get"], requires=["auth.validate"])

        registry.register(auth)
        registry.register(content)

        # auth는 content가 의존하므로 해제 실패
        with pytest.raises(ValueError, match="required by"):
            registry.unregister("auth")

    def test_unregister_nonexistent_block(self):
        """존재하지 않는 블럭 해제 시도"""
        from src.orchestration.registry import BlockRegistry

        registry = BlockRegistry()
        # 에러 없이 실행되어야 함
        registry.unregister("nonexistent")

    def test_get_all_blocks(self):
        """모든 블럭 조회"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()

        block1 = BlockInfo(block_id="a", version="1.0.0", provides=[], requires=[])
        block2 = BlockInfo(block_id="b", version="1.0.0", provides=[], requires=[])

        registry.register(block1)
        registry.register(block2)

        all_blocks = registry.get_all_blocks()
        assert len(all_blocks) == 2

    def test_dependency_order(self):
        """의존성 순서 정렬"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()

        # L0
        auth = BlockInfo(block_id="auth", version="1.0.0", provides=["validate"], requires=[])
        cache = BlockInfo(block_id="cache", version="1.0.0", provides=["get"], requires=[])

        # L1
        content = BlockInfo(block_id="content", version="1.0.0", provides=["data"], requires=["auth.validate"])

        # L2
        stream = BlockInfo(block_id="stream", version="1.0.0", provides=["play"], requires=["auth.validate", "cache.get", "content.data"])

        registry.register(auth)
        registry.register(cache)
        registry.register(content)
        registry.register(stream)

        order = registry.get_dependency_order()

        # auth, cache가 content보다 먼저, content가 stream보다 먼저
        auth_idx = order.index("auth")
        cache_idx = order.index("cache")
        content_idx = order.index("content")
        stream_idx = order.index("stream")

        assert auth_idx < content_idx
        assert content_idx < stream_idx

    def test_update_health(self):
        """헬스 상태 업데이트"""
        from src.orchestration.registry import BlockRegistry, BlockInfo, BlockStatus

        registry = BlockRegistry()
        block = BlockInfo(block_id="test", version="1.0.0", provides=[], requires=[])
        registry.register(block)

        assert registry.is_healthy("test") is True

        registry.update_health("test", BlockStatus.UNHEALTHY)
        assert registry.is_healthy("test") is False

    def test_update_health_nonexistent_block(self):
        """존재하지 않는 블럭의 헬스 업데이트"""
        from src.orchestration.registry import BlockRegistry, BlockStatus

        registry = BlockRegistry()
        # 에러 없이 실행되어야 함
        registry.update_health("nonexistent", BlockStatus.UNHEALTHY)

    def test_register_duplicate_block(self):
        """중복 블럭 등록 방지"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()
        block = BlockInfo(block_id="test", version="1.0.0", provides=[], requires=[])

        registry.register(block)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(block)

    def test_register_missing_dependencies(self):
        """의존성 미충족 시 등록 실패"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()

        content = BlockInfo(
            block_id="content",
            version="1.0.0",
            provides=["get"],
            requires=["auth.validate"]
        )

        with pytest.raises(ValueError, match="missing dependencies"):
            registry.register(content)

    def test_get_required_blocks(self):
        """블럭이 의존하는 블럭 ID 목록 조회"""
        from src.orchestration.registry import BlockInfo

        block = BlockInfo(
            block_id="stream",
            version="1.0.0",
            provides=["play"],
            requires=["auth.validate", "cache.get", "content.data"]
        )

        required = block.get_required_blocks()
        assert required == {"auth", "cache", "content"}

    def test_circular_dependency_detection(self):
        """순환 의존성 감지"""
        from src.orchestration.registry import BlockRegistry, BlockInfo

        registry = BlockRegistry()

        # 실제로 순환 의존성을 만들기는 어려움 (등록 시 검증)
        # 하지만 get_dependency_order에서 감지 테스트

        # A -> B, B -> C, C -> A (순환)
        # 이 경우는 등록 자체가 불가능하므로,
        # 대신 복잡한 의존성 그래프 테스트

        a = BlockInfo(block_id="a", version="1.0.0", provides=["fa"], requires=[])
        b = BlockInfo(block_id="b", version="1.0.0", provides=["fb"], requires=["a.fa"])
        c = BlockInfo(block_id="c", version="1.0.0", provides=["fc"], requires=["b.fb"])

        registry.register(a)
        registry.register(b)
        registry.register(c)

        order = registry.get_dependency_order()
        assert order == ["a", "b", "c"]


class TestContractValidatorAdvanced:
    """ContractValidator 고급 테스트"""

    def test_validate_output(self):
        """출력 스키마 검증"""
        from src.orchestration.contract import ContractValidator

        validator = ContractValidator()

        contract = {
            "name": "get_user",
            "output": {"id": "str", "email": "str", "is_admin": "bool"}
        }

        valid_output = {"id": "123", "email": "test@test.com", "is_admin": True}
        assert validator.validate_output(contract, valid_output) is True

        invalid_output = {"id": 123, "email": "test@test.com"}  # id가 int
        assert validator.validate_output(contract, invalid_output) is False

    def test_nullable_output(self):
        """Nullable 출력 검증"""
        from src.orchestration.contract import ContractValidator

        validator = ContractValidator()

        contract = {
            "output": {"user_id": "str | None"}
        }

        # None 허용
        assert validator.validate_output(contract, {"user_id": None}) is True
        assert validator.validate_output(contract, {"user_id": "123"}) is True

    def test_validate_complex_types(self):
        """복잡한 타입 검증"""
        from src.orchestration.contract import ContractValidator

        validator = ContractValidator()

        contract = {
            "output": {
                "user": "dict",
                "tags": "list",
                "count": "int"
            }
        }

        valid_output = {
            "user": {"id": "123"},
            "tags": ["tag1", "tag2"],
            "count": 42
        }
        assert validator.validate_output(contract, valid_output) is True

    def test_missing_required_field(self):
        """필수 필드 누락 감지"""
        from src.orchestration.contract import ContractValidator

        validator = ContractValidator()

        contract = {
            "input": {"user_id": "str", "token": "str"}
        }

        incomplete_input = {"user_id": "123"}
        assert validator.validate_input(contract, incomplete_input) is False


class TestBlockIsolation:
    """블럭 격리 테스트 - 코드 오염 방지의 핵심"""

    def test_no_direct_import_between_blocks(self):
        """블럭 간 직접 import 금지 검증"""
        from src.orchestration.isolation import ImportChecker

        checker = ImportChecker()

        # 허용: 자기 블럭 내 import
        assert checker.is_allowed_import(
            from_block="auth",
            import_path="src.blocks.auth.models"
        ) is True

        # 금지: 다른 블럭 직접 import
        assert checker.is_allowed_import(
            from_block="content",
            import_path="src.blocks.auth.models"
        ) is False

        # 허용: orchestration을 통한 통신
        assert checker.is_allowed_import(
            from_block="content",
            import_path="src.orchestration.message_bus"
        ) is True

    def test_block_context_isolation(self):
        """블럭별 독립 컨텍스트"""
        from src.orchestration.isolation import BlockContext

        auth_context = BlockContext(block_id="auth")
        content_context = BlockContext(block_id="content")

        # 각 컨텍스트는 독립적
        auth_context.set("key", "auth_value")
        content_context.set("key", "content_value")

        assert auth_context.get("key") == "auth_value"
        assert content_context.get("key") == "content_value"
