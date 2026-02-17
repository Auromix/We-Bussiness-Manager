"""LLM 提供商模块 - 支持多种大模型接入。

本模块提供了统一的 LLM 提供商接口和工厂函数，支持多种大语言模型：
- OpenAI（GPT 系列）
- Anthropic（Claude 系列）
- MiniMax（M2.5、M2.1 等系列）
- 开源模型（兼容 OpenAI API 格式）

架构：
    LLMProvider (base.py)          ← 抽象基类
    ├── OpenAIProvider             ← OpenAI GPT 系列
    ├── AnthropicBaseProvider       ← Anthropic SDK 共享基类
    │   ├── ClaudeProvider          ← Claude 系列
    │   └── MiniMaxProvider         ← MiniMax 系列
    └── OpenSourceProvider          ← OpenAI API 兼容的开源模型

所有提供商都实现 LLMProvider 接口，可以无缝切换使用。

接入新模型：
    1. 继承 LLMProvider（或 AnthropicBaseProvider）
    2. 实现 chat()、supports_function_calling()、model_name
    3. 在下方 create_provider() 中注册
"""
from typing import Any

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall
from agent.providers.openai_provider import OpenAIProvider
from agent.providers.anthropic_base import AnthropicBaseProvider
from agent.providers.claude_provider import ClaudeProvider
from agent.providers.minimax_provider import MiniMaxProvider
from agent.providers.open_source_provider import OpenSourceProvider

__all__ = [
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "FunctionCall",
    "AnthropicBaseProvider",
    "OpenAIProvider",
    "ClaudeProvider",
    "MiniMaxProvider",
    "OpenSourceProvider",
    "create_provider",
]


def create_provider(provider_type: str, **kwargs: Any) -> LLMProvider:
    """创建 LLM 提供商实例的工厂函数。

    根据提供商类型创建对应的 LLMProvider 实例。对用户完全透明，
    只需指定类型即可获得可用的 Provider。

    Args:
        provider_type: 提供商类型字符串（不区分大小写）：
            - "openai": OpenAI GPT 系列
            - "claude" / "anthropic": Claude 系列
            - "minimax": MiniMax 系列
            - "open_source" / "custom": 兼容 OpenAI API 的开源模型
        **kwargs: 提供商初始化参数：
            - OpenAI: api_key, model, base_url
            - Claude: api_key, model, base_url
            - MiniMax: api_key, model, base_url
            - OpenSource: base_url, model, api_key, timeout

    Returns:
        LLMProvider 实例。

    Raises:
        ValueError: 不支持的提供商类型。

    Examples:
        ```python
        # 创建 OpenAI 提供商
        provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")

        # 创建 Claude 提供商
        provider = create_provider("claude", api_key="sk-ant-...")

        # 创建 MiniMax 提供商
        provider = create_provider("minimax", api_key="sk-api-...")

        # 创建开源模型提供商
        provider = create_provider(
            "open_source",
            base_url="http://localhost:8000/v1",
            model="qwen"
        )
        ```
    """
    provider_type = provider_type.lower()

    if provider_type == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_type in ("claude", "anthropic"):
        return ClaudeProvider(**kwargs)
    elif provider_type == "minimax":
        return MiniMaxProvider(**kwargs)
    elif provider_type in ("open_source", "custom"):
        return OpenSourceProvider(**kwargs)
    else:
        raise ValueError(
            f"Unknown provider type: {provider_type}. "
            f"Supported: openai, claude, anthropic, minimax, "
            f"open_source, custom"
        )
