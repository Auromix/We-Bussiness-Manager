"""Anthropic SDK 兼容提供商基类。

本模块实现了基于 Anthropic SDK 的提供商基类，为 Claude 和 MiniMax
等使用 Anthropic 兼容接口的模型提供共享的消息转换和响应解析逻辑。

设计目标：
    - 消除 Claude 和 MiniMax 之间的代码重复
    - 统一处理 Anthropic 特有的消息格式（system 独立、tool_result、content blocks）
    - 通过 provider_extras 机制透明保留 thinking/tool_use 块，
      无需在 Provider 层维护复杂的缓存/队列状态

继承指南：
    子类只需设置模型名称、base_url 和默认参数即可：
    ```python
    class MyAnthropicProvider(AnthropicBaseProvider):
        def __init__(self, api_key, model="my-model"):
            super().__init__(api_key=api_key, model=model,
                             base_url="https://api.example.com",
                             default_max_tokens=4096)
    ```
"""
from typing import List, Dict, Any, Optional, Tuple
from anthropic import Anthropic
from loguru import logger

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall


class AnthropicBaseProvider(LLMProvider):
    """Anthropic SDK 兼容提供商基类。

    封装了 Anthropic SDK 的完整调用逻辑，包括：
    - 消息格式转换（LLMMessage ↔ Anthropic API 格式）
    - System 消息的独立提取（Anthropic 要求单独传递）
    - 工具调用 (tool_use) 与结果 (tool_result) 的格式处理
    - Thinking 块（Interleaved Thinking）的解析
    - tool_use_id 的自动跟踪（通过 provider_extras 机制）

    核心机制 - provider_extras 透传：
        当 LLM 返回包含 tool_use 的响应时，原始 content blocks
        会通过 LLMResponse.raw_response 传递给 Agent。Agent 将其
        存入 assistant 消息的 provider_extras 字段。下一轮请求时，
        本基类从 provider_extras 恢复完整的 content blocks（包含
        thinking、text、tool_use 等），确保 Anthropic API 收到
        完整的上下文，无需任何缓存或状态管理。

    Attributes:
        client: Anthropic 客户端实例。
        _model: 模型名称。
        _default_max_tokens: 默认最大 token 数。
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        default_max_tokens: int = 2048
    ) -> None:
        """初始化 Anthropic 兼容提供商。

        Args:
            api_key: API Key，用于身份验证。
            model: 模型名称。
            base_url: 自定义 API 基础 URL（可选）。
            default_max_tokens: 默认最大 token 数，默认 2048。
        """
        kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = Anthropic(**kwargs)
        self._model = model
        self._default_max_tokens = default_max_tokens
        logger.info(
            f"Initialized {self.__class__.__name__} "
            f"with model: {model}"
            + (f", base_url: {base_url}" if base_url else "")
        )

    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称。"""
        return self._model

    def supports_function_calling(self) -> bool:
        """Anthropic 兼容模型均支持工具调用。"""
        return True

    # ================================================================
    # 消息格式转换
    # ================================================================

    def _extract_system(
        self, messages: List[LLMMessage]
    ) -> Tuple[Optional[str], List[LLMMessage]]:
        """提取 system 消息，返回 (system_text, non_system_messages)。

        Anthropic API 要求 system 消息单独传递，不能放在 messages 数组中。
        """
        system_parts: List[str] = []
        non_system: List[LLMMessage] = []
        for msg in messages:
            if msg.role == "system":
                system_parts.append(msg.content)
            else:
                non_system.append(msg)
        system_text = "\n".join(system_parts) if system_parts else None
        return system_text, non_system

    def _convert_messages(
        self, messages: List[LLMMessage]
    ) -> List[Dict[str, Any]]:
        """将 LLMMessage 列表转换为 Anthropic API 消息格式。

        转换规则：
        - assistant + provider_extras → 使用原始 content blocks
          （保留 thinking / tool_use 等块的完整性）
        - assistant 无 provider_extras → 使用纯文本 content
        - tool / function → 转为 Anthropic 的 tool_result 格式，
          打包到 user role 消息中
        - user → 直接传递

        Returns:
            Anthropic API 格式的消息列表。
        """
        api_messages: List[Dict[str, Any]] = []
        pending_tool_results: List[Dict[str, Any]] = []

        for msg in messages:
            # ---- tool / function 角色 → tool_result ----
            if msg.role in ("tool", "function"):
                tool_result: Dict[str, Any] = {
                    "type": "tool_result",
                    "tool_use_id": (
                        msg.tool_call_id or f"call_{msg.name}"
                    ),
                    "content": msg.content,
                }
                pending_tool_results.append(tool_result)
                continue

            # ---- 刷新待处理的 tool_results（作为 user 消息发送）----
            if pending_tool_results:
                api_messages.append({
                    "role": "user",
                    "content": pending_tool_results,
                })
                pending_tool_results = []

            # ---- assistant 消息 ----
            if msg.role == "assistant":
                if msg.provider_extras is not None:
                    # 使用原始 content blocks（保留 thinking / tool_use 等）
                    api_messages.append({
                        "role": "assistant",
                        "content": msg.provider_extras,
                    })
                else:
                    api_messages.append({
                        "role": "assistant",
                        "content": msg.content,
                    })
            else:
                # ---- user 及其他消息 ----
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        # 处理尾部剩余的 tool_results
        if pending_tool_results:
            api_messages.append({
                "role": "user",
                "content": pending_tool_results,
            })

        return api_messages

    def _convert_functions(
        self, functions: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Dict[str, Any]]]:
        """将函数定义列表转换为 Anthropic tools 格式。

        Anthropic 使用 input_schema 而非 OpenAI 的 parameters。
        """
        if not functions:
            return None
        tools: List[Dict[str, Any]] = []
        for func in functions:
            tool: Dict[str, Any] = {
                "name": func.get("name"),
                "description": func.get("description"),
            }
            if "parameters" in func:
                tool["input_schema"] = func["parameters"]
            elif "input_schema" in func:
                tool["input_schema"] = func["input_schema"]
            tools.append(tool)
        return tools

    # ================================================================
    # 响应解析
    # ================================================================

    def _parse_response(self, response: Any) -> LLMResponse:
        """解析 Anthropic API 响应为 LLMResponse。

        解析 content blocks：
        - text → 累积到 content
        - thinking → 累积到 metadata["thinking"]
        - tool_use → 转换为 FunctionCall（保留 id）

        原始 content blocks 存入 raw_response，供 Agent 在下一轮
        对话中通过 provider_extras 透传回来。
        """
        content_text: str = ""
        thinking_text: str = ""
        function_calls: Optional[List[FunctionCall]] = None

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "thinking":
                thinking_text += block.thinking
            elif block.type == "tool_use":
                if function_calls is None:
                    function_calls = []
                function_calls.append(FunctionCall(
                    name=block.name,
                    arguments=block.input,
                    id=block.id,
                ))

        # 构建响应
        llm_response = LLMResponse(
            content=content_text.strip(),
            function_calls=function_calls,
            finish_reason=response.stop_reason,
            raw_response=list(response.content),
        )

        # 元数据
        metadata: Dict[str, Any] = {}
        if thinking_text:
            metadata["thinking"] = thinking_text
            logger.debug(
                f"Captured thinking content: {thinking_text[:100]}..."
            )
        if hasattr(response, "usage"):
            usage = response.usage
            metadata["usage"] = {
                "input_tokens": getattr(usage, "input_tokens", 0),
                "output_tokens": getattr(usage, "output_tokens", 0),
                "cache_creation_input_tokens": getattr(
                    usage, "cache_creation_input_tokens", 0
                ),
                "cache_read_input_tokens": getattr(
                    usage, "cache_read_input_tokens", 0
                ),
            }
            logger.debug(f"Token usage: {metadata['usage']}")
        if metadata:
            llm_response.metadata = metadata

        return llm_response

    # ================================================================
    # 核心调用
    # ================================================================

    async def chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> LLMResponse:
        """发送聊天请求到 Anthropic 兼容 API。

        Args:
            messages: 消息列表，会自动处理 system 提取、tool_result 转换。
            functions: 函数定义列表，会转换为 Anthropic tools 格式。
            temperature: 温度参数，默认 0.1。
            **kwargs: 其他 API 参数（如 max_tokens）。

        Returns:
            LLMResponse 对象，包含回复、函数调用和 raw_response。

        Raises:
            Exception: API 调用失败时抛出。
        """
        try:
            # 提取 system 消息
            system_text, non_system_messages = self._extract_system(messages)

            # 转换消息和工具
            api_messages = self._convert_messages(non_system_messages)
            tools = self._convert_functions(functions)

            # 构建请求参数
            max_tokens = kwargs.pop("max_tokens", self._default_max_tokens)
            request_params: Dict[str, Any] = {
                "model": self._model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": api_messages,
                **kwargs,
            }
            if system_text:
                request_params["system"] = system_text
            if tools:
                request_params["tools"] = tools

            logger.debug(
                f"Sending request to {self.__class__.__name__} "
                f"with {len(api_messages)} messages"
            )

            # 调用 API
            response = self.client.messages.create(**request_params)

            return self._parse_response(response)

        except Exception as e:
            logger.error(f"{self.__class__.__name__} API error: {e}")
            raise

