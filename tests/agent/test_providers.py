"""测试 LLM Provider 实现。

本模块测试所有 LLM Provider 的实现，包括：
- OpenAIProvider
- ClaudeProvider
- OpenSourceProvider

测试支持两种模式：
1. Mock 测试：使用 mock 对象模拟 API 响应（默认）
2. 真实 API 测试：通过环境变量配置进行真实 API 调用

使用真实 API 测试：
    export AGENT_TEST_USE_REAL_API=true
    export AGENT_TEST_PROVIDER_TYPE=openai
    export AGENT_TEST_API_KEY=sk-...
    export AGENT_TEST_MODEL=gpt-4o-mini
    pytest tests/agent/test_providers.py
"""
import pytest
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall
from agent.providers.openai_provider import OpenAIProvider
from agent.providers.claude_provider import ClaudeProvider
from agent.providers.open_source_provider import OpenSourceProvider
from tests.agent.conftest import get_test_config


# 注意：异步测试需要 @pytest.mark.asyncio 标记


class TestOpenAIProvider:
    """测试 OpenAIProvider"""
    
    def test_init(self):
        """测试初始化"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        
        assert provider.model_name == "gpt-4o-mini"
        assert provider.supports_function_calling() is True
        assert provider.client is not None
    
    def test_init_with_base_url(self):
        """测试使用自定义 base_url 初始化"""
        provider = OpenAIProvider(
            api_key="test-key",
            model="custom-model",
            base_url="https://api.example.com/v1"
        )
        
        assert provider.model_name == "custom-model"
        # OpenAI 客户端会自动在 base_url 后面加斜杠
        assert str(provider.client.base_url).rstrip("/") == "https://api.example.com/v1"
    
    @pytest.mark.asyncio
    async def test_chat_simple(self):
        """测试简单对话（Mock）"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        
        # Mock OpenAI 客户端响应
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "这是测试回复"
        mock_message.tool_calls = None
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        
        provider.client.chat.completions.create = Mock(return_value=mock_response)
        
        messages = [
            LLMMessage(role="user", content="你好")
        ]
        
        response = await provider.chat(messages)
        
        assert response.content == "这是测试回复"
        assert response.function_calls is None
        assert response.finish_reason == "stop"
    
    @pytest.mark.asyncio
    async def test_chat_with_function_calling(self):
        """测试带函数调用的对话（Mock）"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        
        # Mock OpenAI 客户端响应（包含函数调用）
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = None
        mock_tool_call = Mock()
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "test_function"
        mock_tool_call.function.arguments = '{"param1": "value1"}'
        mock_message.tool_calls = [mock_tool_call]
        mock_choice.message = mock_message
        mock_choice.finish_reason = "tool_calls"
        mock_response.choices = [mock_choice]
        
        provider.client.chat.completions.create = Mock(return_value=mock_response)
        
        messages = [
            LLMMessage(role="user", content="调用函数")
        ]
        functions = [
            {
                "name": "test_function",
                "description": "测试函数",
                "parameters": {
                    "type": "object",
                    "properties": {"param1": {"type": "string"}},
                    "required": ["param1"]
                }
            }
        ]
        
        response = await provider.chat(messages, functions=functions)
        
        assert response.content == ""
        assert response.function_calls is not None
        assert len(response.function_calls) == 1
        assert response.function_calls[0].name == "test_function"
        assert response.function_calls[0].arguments == {"param1": "value1"}
    
    @pytest.mark.asyncio
    async def test_chat_with_function_message(self):
        """测试包含 function 消息的对话"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "函数执行完成"
        mock_message.tool_calls = None
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        
        provider.client.chat.completions.create = Mock(return_value=mock_response)
        
        messages = [
            LLMMessage(role="user", content="调用函数"),
            LLMMessage(role="assistant", content=""),
            LLMMessage(role="function", content='{"result": "success"}', name="test_function")
        ]
        
        response = await provider.chat(messages)
        
        # 检查请求中是否包含了 function 消息的 name
        call_args = provider.client.chat.completions.create.call_args
        assert call_args is not None
        api_messages = call_args.kwargs["messages"]
        function_msg = [m for m in api_messages if m["role"] == "function"][0]
        assert function_msg["name"] == "test_function"
    
    @pytest.mark.skipif(
        not get_test_config()["use_real_api"],
        reason="需要设置 AGENT_TEST_USE_REAL_API=true 进行真实 API 测试"
    )
    @pytest.mark.asyncio
    async def test_chat_real_api(self):
        """测试真实 API 调用（需要环境变量配置）"""
        config = get_test_config()
        if config["provider_type"] != "openai":
            pytest.skip("当前配置的 Provider 类型不是 openai")
        
        if not config["api_key"]:
            pytest.skip("未设置 AGENT_TEST_API_KEY")
        
        provider = OpenAIProvider(
            api_key=config["api_key"],
            model=config["model"]
        )
        
        messages = [
            LLMMessage(role="user", content="请说'测试成功'")
        ]
        
        response = await provider.chat(messages, temperature=0.1)
        
        assert response.content is not None
        assert len(response.content) > 0
        # 真实 API 测试，只检查基本结构
        assert isinstance(response.content, str)


class TestClaudeProvider:
    """测试 ClaudeProvider"""
    
    def test_init(self):
        """测试初始化"""
        provider = ClaudeProvider(api_key="test-key", model="claude-sonnet-4-20250514")
        
        assert provider.model_name == "claude-sonnet-4-20250514"
        assert provider.supports_function_calling() is True
        assert provider.client is not None
    
    @pytest.mark.asyncio
    async def test_chat_simple(self):
        """测试简单对话（Mock）"""
        provider = ClaudeProvider(api_key="test-key", model="claude-sonnet-4-20250514")
        
        # Mock Claude 客户端响应
        mock_response = Mock()
        mock_text_block = Mock()
        mock_text_block.type = "text"
        mock_text_block.text = "这是测试回复"
        mock_response.content = [mock_text_block]
        mock_response.stop_reason = "end_turn"
        
        provider.client.messages.create = Mock(return_value=mock_response)
        
        messages = [
            LLMMessage(role="user", content="你好")
        ]
        
        response = await provider.chat(messages)
        
        assert response.content == "这是测试回复"
        assert response.function_calls is None
        assert response.finish_reason == "end_turn"
    
    @pytest.mark.asyncio
    async def test_chat_with_system_message(self):
        """测试包含 system 消息的对话"""
        provider = ClaudeProvider(api_key="test-key", model="claude-sonnet-4-20250514")
        
        mock_response = Mock()
        mock_text_block = Mock()
        mock_text_block.type = "text"
        mock_text_block.text = "回复"
        mock_response.content = [mock_text_block]
        mock_response.stop_reason = "end_turn"
        
        provider.client.messages.create = Mock(return_value=mock_response)
        
        messages = [
            LLMMessage(role="system", content="你是一个助手"),
            LLMMessage(role="user", content="你好")
        ]
        
        response = await provider.chat(messages)
        
        # 检查 system 消息是否被单独提取
        call_args = provider.client.messages.create.call_args
        assert call_args is not None
        assert "system" in call_args.kwargs
        assert call_args.kwargs["system"] == "你是一个助手"
        
        # messages 中不应该包含 system 消息
        api_messages = call_args.kwargs["messages"]
        assert not any(m["role"] == "system" for m in api_messages)
    
    @pytest.mark.asyncio
    async def test_chat_with_function_calling(self):
        """测试带函数调用的对话（Mock）"""
        provider = ClaudeProvider(api_key="test-key", model="claude-sonnet-4-20250514")
        
        # Mock Claude 客户端响应（包含工具使用）
        mock_response = Mock()
        mock_tool_use_block = Mock()
        mock_tool_use_block.type = "tool_use"
        mock_tool_use_block.name = "test_function"
        mock_tool_use_block.input = {"param1": "value1"}
        mock_response.content = [mock_tool_use_block]
        mock_response.stop_reason = "tool_use"
        
        provider.client.messages.create = Mock(return_value=mock_response)
        
        messages = [
            LLMMessage(role="user", content="调用函数")
        ]
        functions = [
            {
                "name": "test_function",
                "description": "测试函数",
                "input_schema": {
                    "type": "object",
                    "properties": {"param1": {"type": "string"}},
                    "required": ["param1"]
                }
            }
        ]
        
        response = await provider.chat(messages, functions=functions)
        
        assert response.content == ""
        assert response.function_calls is not None
        assert len(response.function_calls) == 1
        assert response.function_calls[0].name == "test_function"
        assert response.function_calls[0].arguments == {"param1": "value1"}
    
    @pytest.mark.asyncio
    async def test_chat_mixed_content(self):
        """测试混合内容（文本 + 工具使用）"""
        provider = ClaudeProvider(api_key="test-key", model="claude-sonnet-4-20250514")
        
        mock_response = Mock()
        mock_text_block = Mock()
        mock_text_block.type = "text"
        mock_text_block.text = "我需要调用函数"
        mock_tool_use_block = Mock()
        mock_tool_use_block.type = "tool_use"
        mock_tool_use_block.name = "test_function"
        mock_tool_use_block.input = {}
        mock_response.content = [mock_text_block, mock_tool_use_block]
        mock_response.stop_reason = "tool_use"
        
        provider.client.messages.create = Mock(return_value=mock_response)
        
        messages = [LLMMessage(role="user", content="测试")]
        response = await provider.chat(messages)
        
        assert response.content == "我需要调用函数"
        assert response.function_calls is not None
        assert len(response.function_calls) == 1
    
    @pytest.mark.skipif(
        not get_test_config()["use_real_api"],
        reason="需要设置 AGENT_TEST_USE_REAL_API=true 进行真实 API 测试"
    )
    @pytest.mark.asyncio
    async def test_chat_real_api(self):
        """测试真实 API 调用（需要环境变量配置）"""
        config = get_test_config()
        if config["provider_type"] not in ["claude", "anthropic"]:
            pytest.skip("当前配置的 Provider 类型不是 claude")
        
        if not config["api_key"]:
            pytest.skip("未设置 AGENT_TEST_API_KEY")
        
        provider = ClaudeProvider(
            api_key=config["api_key"],
            model=config["model"]
        )
        
        messages = [
            LLMMessage(role="user", content="请说'测试成功'")
        ]
        
        response = await provider.chat(messages, temperature=0.1)
        
        assert response.content is not None
        assert len(response.content) > 0


class TestOpenSourceProvider:
    """测试 OpenSourceProvider"""
    
    def test_init(self):
        """测试初始化"""
        provider = OpenSourceProvider(
            base_url="http://localhost:8000/v1",
            model="qwen"
        )
        
        assert provider.model_name == "qwen"
        assert provider.base_url == "http://localhost:8000/v1"
        assert provider.supports_function_calling() is True
    
    def test_init_with_api_key(self):
        """测试使用 API Key 初始化"""
        provider = OpenSourceProvider(
            base_url="https://api.example.com/v1",
            model="custom-model",
            api_key="test-key"
        )
        
        assert provider.api_key == "test-key"
    
    def test_init_with_timeout(self):
        """测试使用自定义超时时间初始化"""
        provider = OpenSourceProvider(
            base_url="http://localhost:8000/v1",
            model="qwen",
            timeout=120.0
        )
        
        assert provider.timeout == 120.0
    
    def test_init_strip_trailing_slash(self):
        """测试自动去除 URL 末尾的斜杠"""
        provider = OpenSourceProvider(
            base_url="http://localhost:8000/v1/",
            model="qwen"
        )
        
        assert provider.base_url == "http://localhost:8000/v1"
    
    @pytest.mark.asyncio
    async def test_chat_simple(self):
        """测试简单对话（Mock）"""
        provider = OpenSourceProvider(
            base_url="http://localhost:8000/v1",
            model="qwen"
        )
        
        # Mock HTTP 响应
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": "这是测试回复",
                    "role": "assistant"
                },
                "finish_reason": "stop"
            }]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            messages = [
                LLMMessage(role="user", content="你好")
            ]
            
            response = await provider.chat(messages)
            
            assert response.content == "这是测试回复"
            assert response.function_calls is None
            assert response.finish_reason == "stop"
            
            # 检查请求 URL
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "/chat/completions" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_chat_with_api_key(self):
        """测试使用 API Key 的对话"""
        provider = OpenSourceProvider(
            base_url="http://localhost:8000/v1",
            model="qwen",
            api_key="test-key"
        )
        
        mock_response_data = {
            "choices": [{
                "message": {"content": "回复", "role": "assistant"},
                "finish_reason": "stop"
            }]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            messages = [LLMMessage(role="user", content="测试")]
            await provider.chat(messages)
            
            # 检查请求头中是否包含 Authorization
            call_args = mock_client.post.call_args
            headers = call_args[1]["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer test-key"
    
    @pytest.mark.asyncio
    async def test_chat_with_function_calling(self):
        """测试带函数调用的对话（Mock）"""
        provider = OpenSourceProvider(
            base_url="http://localhost:8000/v1",
            model="qwen"
        )
        
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": None,
                    "role": "assistant",
                    "tool_calls": [{
                        "type": "function",
                        "function": {
                            "name": "test_function",
                            "arguments": '{"param1": "value1"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            messages = [LLMMessage(role="user", content="调用函数")]
            functions = [{
                "name": "test_function",
                "description": "测试函数",
                "parameters": {
                    "type": "object",
                    "properties": {"param1": {"type": "string"}},
                    "required": ["param1"]
                }
            }]
            
            response = await provider.chat(messages, functions=functions)
            
            assert response.function_calls is not None
            assert len(response.function_calls) == 1
            assert response.function_calls[0].name == "test_function"
            assert response.function_calls[0].arguments == {"param1": "value1"}
            
            # 检查请求体中是否包含 tools
            call_args = mock_client.post.call_args
            request_body = call_args[1]["json"]
            assert "tools" in request_body
            assert len(request_body["tools"]) == 1
    
    @pytest.mark.asyncio
    async def test_chat_http_error(self):
        """测试 HTTP 错误处理"""
        provider = OpenSourceProvider(
            base_url="http://localhost:8000/v1",
            model="qwen"
        )
        
        import httpx
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError("网络错误"))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            messages = [LLMMessage(role="user", content="测试")]
            
            with pytest.raises(httpx.HTTPError):
                await provider.chat(messages)
    
    @pytest.mark.skipif(
        not get_test_config()["use_real_api"],
        reason="需要设置 AGENT_TEST_USE_REAL_API=true 进行真实 API 测试"
    )
    @pytest.mark.skipif(
        not get_test_config()["base_url"],
        reason="需要设置 AGENT_TEST_BASE_URL 进行真实 API 测试"
    )
    @pytest.mark.asyncio
    async def test_chat_real_api(self):
        """测试真实 API 调用（需要环境变量配置）"""
        config = get_test_config()
        if config["provider_type"] not in ["open_source", "custom"]:
            pytest.skip("当前配置的 Provider 类型不是 open_source")
        
        if not config["base_url"]:
            pytest.skip("未设置 AGENT_TEST_BASE_URL")
        
        provider = OpenSourceProvider(
            base_url=config["base_url"],
            model=config["model"],
            api_key=config.get("api_key") or None
        )
        
        messages = [
            LLMMessage(role="user", content="请说'测试成功'")
        ]
        
        response = await provider.chat(messages, temperature=0.1)
        
        assert response.content is not None
        assert len(response.content) > 0


class TestProviderIntegration:
    """Provider 集成测试"""
    
    @pytest.mark.asyncio
    async def test_provider_interface(self):
        """测试所有 Provider 都实现了接口"""
        providers = [
            OpenAIProvider(api_key="test", model="gpt-4o-mini"),
            ClaudeProvider(api_key="test", model="claude-sonnet-4-20250514"),
            OpenSourceProvider(base_url="http://localhost:8000/v1", model="qwen")
        ]
        
        for provider in providers:
            assert isinstance(provider, LLMProvider)
            assert hasattr(provider, "model_name")
            assert hasattr(provider, "supports_function_calling")
            assert hasattr(provider, "chat")
            assert callable(provider.supports_function_calling)
            assert callable(provider.chat)

