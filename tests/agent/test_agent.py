"""测试 Agent 核心类。

本模块测试 Agent 类的所有功能，包括：
- 初始化
- 普通对话
- 函数调用
- 多轮迭代
- 消息解析
- 历史管理
"""
import pytest
import json
from unittest.mock import AsyncMock, Mock

from agent.agent import Agent
from agent.providers.base import LLMMessage, LLMResponse, FunctionCall
from agent.functions.registry import FunctionRegistry
from tests.agent.conftest import (
    mock_llm_provider,
    mock_llm_provider_with_function_calling,
    populated_registry
)


class TestAgent:
    """Agent 测试类"""
    
    def test_init_with_provider(self, mock_llm_provider):
        """测试使用 Provider 初始化"""
        agent = Agent(mock_llm_provider)
        
        assert agent.provider == mock_llm_provider
        assert agent.function_registry is not None
        assert isinstance(agent.function_registry, FunctionRegistry)
        assert agent.tool_executor is not None
        assert agent.conversation_history == []
    
    def test_init_with_registry(self, mock_llm_provider, function_registry):
        """测试使用自定义 Registry 初始化"""
        agent = Agent(mock_llm_provider, function_registry=function_registry)
        
        assert agent.function_registry == function_registry
    
    def test_init_with_system_prompt(self, mock_llm_provider):
        """测试使用系统提示词初始化"""
        system_prompt = "你是一个有用的助手"
        agent = Agent(mock_llm_provider, system_prompt=system_prompt)
        
        assert agent.system_prompt == system_prompt
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0].role == "system"
        assert agent.conversation_history[0].content == system_prompt
    
    @pytest.mark.asyncio
    async def test_chat_simple(self, mock_llm_provider):
        """测试简单对话"""
        agent = Agent(mock_llm_provider)
        
        response = await agent.chat("你好")
        
        assert "content" in response
        assert response["content"] == "这是一个测试回复"
        assert response["function_calls"] == []
        assert response["iterations"] == 1
        
        # 检查历史记录
        assert len(agent.conversation_history) == 2  # user + assistant
        assert agent.conversation_history[0].role == "user"
        assert agent.conversation_history[0].content == "你好"
        assert agent.conversation_history[1].role == "assistant"
    
    @pytest.mark.asyncio
    async def test_chat_with_function_calling(self, mock_llm_provider_with_function_calling, populated_registry):
        """测试带函数调用的对话"""
        agent = Agent(
            mock_llm_provider_with_function_calling,
            function_registry=populated_registry
        )
        
        response = await agent.chat("调用测试函数")
        
        # 应该进行了多轮迭代
        assert response["iterations"] >= 2
        assert len(response["function_calls"]) > 0
        assert response["function_calls"][0]["name"] == "test_function"
        
        # 检查历史记录应该包含 function 消息
        function_messages = [
            msg for msg in agent.conversation_history
            if msg.role == "function"
        ]
        assert len(function_messages) > 0
    
    @pytest.mark.asyncio
    async def test_chat_max_iterations(self, mock_llm_provider_with_function_calling, populated_registry):
        """测试达到最大迭代次数"""
        # 创建一个总是返回函数调用的 provider
        provider = Mock()
        provider.model_name = "mock-model"
        provider.supports_function_calling = Mock(return_value=True)
        
        async def always_function_call(messages, functions=None, **kwargs):
            return LLMResponse(
                content="",
                function_calls=[
                    FunctionCall(name="test_function", arguments={})
                ],
                finish_reason="tool_calls"
            )
        
        provider.chat = AsyncMock(side_effect=always_function_call)
        
        agent = Agent(provider, function_registry=populated_registry)
        
        response = await agent.chat("测试", max_iterations=3)
        
        assert response["iterations"] == 3
        assert len(response["function_calls"]) == 3
    
    @pytest.mark.asyncio
    async def test_chat_function_execution_error(self, mock_llm_provider_with_function_calling):
        """测试函数执行错误处理"""
        registry = FunctionRegistry()
        
        def error_function() -> str:
            raise ValueError("执行错误")
        
        registry.register(
            name="error_function",
            description="错误函数",
            func=error_function
        )
        
        # 修改 provider 使其调用 error_function
        async def call_error_function(messages, functions=None, **kwargs):
            if any(msg.role == "function" for msg in messages):
                # 第二次调用，返回最终回复
                return LLMResponse(
                    content="处理完成",
                    function_calls=None,
                    finish_reason="stop"
                )
            else:
                # 第一次调用，返回函数调用
                return LLMResponse(
                    content="",
                    function_calls=[
                        FunctionCall(name="error_function", arguments={})
                    ],
                    finish_reason="tool_calls"
                )
        
        provider = Mock()
        provider.model_name = "mock-model"
        provider.supports_function_calling = Mock(return_value=True)
        provider.chat = AsyncMock(side_effect=call_error_function)
        
        agent = Agent(provider, function_registry=registry)
        
        response = await agent.chat("测试")
        
        # 应该包含错误信息
        function_messages = [
            msg for msg in agent.conversation_history
            if msg.role == "function"
        ]
        assert len(function_messages) > 0
        assert "错误" in function_messages[0].content
    
    @pytest.mark.asyncio
    async def test_chat_no_function_calling_support(self, mock_llm_provider, populated_registry):
        """测试不支持函数调用的 Provider"""
        provider = Mock()
        provider.model_name = "mock-model"
        provider.supports_function_calling = Mock(return_value=False)
        provider.chat = AsyncMock(return_value=LLMResponse(
            content="回复内容",
            function_calls=None,
            finish_reason="stop"
        ))
        
        agent = Agent(provider, function_registry=populated_registry)
        
        response = await agent.chat("测试")
        
        # 即使有函数注册表，如果不支持函数调用，也不会调用函数
        assert response["function_calls"] == []
        assert response["content"] == "回复内容"
    
    @pytest.mark.asyncio
    async def test_chat_with_kwargs(self, mock_llm_provider):
        """测试传递额外参数"""
        agent = Agent(mock_llm_provider)
        
        await agent.chat("测试", temperature=0.5, max_tokens=100)
        
        # 检查 provider.chat 是否被调用时包含了这些参数
        call_args = mock_llm_provider.chat.call_args
        assert call_args is not None
        assert "temperature" in call_args.kwargs
        assert call_args.kwargs["temperature"] == 0.5
        assert "max_tokens" in call_args.kwargs
        assert call_args.kwargs["max_tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_parse_message(self, mock_llm_provider):
        """测试解析消息"""
        # 设置 provider 返回 JSON 格式的回复
        async def mock_chat_with_json(messages, functions=None, **kwargs):
            return LLMResponse(
                content='[{"type": "service", "name": "头疗", "price": 30}]',
                function_calls=None,
                finish_reason="stop"
            )
        
        provider = Mock()
        provider.model_name = "mock-model"
        provider.supports_function_calling = Mock(return_value=False)
        provider.chat = AsyncMock(side_effect=mock_chat_with_json)
        
        agent = Agent(provider)
        
        result = await agent.parse_message(
            sender="测试用户",
            timestamp="2024-01-28 10:00:00",
            content="1.28段老师头疗30"
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], dict)
    
    @pytest.mark.asyncio
    async def test_parse_message_json_object(self, mock_llm_provider):
        """测试解析单个 JSON 对象（非数组）"""
        async def mock_chat_with_object(messages, functions=None, **kwargs):
            return LLMResponse(
                content='{"type": "service", "name": "头疗"}',
                function_calls=None,
                finish_reason="stop"
            )
        
        provider = Mock()
        provider.model_name = "mock-model"
        provider.supports_function_calling = Mock(return_value=False)
        provider.chat = AsyncMock(side_effect=mock_chat_with_object)
        
        agent = Agent(provider)
        
        result = await agent.parse_message(
            sender="测试用户",
            timestamp="2024-01-28 10:00:00",
            content="头疗"
        )
        
        # 单个对象应该被转换为列表
        assert isinstance(result, list)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_parse_message_markdown_code_block(self, mock_llm_provider):
        """测试解析 Markdown code block 格式的 JSON"""
        async def mock_chat_with_markdown(messages, functions=None, **kwargs):
            return LLMResponse(
                content='```json\n[{"type": "service"}]\n```',
                function_calls=None,
                finish_reason="stop"
            )
        
        provider = Mock()
        provider.model_name = "mock-model"
        provider.supports_function_calling = Mock(return_value=False)
        provider.chat = AsyncMock(side_effect=mock_chat_with_markdown)
        
        agent = Agent(provider)
        
        result = await agent.parse_message(
            sender="测试用户",
            timestamp="2024-01-28 10:00:00",
            content="服务"
        )
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_parse_message_invalid_json(self, mock_llm_provider):
        """测试解析无效 JSON"""
        async def mock_chat_invalid_json(messages, functions=None, **kwargs):
            return LLMResponse(
                content="这不是有效的 JSON",
                function_calls=None,
                finish_reason="stop"
            )
        
        provider = Mock()
        provider.model_name = "mock-model"
        provider.supports_function_calling = Mock(return_value=False)
        provider.chat = AsyncMock(side_effect=mock_chat_invalid_json)
        
        agent = Agent(provider)
        
        result = await agent.parse_message(
            sender="测试用户",
            timestamp="2024-01-28 10:00:00",
            content="测试"
        )
        
        # 应该返回包含错误信息的字典
        assert isinstance(result, list)
        assert len(result) > 0
        assert "error" in result[0] or "type" in result[0]
    
    def test_clear_history(self, mock_llm_provider):
        """测试清空历史记录"""
        agent = Agent(mock_llm_provider, system_prompt="系统提示")
        
        # 添加一些消息
        agent.conversation_history.append(
            LLMMessage(role="user", content="消息1")
        )
        agent.conversation_history.append(
            LLMMessage(role="assistant", content="回复1")
        )
        
        assert len(agent.conversation_history) == 3  # system + user + assistant
        
        agent.clear_history()
        
        # 应该只保留系统提示词
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0].role == "system"
        assert agent.conversation_history[0].content == "系统提示"
    
    def test_clear_history_no_system_prompt(self, mock_llm_provider):
        """测试清空历史记录（无系统提示词）"""
        agent = Agent(mock_llm_provider)
        
        agent.conversation_history.append(
            LLMMessage(role="user", content="消息1")
        )
        
        agent.clear_history()
        
        # 没有系统提示词时，历史应该为空
        assert len(agent.conversation_history) == 0
    
    def test_register_function(self, mock_llm_provider):
        """测试注册函数（便捷方法）"""
        agent = Agent(mock_llm_provider)
        
        def test_func(param: str) -> str:
            return param
        
        agent.register_function(
            name="test_func",
            description="测试函数",
            func=test_func
        )
        
        assert agent.function_registry.has_function("test_func")
        func_def = agent.function_registry.get_function("test_func")
        assert func_def.description == "测试函数"

