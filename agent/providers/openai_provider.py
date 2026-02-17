"""OpenAI 提供商实现。

本模块实现了 OpenAI GPT 系列模型的提供商，支持通过 OpenAI API
或兼容 OpenAI API 格式的服务调用 GPT 模型。

支持的模型：
    - gpt-4o-mini（推荐，性价比高）
    - gpt-4o
    - gpt-4-turbo
    - gpt-3.5-turbo
    - 以及兼容 OpenAI API 格式的第三方模型
"""
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall


class OpenAIProvider(LLMProvider):
    """OpenAI GPT 模型提供商。

    支持所有 OpenAI GPT 系列模型，同时支持通过自定义 base_url
    使用兼容 OpenAI API 格式的第三方服务。

    消息转换说明：
    - assistant 消息如果包含 tool_calls，会重建为 OpenAI 的
      tool_calls 格式（包含 id、type、function）
    - tool 消息会使用 tool_call_id 关联对应的工具调用
    - 兼容旧的 function role（自动转为 tool role）

    Attributes:
        client: OpenAI 客户端实例。
        _model: 当前使用的模型名称。

    Example:
        ```python
        # 使用 OpenAI 官方 API
        provider = OpenAIProvider(
            api_key="sk-...",
            model="gpt-4o-mini"
        )

        # 使用兼容 API 服务
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
        base_url: Optional[str] = None,
    ) -> None:
        """初始化 OpenAI 提供商。

        Args:
            api_key: OpenAI API Key。
            model: 模型名称，默认 "gpt-4o-mini"。
            base_url: 自定义 API 基础 URL（可选）。
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称。"""
        return self._model

    def supports_function_calling(self) -> bool:
        """OpenAI GPT 模型均支持函数调用。"""
        return True

    def _convert_messages(
        self, messages: List[LLMMessage]
    ) -> List[Dict[str, Any]]:
        """将 LLMMessage 列表转换为 OpenAI API 消息格式。

        转换规则：
        - assistant + tool_calls → 重建 OpenAI tool_calls 结构
        - tool / function → 使用 role="tool" + tool_call_id
        - 其他 → 直接传递 role + content
        """
        openai_messages: List[Dict[str, Any]] = []

        for msg in messages:
            message_dict: Dict[str, Any] = {
                "role": msg.role,
                "content": msg.content,
            }

            # assistant 消息带有 tool_calls → 重建完整的 tool_calls 结构
            if msg.role == "assistant" and msg.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tc.id or f"call_{tc.name}",
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(
                                tc.arguments, ensure_ascii=False
                            ),
                        },
                    }
                    for tc in msg.tool_calls
                ]
                # OpenAI: content 可以为 null（当只有 tool_calls 时）
                if not msg.content:
                    message_dict["content"] = None

            # tool / function 消息 → 统一为 tool role + tool_call_id
            if msg.role in ("tool", "function"):
                message_dict["role"] = "tool"
                message_dict["tool_call_id"] = (
                    msg.tool_call_id or f"call_{msg.name}"
                )

            # 普通消息的 name 字段
            if msg.name and msg.role not in ("tool", "function"):
                message_dict["name"] = msg.name

            openai_messages.append(message_dict)

        return openai_messages

    async def chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> LLMResponse:
        """发送聊天请求到 OpenAI API。

        Args:
            messages: 消息列表，会被转换为 OpenAI API 格式。
            functions: 函数定义列表，会转换为 OpenAI tools 格式。
            temperature: 温度参数，默认 0.1。
            **kwargs: 其他 OpenAI API 参数（如 max_tokens、top_p）。

        Returns:
            LLMResponse 对象，包含回复和可能的函数调用（带 id）。

        Raises:
            Exception: OpenAI API 调用失败时抛出。
        """
        try:
            # 转换消息格式
            openai_messages = self._convert_messages(messages)

            # 构建请求参数
            request_params: Dict[str, Any] = {
                "model": self._model,
                "messages": openai_messages,
                "temperature": temperature,
                **kwargs,
            }

            # 转换函数定义为 OpenAI tools 格式
            if functions:
                request_params["tools"] = [
                    {"type": "function", "function": func}
                    for func in functions
                ]
                request_params["tool_choice"] = "auto"

            # 发送请求
            response = self.client.chat.completions.create(**request_params)

            # 解析响应
            choice = response.choices[0]
            message = choice.message

            # 提取函数调用（保留 tool_call_id）
            function_calls: Optional[List[FunctionCall]] = None
            if message.tool_calls:
                function_calls = []
                for tool_call in message.tool_calls:
                    if tool_call.type == "function":
                        try:
                            arguments: Dict[str, Any] = json.loads(
                                tool_call.function.arguments
                            )
                            function_calls.append(FunctionCall(
                                name=tool_call.function.name,
                                arguments=arguments,
                                id=tool_call.id,
                            ))
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Failed to parse function arguments: {e}, "
                                f"raw: {tool_call.function.arguments}"
                            )

            return LLMResponse(
                content=message.content or "",
                function_calls=function_calls,
                finish_reason=choice.finish_reason,
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
