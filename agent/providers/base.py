"""LLM 提供商基础接口。

本模块定义了 LLM 提供商的抽象基类和相关的数据类，所有具体的
LLM 提供商实现都必须继承 LLMProvider 并实现其抽象方法。

数据流：
    用户消息 → Agent → LLMProvider.chat() → LLMResponse
    LLMResponse.function_calls → Agent 执行 → tool 消息 → 下一轮 chat()

关键设计：
    - FunctionCall.id: 每次工具调用都有唯一 ID，用于关联调用和结果
    - LLMMessage.tool_calls: assistant 消息中记录触发了哪些工具调用
    - LLMMessage.tool_call_id: tool 消息中引用对应的调用 ID
    - LLMMessage.provider_extras: 保存提供商原始数据，多轮对话时透传
    - LLMResponse.raw_response: 提供商原始响应，存入下一轮的 provider_extras
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class FunctionCall:
    """函数调用对象，表示 LLM 决定调用的一个函数。

    Attributes:
        name: 要调用的函数名称，必须与 FunctionRegistry 中注册的
            函数名称一致。
        arguments: 函数调用的参数字典，键为参数名，值为参数值。
        id: 调用标识符，用于在多轮对话中关联工具调用与结果。
            OpenAI 中对应 tool_call_id，Anthropic 中对应 tool_use_id。
            如果为 None，Agent 会使用函数名生成 fallback ID。

    Example:
        ```python
        func_call = FunctionCall(
            name="get_customer",
            arguments={"name": "张三"},
            id="call_abc123"
        )
        ```
    """
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class LLMMessage:
    """LLM 消息对象，表示对话中的一条消息。

    统一的消息格式，各提供商在 chat() 方法中将此格式转换为
    各自 API 所需的格式。

    Attributes:
        role: 消息角色，必须是以下值之一：
            - "system": 系统消息，设置 AI 行为
            - "user": 用户消息
            - "assistant": AI 助手回复
            - "tool": 工具/函数调用的结果（也兼容旧的 "function"）
        content: 消息的文本内容。
        name: 函数名称（tool 消息时标识对应的函数）。
        tool_calls: 工具调用列表（assistant 消息触发工具调用时使用）。
            存储 LLM 决定调用的所有函数及其参数。
        tool_call_id: 工具调用标识符（tool 消息时引用对应的调用 ID），
            用于将工具执行结果与特定的工具调用关联。
        provider_extras: 提供商特定的附加数据，用于在多轮对话中保持
            提供商所需的完整上下文。例如 Anthropic 的 content blocks
            （包含 thinking、tool_use 等块）。Agent 在存储 assistant
            消息时，会将 LLMResponse.raw_response 赋值到此字段。

    Example:
        ```python
        # 系统消息
        system_msg = LLMMessage(role="system", content="你是一个助手")

        # 用户消息
        user_msg = LLMMessage(role="user", content="查询顾客信息")

        # 带工具调用的 assistant 消息
        assistant_msg = LLMMessage(
            role="assistant",
            content="",
            tool_calls=[FunctionCall(name="get_customer", arguments={"name": "张三"}, id="call_123")]
        )

        # 工具结果消息
        tool_msg = LLMMessage(
            role="tool",
            content='{"name": "张三", "balance": 500}',
            name="get_customer",
            tool_call_id="call_123"
        )
        ```
    """
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[FunctionCall]] = None
    tool_call_id: Optional[str] = None
    provider_extras: Optional[Any] = field(default=None, repr=False)


@dataclass
class LLMResponse:
    """LLM 响应对象，包含 LLM 的回复和可能的函数调用。

    Attributes:
        content: LLM 生成的文本回复内容。如果 LLM 决定调用函数，
            此字段可能为空字符串。
        function_calls: 函数调用列表（如果 LLM 决定调用函数）。
            每个 FunctionCall 包含函数名、参数和唯一 ID。
        finish_reason: 完成原因，如 "stop"、"tool_calls" 等。
        metadata: 元数据字典，用于存储额外信息。
            例如：thinking 内容、token 使用统计等。
        raw_response: 提供商原始响应数据。Agent 会将此值存入
            下一轮 assistant 消息的 provider_extras 字段，
            以便提供商在后续请求中恢复完整的上下文。

    Example:
        ```python
        # 普通回复
        response = LLMResponse(content="你好", finish_reason="stop")

        # 包含函数调用的回复
        response = LLMResponse(
            content="",
            function_calls=[
                FunctionCall(name="query_income", arguments={"date": "2024-01-28"}, id="call_456")
            ],
            finish_reason="tool_calls"
        )

        # 包含 thinking 的回复（MiniMax）
        response = LLMResponse(
            content="今天收入共计500元",
            metadata={"thinking": "用户在问收入，我来查一下..."}
        )
        ```
    """
    content: str
    function_calls: Optional[List[FunctionCall]] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    raw_response: Optional[Any] = field(default=None, repr=False)


class LLMProvider(ABC):
    """LLM 提供商抽象基类。

    所有 LLM 提供商（OpenAI、Claude、MiniMax 等）都必须继承此类并实现
    其抽象方法。此接口定义了统一的 LLM 调用规范，使得不同的提供商可以
    无缝切换，对上层 Agent 完全透明。

    扩展新提供商只需：
        1. 继承 LLMProvider
        2. 实现 chat()、supports_function_calling()、model_name
        3. 在 providers/__init__.py 的 create_provider() 中注册

    子类职责：
        - 将 LLMMessage 列表转换为自身 API 所需的格式
        - 将 API 响应转换为统一的 LLMResponse
        - 正确处理 tool_calls 和 tool_call_id 的映射
        - 将原始响应数据存入 LLMResponse.raw_response（如有需要）

    Example:
        ```python
        class MyProvider(LLMProvider):
            @property
            def model_name(self) -> str:
                return "my-model"

            def supports_function_calling(self) -> bool:
                return True

            async def chat(self, messages, functions=None, **kwargs):
                # 1. 转换消息格式
                # 2. 调用 API
                # 3. 解析响应为 LLMResponse
                ...
        ```
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        **kwargs: Any
    ) -> LLMResponse:
        """发送聊天请求到 LLM 并获取回复。

        Args:
            messages: 消息列表，按时间顺序排列。包含 system、user、
                assistant 和 tool 类型的消息。
            functions: 可选的函数定义列表，格式为：
                [{"name": "...", "description": "...", "parameters": {...}}]
            temperature: 温度参数，控制回复的随机性。默认 0.1。
            **kwargs: 提供商特定的参数，如 max_tokens、top_p 等。

        Returns:
            LLMResponse 对象，包含回复内容和可能的函数调用。
            如果包含函数调用，每个 FunctionCall 应有唯一的 id。

        Raises:
            Exception: API 调用失败时抛出异常。
        """
        pass

    @abstractmethod
    def supports_function_calling(self) -> bool:
        """检查此提供商是否支持函数调用功能。

        Returns:
            True 如果支持函数调用，False 否则。
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回当前使用的模型名称。

        Returns:
            模型名称字符串，如 "gpt-4o-mini"、"claude-sonnet-4-20250514"。
        """
        pass
