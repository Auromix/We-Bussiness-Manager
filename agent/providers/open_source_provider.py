"""开源模型提供商实现 - 支持兼容 OpenAI API 格式的开源模型。

本模块实现了开源模型的提供商，支持通过 HTTP API 调用兼容 OpenAI API
格式的模型服务。可以用于接入通过 vLLM、Ollama、LocalAI 等部署的模型。

支持的部署方式：
    - vLLM: 高性能 LLM 推理服务
    - Ollama: 本地模型运行工具
    - LocalAI: OpenAI 兼容的本地 API 服务
    - 其他兼容 OpenAI API 格式的服务

支持的模型（取决于部署服务）：
    - Qwen（通义千问）
    - ChatGLM
    - Llama 系列
    - Mistral
    - DeepSeek
"""
import json
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall


class OpenSourceProvider(LLMProvider):
    """开源模型提供商 - 支持兼容 OpenAI API 格式的模型。

    通过 HTTP API 接入的开源模型，只要模型服务兼容 OpenAI API
    格式即可。消息转换逻辑与 OpenAIProvider 一致。

    Attributes:
        base_url: API 基础 URL。
        _model: 当前使用的模型名称。
        api_key: 可选的 API Key。
        timeout: HTTP 请求超时时间（秒）。

    Example:
        ```python
        # 使用本地部署的 vLLM 服务
        provider = OpenSourceProvider(
            base_url="http://localhost:8000/v1",
            model="qwen",
            timeout=120.0
        )

        # 使用需要认证的服务
        provider = OpenSourceProvider(
            base_url="https://api.example.com/v1",
            model="custom-model",
            api_key="sk-..."
        )
        ```
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        """初始化开源模型提供商。

        Args:
            base_url: API 基础 URL（如 "http://localhost:8000/v1"）。
            model: 模型名称。
            api_key: 可选的 API Key。
            timeout: HTTP 请求超时时间（秒），默认 60.0。
        """
        self.base_url = base_url.rstrip("/")
        self._model = model
        self.api_key = api_key
        self.timeout = timeout

    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称。"""
        return self._model

    def supports_function_calling(self) -> bool:
        """大多数 OpenAI 兼容服务支持函数调用。"""
        return True

    def _convert_messages(
        self, messages: List[LLMMessage]
    ) -> List[Dict[str, Any]]:
        """将 LLMMessage 列表转换为 OpenAI 兼容 API 消息格式。

        转换逻辑与 OpenAIProvider 一致。
        """
        api_messages: List[Dict[str, Any]] = []

        for msg in messages:
            message_dict: Dict[str, Any] = {
                "role": msg.role,
                "content": msg.content,
            }

            # assistant 消息带有 tool_calls
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
                if not msg.content:
                    message_dict["content"] = None

            # tool / function 消息
            if msg.role in ("tool", "function"):
                message_dict["role"] = "tool"
                message_dict["tool_call_id"] = (
                    msg.tool_call_id or f"call_{msg.name}"
                )

            if msg.name and msg.role not in ("tool", "function"):
                message_dict["name"] = msg.name

            api_messages.append(message_dict)

        return api_messages

    async def chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> LLMResponse:
        """发送聊天请求到开源模型 API。

        通过 HTTP POST 请求调用兼容 OpenAI API 格式的模型服务。

        Args:
            messages: 消息列表，会被转换为 OpenAI API 格式。
            functions: 函数定义列表，会转换为 tools 格式。
            temperature: 温度参数，默认 0.1。
            **kwargs: 其他 API 参数。

        Returns:
            LLMResponse 对象，包含回复和可能的函数调用。

        Raises:
            httpx.HTTPError: HTTP 请求失败。
            Exception: 其他错误。
        """
        try:
            # 转换消息格式
            api_messages = self._convert_messages(messages)

            # 构建请求体
            request_body: Dict[str, Any] = {
                "model": self._model,
                "messages": api_messages,
                "temperature": temperature,
                **kwargs,
            }

            # 转换函数定义为 tools 格式
            if functions:
                request_body["tools"] = [
                    {"type": "function", "function": func}
                    for func in functions
                ]
                request_body["tool_choice"] = "auto"

            # 准备请求头
            headers: Dict[str, str] = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # 发送 HTTP POST 请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=request_body,
                    headers=headers,
                )
                response.raise_for_status()
                data: Dict[str, Any] = response.json()

            # 解析响应
            choice: Dict[str, Any] = data["choices"][0]
            message: Dict[str, Any] = choice["message"]

            # 提取函数调用（保留 id）
            function_calls: Optional[List[FunctionCall]] = None
            if "tool_calls" in message and message["tool_calls"]:
                function_calls = []
                for tool_call in message["tool_calls"]:
                    if tool_call.get("type") == "function":
                        func: Dict[str, Any] = tool_call["function"]
                        try:
                            arguments: Dict[str, Any] = json.loads(
                                func.get("arguments", "{}")
                            )
                            function_calls.append(FunctionCall(
                                name=func.get("name", ""),
                                arguments=arguments,
                                id=tool_call.get("id"),
                            ))
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Failed to parse function arguments: {e}, "
                                f"raw: {func.get('arguments', '')}"
                            )

            return LLMResponse(
                content=message.get("content", "") or "",
                function_calls=function_calls,
                finish_reason=choice.get("finish_reason"),
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling open source model: {e}")
            raise
        except Exception as e:
            logger.error(f"Open source model API error: {e}")
            raise
