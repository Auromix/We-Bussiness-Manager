"""OpenAI 提供商实现。

本模块实现了 OpenAI GPT 系列模型的提供商，支持通过 OpenAI API
或兼容 OpenAI API 格式的服务调用 GPT 模型。
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall


class OpenAIProvider(LLMProvider):
    """OpenAI GPT 模型提供商。

    此提供商支持所有 OpenAI GPT 系列模型，包括 GPT-4、GPT-3.5 等。
    同时支持通过自定义 base_url 使用兼容 OpenAI API 格式的第三方服务。

    Attributes:
        client: OpenAI 客户端实例，用于发送 API 请求。
        _model: 当前使用的模型名称。

    Example:
        ```python
        # 使用 OpenAI 官方 API
        provider = OpenAIProvider(
            api_key="sk-...",
            model="gpt-4o-mini"
        )

        # 使用兼容 OpenAI API 格式的第三方服务
        provider = OpenAIProvider(
            api_key="sk-...",
            model="custom-model",
            base_url="https://api.example.com/v1"
        )
        ```
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None
    ) -> None:
        """初始化 OpenAI 提供商。

        Args:
            api_key: OpenAI API Key，用于身份验证。可以从 OpenAI 官网获取。
            model: 要使用的模型名称。支持的模型包括：
                - "gpt-4o-mini": GPT-4o 的轻量版本（推荐）
                - "gpt-4o": GPT-4o 完整版本
                - "gpt-4-turbo": GPT-4 Turbo
                - "gpt-3.5-turbo": GPT-3.5 Turbo
                默认值为 "gpt-4o-mini"。
            base_url: 可选的 API 基础 URL。如果提供，将使用此 URL 而不是
                OpenAI 官方 API。用于兼容 OpenAI API 格式的第三方服务。
                例如："https://api.example.com/v1"。

        Raises:
            ValueError: 如果 api_key 为空或无效。
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
    
    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称。

        Returns:
            模型名称字符串，如 "gpt-4o-mini"。
        """
        return self._model
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用。

        OpenAI 的 GPT 模型都支持函数调用功能（通过 tools 参数）。

        Returns:
            True，因为 OpenAI 模型支持函数调用。
        """
        return True
    
    async def chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        **kwargs: Any
    ) -> LLMResponse:
        """发送聊天请求到 OpenAI API。

        此方法将消息列表和可选的函数定义发送给 OpenAI API，并解析返回的
        回复。如果 LLM 决定调用函数，会解析 tool_calls 并返回 FunctionCall
        对象列表。

        Args:
            messages: 消息列表，会被转换为 OpenAI API 格式。
            functions: 可选的函数定义列表。如果提供，会被转换为 OpenAI
                的 tools 格式。
            temperature: 温度参数，控制回复的随机性。默认值为 0.1。
            **kwargs: 其他 OpenAI API 参数，如 max_tokens、top_p 等。

        Returns:
            LLMResponse 对象，包含回复内容和可能的函数调用。

        Raises:
            Exception: 如果 OpenAI API 调用失败。可能是网络错误、API 密钥
                无效、模型不存在等原因。

        Note:
            - OpenAI API 使用 "tools" 参数而不是 "functions" 参数。
            - tool_calls 中的 arguments 是 JSON 字符串，需要解析。
            - 如果 message.content 为 None，表示 LLM 只调用了函数。
        """
        try:
            # 转换消息格式为 OpenAI API 格式
            openai_messages: List[Dict[str, Any]] = []
            for msg in messages:
                message_dict: Dict[str, Any] = {
                    "role": msg.role,
                    "content": msg.content
                }
                # 如果消息有函数名（function 类型消息），添加到字典中
                if msg.name:
                    message_dict["name"] = msg.name
                openai_messages.append(message_dict)
            
            # 准备请求参数
            request_params: Dict[str, Any] = {
                "model": self._model,
                "messages": openai_messages,
                "temperature": temperature,
                **kwargs
            }
            
            # 如果提供了函数定义，转换为 OpenAI 的 tools 格式
            if functions:
                # OpenAI 使用 tools 参数，格式为 [{"type": "function", "function": {...}}]
                request_params["tools"] = [
                    {"type": "function", "function": func} for func in functions
                ]
                # tool_choice 设置为 "auto"，让模型决定是否调用函数
                request_params["tool_choice"] = "auto"
            
            # 发送请求到 OpenAI API
            response = self.client.chat.completions.create(**request_params)
            
            # 解析响应
            choice = response.choices[0]
            message = choice.message
            
            # 提取函数调用（如果有）
            function_calls: Optional[List[FunctionCall]] = None
            if message.tool_calls:
                function_calls = []
                for tool_call in message.tool_calls:
                    if tool_call.type == "function":
                        import json
                        try:
                            # OpenAI 返回的 arguments 是 JSON 字符串，需要解析
                            arguments: Dict[str, Any] = json.loads(
                                tool_call.function.arguments
                            )
                            function_calls.append(FunctionCall(
                                name=tool_call.function.name,
                                arguments=arguments
                            ))
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Failed to parse function arguments: {e}, "
                                f"raw: {tool_call.function.arguments}"
                            )
            
            return LLMResponse(
                content=message.content or "",
                function_calls=function_calls,
                finish_reason=choice.finish_reason
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

