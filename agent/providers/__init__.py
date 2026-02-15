"""LLM 提供商模块 - 支持多种大模型接入。

本模块提供了统一的 LLM 提供商接口和工厂函数，支持多种大语言模型：
- OpenAI（GPT 系列）
- Anthropic（Claude 系列）
- 开源模型（兼容 OpenAI API 格式）

所有提供商都实现 LLMProvider 接口，可以无缝切换使用。
"""

from typing import Any

from agent.providers.base import LLMProvider
from agent.providers.openai_provider import OpenAIProvider
from agent.providers.claude_provider import ClaudeProvider
from agent.providers.open_source_provider import OpenSourceProvider

__all__ = [
    "LLMProvider",
    "OpenAIProvider",
    "ClaudeProvider",
    "OpenSourceProvider",
    "create_provider",
]


def create_provider(provider_type: str, **kwargs: Any) -> LLMProvider:
    """创建 LLM 提供商实例的工厂函数。

    根据提供商类型创建对应的 LLMProvider 实例。支持的提供商类型包括：
    - "openai" 或 "OpenAI": OpenAI GPT 系列模型
    - "claude" 或 "anthropic": Anthropic Claude 系列模型
    - "open_source" 或 "custom": 兼容 OpenAI API 格式的开源模型

    Args:
        provider_type: 提供商类型字符串，不区分大小写。支持的值：
            - "openai": OpenAI 提供商
            - "claude" 或 "anthropic": Claude 提供商
            - "open_source" 或 "custom": 开源模型提供商
        **kwargs: 提供商特定的初始化参数：
            - OpenAI: api_key (str), model (str, 默认 "gpt-4o-mini"),
              base_url (Optional[str])
            - Claude: api_key (str), model (str, 默认 "claude-sonnet-4-20250514")
            - OpenSource: base_url (str), model (str), api_key (Optional[str]),
              timeout (float, 默认 60.0)

    Returns:
        实现了 LLMProvider 接口的提供商实例。

    Raises:
        ValueError: 如果 provider_type 不是支持的提供商类型。

    Examples:
        ```python
        # 创建 OpenAI 提供商
        provider = create_provider("openai", api_key="sk-...", model="gpt-4")

        # 创建 Claude 提供商
        provider = create_provider("claude", api_key="sk-ant-...", model="claude-3")

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
    elif provider_type == "claude" or provider_type == "anthropic":
        return ClaudeProvider(**kwargs)
    elif provider_type == "open_source" or provider_type == "custom":
        return OpenSourceProvider(**kwargs)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

