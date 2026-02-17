"""Anthropic Claude 提供商实现。

本模块实现了 Anthropic Claude 系列模型的提供商。
继承自 AnthropicBaseProvider，共享消息转换和响应解析逻辑。

支持的模型：
    - claude-sonnet-4-20250514（推荐）
    - claude-opus-3-20240229
    - claude-3-5-sonnet-20241022
    - 以及其他 Claude 系列模型
"""
from typing import Optional

from agent.providers.anthropic_base import AnthropicBaseProvider


class ClaudeProvider(AnthropicBaseProvider):
    """Anthropic Claude 模型提供商。

    继承自 AnthropicBaseProvider，所有消息转换、响应解析、
    tool_use_id 跟踪等逻辑由基类统一处理。

    Example:
        ```python
        # 使用 Anthropic 官方 API
        provider = ClaudeProvider(
            api_key="sk-ant-...",
            model="claude-sonnet-4-20250514"
        )

        # 使用兼容 API 服务
        provider = ClaudeProvider(
            api_key="sk-...",
            model="claude-sonnet-4-20250514",
            base_url="https://api.example.com"
        )
        ```
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        base_url: Optional[str] = None,
    ) -> None:
        """初始化 Claude 提供商。

        Args:
            api_key: Anthropic API Key。
            model: 模型名称，默认 "claude-sonnet-4-20250514"。
            base_url: 自定义 API 基础 URL（可选）。
        """
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            default_max_tokens=2048,
        )
