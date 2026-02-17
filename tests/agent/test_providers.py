"""测试 LLM Provider 实现。

覆盖：
- OpenAIProvider：初始化、消息转换、函数调用、tool 消息
- ClaudeProvider：初始化、system 提取、函数调用、thinking 解析
- MiniMaxProvider：初始化、继承关系、默认参数
- OpenSourceProvider：初始化、HTTP 请求、函数调用、错误处理
- Provider 接口一致性
- create_provider 工厂函数
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from agent.providers import create_provider
from agent.providers.base import (
    LLMProvider, LLMMessage, LLMResponse, FunctionCall,
)
from agent.providers.openai_provider import OpenAIProvider
from agent.providers.anthropic_base import AnthropicBaseProvider
from agent.providers.claude_provider import ClaudeProvider
from agent.providers.minimax_provider import MiniMaxProvider
from agent.providers.open_source_provider import OpenSourceProvider


# ================================================================
# OpenAIProvider
# ================================================================

class TestOpenAIProvider:

    def test_init_default(self):
        p = OpenAIProvider(api_key="k", model="gpt-4o-mini")
        assert p.model_name == "gpt-4o-mini"
        assert p.supports_function_calling() is True

    def test_init_custom_base_url(self):
        p = OpenAIProvider(
            api_key="k", model="m",
            base_url="https://api.example.com/v1",
        )
        assert str(p.client.base_url).rstrip("/") == \
            "https://api.example.com/v1"

    @pytest.mark.asyncio
    async def test_chat_simple(self):
        p = OpenAIProvider(api_key="k", model="m")
        mock_msg = Mock(content="回复", tool_calls=None)
        mock_choice = Mock(message=mock_msg, finish_reason="stop")
        p.client.chat.completions.create = Mock(
            return_value=Mock(choices=[mock_choice])
        )

        resp = await p.chat([LLMMessage(role="user", content="你好")])
        assert resp.content == "回复"
        assert resp.function_calls is None

    @pytest.mark.asyncio
    async def test_chat_function_calling(self):
        p = OpenAIProvider(api_key="k", model="m")
        mock_function = Mock(arguments='{"a": 1}')
        mock_function.name = "fn"
        tc = Mock(
            id="call_abc", type="function",
            function=mock_function,
        )
        mock_msg = Mock(content=None, tool_calls=[tc])
        mock_choice = Mock(message=mock_msg, finish_reason="tool_calls")
        p.client.chat.completions.create = Mock(
            return_value=Mock(choices=[mock_choice])
        )

        resp = await p.chat(
            [LLMMessage(role="user", content="call")],
            functions=[{"name": "fn", "description": "d", "parameters": {}}],
        )
        assert resp.function_calls is not None
        assert resp.function_calls[0].name == "fn"
        assert resp.function_calls[0].id == "call_abc"
        assert resp.function_calls[0].arguments == {"a": 1}

    @pytest.mark.asyncio
    async def test_tool_message_conversion(self):
        """assistant + tool_calls → tool 消息应正确转换。"""
        p = OpenAIProvider(api_key="k", model="m")
        mock_msg = Mock(content="done", tool_calls=None)
        mock_choice = Mock(message=mock_msg, finish_reason="stop")
        p.client.chat.completions.create = Mock(
            return_value=Mock(choices=[mock_choice])
        )

        messages = [
            LLMMessage(role="user", content="go"),
            LLMMessage(
                role="assistant", content="",
                tool_calls=[
                    FunctionCall(name="fn", arguments={"x": 1}, id="c1")
                ],
            ),
            LLMMessage(
                role="tool", content='{"r": 1}',
                name="fn", tool_call_id="c1",
            ),
        ]
        await p.chat(messages)

        api_msgs = p.client.chat.completions.create.call_args.kwargs[
            "messages"
        ]
        assistant_msg = [m for m in api_msgs if m["role"] == "assistant"][0]
        assert assistant_msg["tool_calls"][0]["id"] == "c1"
        tool_msg = [m for m in api_msgs if m["role"] == "tool"][0]
        assert tool_msg["tool_call_id"] == "c1"


# ================================================================
# ClaudeProvider
# ================================================================

class TestClaudeProvider:

    def test_init(self):
        p = ClaudeProvider(api_key="k")
        assert p.model_name == "claude-sonnet-4-20250514"
        assert p.supports_function_calling() is True
        assert isinstance(p, AnthropicBaseProvider)

    @pytest.mark.asyncio
    async def test_chat_simple(self):
        p = ClaudeProvider(api_key="k")
        text_block = Mock(type="text", text="回复")
        mock_resp = Mock(content=[text_block], stop_reason="end_turn")
        # 不设 usage 属性
        if hasattr(mock_resp, "usage"):
            del mock_resp.usage
        p.client.messages.create = Mock(return_value=mock_resp)

        resp = await p.chat([LLMMessage(role="user", content="你好")])
        assert resp.content == "回复"
        assert resp.function_calls is None

    @pytest.mark.asyncio
    async def test_system_message_extraction(self):
        p = ClaudeProvider(api_key="k")
        text_block = Mock(type="text", text="ok")
        mock_resp = Mock(content=[text_block], stop_reason="end_turn")
        if hasattr(mock_resp, "usage"):
            del mock_resp.usage
        p.client.messages.create = Mock(return_value=mock_resp)

        await p.chat([
            LLMMessage(role="system", content="你是助手"),
            LLMMessage(role="user", content="hi"),
        ])

        kwargs = p.client.messages.create.call_args.kwargs
        assert kwargs["system"] == "你是助手"
        assert all(
            m["role"] != "system" for m in kwargs["messages"]
        )

    @pytest.mark.asyncio
    async def test_tool_use_response(self):
        p = ClaudeProvider(api_key="k")
        tool_block = Mock(
            type="tool_use", id="toolu_123",
            input={"a": 1},
        )
        tool_block.name = "fn"
        mock_resp = Mock(content=[tool_block], stop_reason="tool_use")
        if hasattr(mock_resp, "usage"):
            del mock_resp.usage
        p.client.messages.create = Mock(return_value=mock_resp)

        resp = await p.chat(
            [LLMMessage(role="user", content="call")],
            functions=[{
                "name": "fn", "description": "d",
                "parameters": {"type": "object", "properties": {}},
            }],
        )
        assert resp.function_calls is not None
        assert resp.function_calls[0].name == "fn"
        assert resp.function_calls[0].id == "toolu_123"

    @pytest.mark.asyncio
    async def test_thinking_block_parsed(self):
        """thinking 块应被解析到 metadata。"""
        p = ClaudeProvider(api_key="k")
        thinking_block = Mock(type="thinking", thinking="我在思考...")
        text_block = Mock(type="text", text="结果")
        mock_resp = Mock(
            content=[thinking_block, text_block],
            stop_reason="end_turn",
        )
        if hasattr(mock_resp, "usage"):
            del mock_resp.usage
        p.client.messages.create = Mock(return_value=mock_resp)

        resp = await p.chat([LLMMessage(role="user", content="思考")])
        assert resp.content == "结果"
        assert resp.metadata is not None
        assert "thinking" in resp.metadata
        assert resp.metadata["thinking"] == "我在思考..."

    @pytest.mark.asyncio
    async def test_mixed_content(self):
        """文本 + tool_use 混合响应。"""
        p = ClaudeProvider(api_key="k")
        text_block = Mock(type="text", text="需要调用函数")
        tool_block = Mock(
            type="tool_use", id="toolu_mix",
            name="fn", input={},
        )
        mock_resp = Mock(
            content=[text_block, tool_block],
            stop_reason="tool_use",
        )
        if hasattr(mock_resp, "usage"):
            del mock_resp.usage
        p.client.messages.create = Mock(return_value=mock_resp)

        resp = await p.chat([LLMMessage(role="user", content="test")])
        assert resp.content == "需要调用函数"
        assert resp.function_calls is not None
        assert len(resp.function_calls) == 1

    @pytest.mark.asyncio
    async def test_provider_extras_passthrough(self):
        """provider_extras 应在下一轮请求中被使用。"""
        p = ClaudeProvider(api_key="k")
        text_block = Mock(type="text", text="done")
        mock_resp = Mock(
            content=[text_block], stop_reason="end_turn",
        )
        if hasattr(mock_resp, "usage"):
            del mock_resp.usage
        p.client.messages.create = Mock(return_value=mock_resp)

        original_blocks = [
            {"type": "text", "text": "thinking..."},
            {"type": "tool_use", "id": "t1", "name": "fn", "input": {}},
        ]
        messages = [
            LLMMessage(role="user", content="go"),
            LLMMessage(
                role="assistant", content="",
                provider_extras=original_blocks,
            ),
            LLMMessage(
                role="tool", content="result",
                name="fn", tool_call_id="t1",
            ),
        ]
        await p.chat(messages)

        api_msgs = p.client.messages.create.call_args.kwargs["messages"]
        assistant_msg = [m for m in api_msgs if m["role"] == "assistant"][0]
        assert assistant_msg["content"] is original_blocks


# ================================================================
# MiniMaxProvider
# ================================================================

class TestMiniMaxProvider:

    def test_init_default(self):
        p = MiniMaxProvider(api_key="k")
        assert p.model_name == "MiniMax-M2.5"
        assert isinstance(p, AnthropicBaseProvider)
        assert p._default_max_tokens == 4096

    def test_init_custom_base_url(self):
        p = MiniMaxProvider(
            api_key="k",
            base_url="https://api.minimax.io/anthropic",
        )
        assert p.model_name == "MiniMax-M2.5"

    def test_default_base_url(self):
        """默认应使用国内 API 地址。"""
        p = MiniMaxProvider(api_key="k")
        # AnthropicBaseProvider 会把 base_url 传给 Anthropic client
        # 我们只验证创建成功
        assert p.supports_function_calling() is True

    def test_inherits_anthropic_base(self):
        """应继承 AnthropicBaseProvider 的所有方法。"""
        p = MiniMaxProvider(api_key="k")
        assert hasattr(p, "_convert_messages")
        assert hasattr(p, "_parse_response")
        assert hasattr(p, "_extract_system")
        assert hasattr(p, "_convert_functions")


# ================================================================
# OpenSourceProvider
# ================================================================

class TestOpenSourceProvider:

    def test_init(self):
        p = OpenSourceProvider(base_url="http://localhost:8000/v1", model="q")
        assert p.model_name == "q"
        assert p.base_url == "http://localhost:8000/v1"
        assert p.supports_function_calling() is True

    def test_init_strips_trailing_slash(self):
        p = OpenSourceProvider(
            base_url="http://localhost:8000/v1/", model="q"
        )
        assert p.base_url == "http://localhost:8000/v1"

    def test_init_with_api_key_and_timeout(self):
        p = OpenSourceProvider(
            base_url="http://x/v1", model="m",
            api_key="k", timeout=120.0,
        )
        assert p.api_key == "k"
        assert p.timeout == 120.0

    @pytest.mark.asyncio
    async def test_chat_simple(self):
        p = OpenSourceProvider(base_url="http://x/v1", model="m")
        data = {
            "choices": [{
                "message": {"content": "回复", "role": "assistant"},
                "finish_reason": "stop",
            }]
        }
        with patch("httpx.AsyncClient") as mc:
            client = AsyncMock()
            resp = Mock(json=Mock(return_value=data), raise_for_status=Mock())
            client.post = AsyncMock(return_value=resp)
            mc.return_value.__aenter__.return_value = client

            result = await p.chat([LLMMessage(role="user", content="hi")])
            assert result.content == "回复"

    @pytest.mark.asyncio
    async def test_chat_with_function_calling(self):
        p = OpenSourceProvider(base_url="http://x/v1", model="m")
        data = {
            "choices": [{
                "message": {
                    "content": None, "role": "assistant",
                    "tool_calls": [{
                        "id": "c1", "type": "function",
                        "function": {
                            "name": "fn",
                            "arguments": '{"a": 1}',
                        },
                    }],
                },
                "finish_reason": "tool_calls",
            }]
        }
        with patch("httpx.AsyncClient") as mc:
            client = AsyncMock()
            resp = Mock(json=Mock(return_value=data), raise_for_status=Mock())
            client.post = AsyncMock(return_value=resp)
            mc.return_value.__aenter__.return_value = client

            result = await p.chat(
                [LLMMessage(role="user", content="call")],
                functions=[{"name": "fn", "description": "d", "parameters": {}}],
            )
            assert result.function_calls is not None
            assert result.function_calls[0].id == "c1"

    @pytest.mark.asyncio
    async def test_chat_http_error(self):
        import httpx
        p = OpenSourceProvider(base_url="http://x/v1", model="m")
        with patch("httpx.AsyncClient") as mc:
            client = AsyncMock()
            client.post = AsyncMock(side_effect=httpx.HTTPError("fail"))
            mc.return_value.__aenter__.return_value = client

            with pytest.raises(httpx.HTTPError):
                await p.chat([LLMMessage(role="user", content="hi")])

    @pytest.mark.asyncio
    async def test_auth_header_sent(self):
        p = OpenSourceProvider(
            base_url="http://x/v1", model="m", api_key="my-key"
        )
        data = {
            "choices": [{
                "message": {"content": "ok", "role": "assistant"},
                "finish_reason": "stop",
            }]
        }
        with patch("httpx.AsyncClient") as mc:
            client = AsyncMock()
            resp = Mock(json=Mock(return_value=data), raise_for_status=Mock())
            client.post = AsyncMock(return_value=resp)
            mc.return_value.__aenter__.return_value = client

            await p.chat([LLMMessage(role="user", content="hi")])
            headers = client.post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer my-key"


# ================================================================
# Provider 接口一致性 & 工厂函数
# ================================================================

class TestProviderInterface:

    def test_all_providers_implement_interface(self):
        providers = [
            OpenAIProvider(api_key="k", model="m"),
            ClaudeProvider(api_key="k"),
            MiniMaxProvider(api_key="k"),
            OpenSourceProvider(base_url="http://x/v1", model="m"),
        ]
        for p in providers:
            assert isinstance(p, LLMProvider)
            assert hasattr(p, "model_name")
            assert hasattr(p, "supports_function_calling")
            assert hasattr(p, "chat")
            assert callable(p.supports_function_calling)
            assert callable(p.chat)


class TestCreateProvider:

    def test_create_openai(self):
        p = create_provider("openai", api_key="k", model="m")
        assert isinstance(p, OpenAIProvider)

    def test_create_claude(self):
        p = create_provider("claude", api_key="k")
        assert isinstance(p, ClaudeProvider)

    def test_create_anthropic_alias(self):
        p = create_provider("anthropic", api_key="k")
        assert isinstance(p, ClaudeProvider)

    def test_create_minimax(self):
        p = create_provider("minimax", api_key="k")
        assert isinstance(p, MiniMaxProvider)

    def test_create_open_source(self):
        p = create_provider(
            "open_source", base_url="http://x/v1", model="m"
        )
        assert isinstance(p, OpenSourceProvider)

    def test_create_custom_alias(self):
        p = create_provider("custom", base_url="http://x/v1", model="m")
        assert isinstance(p, OpenSourceProvider)

    def test_create_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider("unknown", api_key="k")

    def test_case_insensitive(self):
        p = create_provider("MINIMAX", api_key="k")
        assert isinstance(p, MiniMaxProvider)
