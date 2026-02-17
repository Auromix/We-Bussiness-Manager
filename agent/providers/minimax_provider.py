"""MiniMax 提供商实现。

本模块实现了 MiniMax 系列模型的提供商，通过 Anthropic SDK 兼容接口
调用 MiniMax 模型。继承自 AnthropicBaseProvider，共享消息转换和
响应解析逻辑。

MiniMax 模型特点：
    - 支持 Interleaved Thinking（交错思维链）
    - 优秀的工具使用能力
    - 支持长上下文（204,800 tokens）
    - 在 Code & Agent Benchmark 上达到 SOTA 水平

支持的模型：
    - MiniMax-M2.5（推荐）
    - MiniMax-M2.5-highspeed
    - MiniMax-M2.1
    - MiniMax-M2.1-highspeed
    - MiniMax-M2
"""
from typing import Optional

from agent.providers.anthropic_base import AnthropicBaseProvider


class MiniMaxProvider(AnthropicBaseProvider):
    """MiniMax 模型提供商（通过 Anthropic SDK 兼容接口）。

    继承自 AnthropicBaseProvider，所有消息转换、响应解析、
    tool_use_id 跟踪等逻辑由基类统一处理。

    相比 Claude，MiniMax 的默认参数有所不同：
    - 默认 base_url 为 MiniMax Anthropic 兼容接口
    - 默认 max_tokens 为 4096（支持更长输出）

    Thinking 内容会自动被基类解析并存入 metadata["thinking"]。

    Example:
        ```python
        # 使用国内 API
        provider = MiniMaxProvider(
            api_key="sk-api-...",
            model="MiniMax-M2.5"
        )

        # 使用国际 API
        provider = MiniMaxProvider(
            api_key="sk-api-...",
            model="MiniMax-M2.5",
            base_url="https://api.minimax.io/anthropic"
        )
        ```
    """

    def __init__(
        self,
        api_key: str,
        model: str = "MiniMax-M2.5",
        base_url: Optional[str] = None,
    ) -> None:
        """初始化 MiniMax 提供商。

        Args:
            api_key: MiniMax API Key。
            model: 模型名称，默认 "MiniMax-M2.5"。
            base_url: API 基础 URL，默认为 MiniMax Anthropic 兼容接口
                （https://api.minimaxi.com/anthropic）。
                国际用户可使用 https://api.minimax.io/anthropic。
        """
        if not base_url:
            base_url = "https://api.minimaxi.com/anthropic"
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            default_max_tokens=4096,
        )
