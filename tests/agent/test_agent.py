"""测试 Agent 核心类。

覆盖场景：
- 初始化（Provider / Registry / SystemPrompt）
- 普通对话
- 带函数调用的对话（含 tool_call_id 跟踪）
- 多轮迭代 & 最大迭代限制
- 函数执行错误处理
- 不支持函数调用的 Provider
- 额外参数透传
- 消息解析（JSON 数组 / 对象 / Markdown / 无效 JSON）
- 历史管理（clear_history）
- 便捷注册函数
"""
import pytest
from unittest.mock import AsyncMock, Mock

from agent.agent import Agent
from agent.providers.base import LLMMessage, LLMResponse, FunctionCall
from agent.functions.registry import FunctionRegistry


class TestAgentInit:
    """Agent 初始化测试。"""

    def test_init_with_provider_only(self, mock_llm_provider):
        agent = Agent(mock_llm_provider)
        assert agent.provider == mock_llm_provider
        assert isinstance(agent.function_registry, FunctionRegistry)
        assert agent.tool_executor is not None
        assert agent.conversation_history == []

    def test_init_with_custom_registry(
        self, mock_llm_provider, function_registry
    ):
        agent = Agent(mock_llm_provider, function_registry=function_registry)
        assert agent.function_registry is function_registry

    def test_init_with_system_prompt(self, mock_llm_provider):
        agent = Agent(mock_llm_provider, system_prompt="你是助手")
        assert agent.system_prompt == "你是助手"
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0].role == "system"
        assert agent.conversation_history[0].content == "你是助手"


class TestAgentChat:
    """Agent.chat() 测试。"""

    @pytest.mark.asyncio
    async def test_simple_chat(self, mock_llm_provider):
        agent = Agent(mock_llm_provider)
        response = await agent.chat("你好")

        assert response["content"] == "这是一个测试回复"
        assert response["function_calls"] == []
        assert response["iterations"] == 1
        # 历史：user + assistant
        assert len(agent.conversation_history) == 2
        assert agent.conversation_history[0].role == "user"
        assert agent.conversation_history[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_chat_with_function_calling(
        self, mock_llm_provider_with_function_calling, populated_registry
    ):
        """函数调用应正确执行并记录 tool 消息。"""
        agent = Agent(
            mock_llm_provider_with_function_calling,
            function_registry=populated_registry,
        )
        # populated_registry 里没有 "test_function"，
        # 但 mock provider 会调用它 → 会触发执行错误 → 仍然继续
        # 先注册一个 test_function 保证可执行
        populated_registry.register(
            name="test_function",
            description="测试函数",
            func=lambda param1="": {"ok": True, "param1": param1},
        )

        response = await agent.chat("调用测试函数")

        assert response["iterations"] >= 2
        assert len(response["function_calls"]) > 0
        assert response["function_calls"][0]["name"] == "test_function"
        # 历史中应包含 tool 消息
        tool_msgs = [
            m for m in agent.conversation_history if m.role == "tool"
        ]
        assert len(tool_msgs) > 0
        # tool 消息应包含 tool_call_id
        assert tool_msgs[0].tool_call_id == "call_mock_001"

    @pytest.mark.asyncio
    async def test_max_iterations(self, populated_registry):
        """达到最大迭代次数时应停止。"""
        provider = Mock()
        provider.model_name = "mock-model"
        provider.supports_function_calling = Mock(return_value=True)

        async def always_tool_call(messages, functions=None, **kwargs):
            return LLMResponse(
                content="",
                function_calls=[
                    FunctionCall(
                        name="sync_test_function",
                        arguments={"param1": "x"},
                        id="call_loop",
                    )
                ],
                finish_reason="tool_calls",
            )

        provider.chat = AsyncMock(side_effect=always_tool_call)
        agent = Agent(provider, function_registry=populated_registry)

        response = await agent.chat("测试", max_iterations=3)
        assert response["iterations"] == 3
        assert len(response["function_calls"]) == 3

    @pytest.mark.asyncio
    async def test_function_execution_error(self):
        """函数执行错误应被捕获并写入 tool 消息。"""
        registry = FunctionRegistry()

        def error_function():
            raise ValueError("模拟执行错误")

        registry.register("error_func", "错误函数", error_function)

        call_count = {"n": 0}

        async def mock_chat(messages, functions=None, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return LLMResponse(
                    content="",
                    function_calls=[
                        FunctionCall(
                            name="error_func", arguments={}, id="call_err"
                        )
                    ],
                    finish_reason="tool_calls",
                )
            return LLMResponse(
                content="已处理错误", function_calls=None, finish_reason="stop"
            )

        provider = Mock()
        provider.model_name = "mock"
        provider.supports_function_calling = Mock(return_value=True)
        provider.chat = AsyncMock(side_effect=mock_chat)

        agent = Agent(provider, function_registry=registry)
        response = await agent.chat("触发错误")

        tool_msgs = [
            m for m in agent.conversation_history if m.role == "tool"
        ]
        assert len(tool_msgs) == 1
        assert "错误" in tool_msgs[0].content
        assert tool_msgs[0].tool_call_id == "call_err"

    @pytest.mark.asyncio
    async def test_no_function_calling_support(self, populated_registry):
        """Provider 不支持函数调用时，不应传递函数列表。"""
        provider = Mock()
        provider.model_name = "no-fc"
        provider.supports_function_calling = Mock(return_value=False)
        provider.chat = AsyncMock(
            return_value=LLMResponse(
                content="直接回复", function_calls=None, finish_reason="stop"
            )
        )

        agent = Agent(provider, function_registry=populated_registry)
        response = await agent.chat("测试")

        assert response["content"] == "直接回复"
        assert response["function_calls"] == []
        # 调用 provider.chat 时 functions 应为 None
        call_kwargs = provider.chat.call_args
        assert call_kwargs.kwargs.get("functions") is None

    @pytest.mark.asyncio
    async def test_kwargs_passthrough(self, mock_llm_provider):
        """额外参数应透传给 Provider.chat()。"""
        agent = Agent(mock_llm_provider)
        await agent.chat("测试", temperature=0.5, max_tokens=100)

        call_kwargs = mock_llm_provider.chat.call_args.kwargs
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 100


class TestAgentParseMessage:
    """Agent.parse_message() 测试。"""

    @staticmethod
    def _make_provider(content: str):
        provider = Mock()
        provider.model_name = "mock"
        provider.supports_function_calling = Mock(return_value=False)
        provider.chat = AsyncMock(
            return_value=LLMResponse(
                content=content, function_calls=None, finish_reason="stop"
            )
        )
        return provider

    @pytest.mark.asyncio
    async def test_parse_json_array(self):
        provider = self._make_provider(
            '[{"type": "service", "name": "头疗", "price": 30}]'
        )
        agent = Agent(provider)
        result = await agent.parse_message("用户", "2024-01-28", "头疗30")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "service"

    @pytest.mark.asyncio
    async def test_parse_json_object(self):
        provider = self._make_provider('{"type": "service", "name": "头疗"}')
        agent = Agent(provider)
        result = await agent.parse_message("用户", "2024-01-28", "头疗")
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_parse_json_with_records_key(self):
        provider = self._make_provider(
            '{"records": [{"type": "a"}, {"type": "b"}]}'
        )
        agent = Agent(provider)
        result = await agent.parse_message("用户", "2024-01-28", "内容")
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_parse_markdown_code_block(self):
        provider = self._make_provider(
            '```json\n[{"type": "service"}]\n```'
        )
        agent = Agent(provider)
        result = await agent.parse_message("用户", "2024-01-28", "服务")
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_parse_invalid_json(self):
        provider = self._make_provider("这不是有效的 JSON")
        agent = Agent(provider)
        result = await agent.parse_message("用户", "2024-01-28", "测试")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "error" in result[0] or "type" in result[0]


class TestAgentHistory:
    """对话历史管理测试。"""

    def test_clear_history_keeps_system_prompt(self, mock_llm_provider):
        agent = Agent(mock_llm_provider, system_prompt="系统提示")
        agent.conversation_history.append(
            LLMMessage(role="user", content="消息")
        )
        assert len(agent.conversation_history) == 2

        agent.clear_history()
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0].role == "system"

    def test_clear_history_no_system_prompt(self, mock_llm_provider):
        agent = Agent(mock_llm_provider)
        agent.conversation_history.append(
            LLMMessage(role="user", content="消息")
        )
        agent.clear_history()
        assert len(agent.conversation_history) == 0

    def test_register_function_shortcut(self, mock_llm_provider):
        agent = Agent(mock_llm_provider)

        def my_func(x: str) -> str:
            return x

        agent.register_function("my_func", "测试", my_func)
        assert agent.function_registry.has_function("my_func")
        func_def = agent.function_registry.get_function("my_func")
        assert func_def.description == "测试"
