"""LLM 提供商基础接口。

本模块定义了 LLM 提供商的抽象基类和相关的数据类，所有具体的
LLM 提供商实现都必须继承 LLMProvider 并实现其抽象方法。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMMessage:
    """LLM 消息对象，表示对话中的一条消息。

    Attributes:
        role: 消息角色，必须是以下值之一：
            - "system": 系统消息，用于设置 AI 的行为
            - "user": 用户消息
            - "assistant": AI 助手的回复
            - "function": 函数调用的结果
        content: 消息的文本内容。
        name: 可选的函数名称。当 role 为 "function" 时，此字段
            表示对应的函数名称。

    Example:
        ```python
        system_msg = LLMMessage(role="system", content="你是一个助手")
        user_msg = LLMMessage(role="user", content="你好")
        func_msg = LLMMessage(
            role="function",
            content='{"result": "success"}',
            name="get_customer"
        )
        ```
    """
    role: str  # "system", "user", "assistant", "function"
    content: str
    name: Optional[str] = None  # 函数调用时的函数名


@dataclass
class FunctionCall:
    """函数调用对象，表示 LLM 决定调用的一个函数。

    Attributes:
        name: 要调用的函数名称，必须与 FunctionRegistry 中注册的
            函数名称一致。
        arguments: 函数调用的参数字典，键为参数名，值为参数值。
            参数值必须符合函数定义的参数 Schema。

    Example:
        ```python
        func_call = FunctionCall(
            name="get_customer",
            arguments={"name": "张三", "id": 123}
        )
        ```
    """
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """LLM 响应对象，包含 LLM 的回复和可能的函数调用。

    Attributes:
        content: LLM 生成的文本回复内容。如果 LLM 决定调用函数，
            此字段可能为空字符串。
        function_calls: 可选的函数调用列表。如果 LLM 决定调用函数，
            此字段包含 FunctionCall 对象列表；否则为 None。
        finish_reason: 可选的完成原因，表示 LLM 为什么停止生成。
            常见值包括 "stop"（正常结束）、"length"（达到最大长度）等。

    Example:
        ```python
        # 普通回复
        response = LLMResponse(
            content="你好，我是助手",
            finish_reason="stop"
        )

        # 包含函数调用的回复
        response = LLMResponse(
            content="",
            function_calls=[
                FunctionCall(name="get_customer", arguments={"name": "张三"})
            ],
            finish_reason="tool_calls"
        )
        ```
    """
    content: str
    function_calls: Optional[List[FunctionCall]] = None
    finish_reason: Optional[str] = None


class LLMProvider(ABC):
    """LLM 提供商抽象基类。

    所有 LLM 提供商（OpenAI、Claude、开源模型等）都必须继承此类并实现
    其抽象方法。此接口定义了统一的 LLM 调用规范，使得不同的提供商可以
    无缝切换使用。

    子类必须实现：
        - chat(): 发送聊天请求并获取回复
        - supports_function_calling(): 是否支持函数调用功能
        - model_name: 模型名称属性

    Example:
        ```python
        class MyProvider(LLMProvider):
            @property
            def model_name(self) -> str:
                return "my-model"

            def supports_function_calling(self) -> bool:
                return True

            async def chat(self, messages, functions=None, **kwargs):
                # 实现具体的调用逻辑
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

        此方法是所有 LLM 提供商的核心方法，负责将消息列表发送给 LLM
        并返回回复。如果提供了函数定义列表，LLM 可能会决定调用函数。

        Args:
            messages: 消息列表，按时间顺序排列。通常包含 system、user、
                assistant 和 function 类型的消息。
            functions: 可选的函数定义列表，用于 function calling 功能。
                每个函数定义应该是一个字典，包含以下键：
                - name: 函数名称
                - description: 函数描述
                - parameters: 参数 Schema（JSON Schema 格式）
            temperature: 温度参数，控制回复的随机性。范围通常在 0.0 到 2.0
                之间，值越大越随机。默认值为 0.1，适合需要确定性的场景。
            **kwargs: 其他提供商特定的参数，如 max_tokens、top_p 等。

        Returns:
            LLMResponse 对象，包含 LLM 的回复内容和可能的函数调用。

        Raises:
            Exception: 如果 API 调用失败或发生其他错误。具体的异常类型
                取决于具体的提供商实现。

        Note:
            - 不同的提供商对 functions 参数的格式要求可能不同，实现类
              需要负责格式转换。
            - 如果 LLM 决定调用函数，content 字段可能为空，函数调用信息
              在 function_calls 字段中。
        """
        pass
    
    @abstractmethod
    def supports_function_calling(self) -> bool:
        """检查此提供商是否支持函数调用功能。

        Returns:
            True 如果此提供商支持函数调用（function calling/tool use），
            False 否则。

        Note:
            - 如果返回 False，即使提供了 functions 参数，也不会进行函数调用。
            - 此方法应该是一个简单的属性检查，不应该执行任何耗时操作。
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回当前使用的模型名称。

        Returns:
            模型名称字符串，如 "gpt-4o-mini"、"claude-sonnet-4-20250514" 等。

        Note:
            - 此属性应该是只读的，返回初始化时设置的模型名称。
            - 模型名称用于日志记录和调试。
        """
        pass

