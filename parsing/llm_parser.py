"""LLM 解析引擎（OpenAI + Claude）"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from openai import OpenAI
from anthropic import Anthropic
import json
import re
from loguru import logger
from config.settings import settings
from config.prompts import get_system_prompt, get_user_prompt, SYSTEM_PROMPT


class LLMParser(ABC):
    """LLM 解析器抽象基类"""
    
    @abstractmethod
    async def parse_message(self, sender: str, timestamp: str, content: str) -> List[Dict[str, Any]]:
        """解析消息，返回结构化数据列表"""
        pass


class OpenAIParser(LLMParser):
    """OpenAI GPT 解析器"""
    
    def __init__(self, api_key: str, model: str = None, system_prompt: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)
        self.model = model or settings.openai_model
        self.system_prompt = system_prompt or get_system_prompt()
    
    async def parse_message(self, sender: str, timestamp: str, content: str) -> List[Dict[str, Any]]:
        """使用 OpenAI API 解析消息"""
        try:
            user_prompt = get_user_prompt(sender, timestamp, content)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # 低温度保证一致性
            )
            
            result_text = response.choices[0].message.content
            return self._parse_json_response(result_text)
            
        except Exception as e:
            logger.error(f"OpenAI parsing error: {e}")
            raise
    
    def _parse_json_response(self, text: str) -> List[Dict[str, Any]]:
        """解析 LLM 返回的 JSON"""
        # 清理可能的 markdown code block
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        
        try:
            data = json.loads(text)
            # 如果返回的是单个对象，转换为列表
            if isinstance(data, dict):
                # 检查是否有 records 字段
                if "records" in data:
                    return data["records"]
                # 否则包装为列表
                return [data]
            elif isinstance(data, list):
                return data
            else:
                logger.warning(f"Unexpected response format: {type(data)}")
                return [{"type": "noise"}]
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, text: {text[:200]}")
            return [{"type": "noise", "error": str(e)}]


class ClaudeParser(LLMParser):
    """Anthropic Claude 解析器"""
    
    def __init__(self, api_key: str, model: str = None, system_prompt: Optional[str] = None):
        self.client = Anthropic(api_key=api_key)
        self.model = model or settings.anthropic_model
        self.system_prompt = system_prompt or get_system_prompt()
    
    async def parse_message(self, sender: str, timestamp: str, content: str) -> List[Dict[str, Any]]:
        """使用 Claude API 解析消息"""
        try:
            user_prompt = get_user_prompt(sender, timestamp, content)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
            )
            
            # Claude 返回的文本可能包含 markdown code block
            text = response.content[0].text
            return self._parse_json_response(text)
            
        except Exception as e:
            logger.error(f"Claude parsing error: {e}")
            raise
    
    def _parse_json_response(self, text: str) -> List[Dict[str, Any]]:
        """解析 Claude 返回的 JSON"""
        # 清理可能的 markdown code block
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        
        try:
            data = json.loads(text)
            # 如果返回的是单个对象，转换为列表
            if isinstance(data, dict):
                if "records" in data:
                    return data["records"]
                return [data]
            elif isinstance(data, list):
                return data
            else:
                logger.warning(f"Unexpected response format: {type(data)}")
                return [{"type": "noise"}]
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, text: {text[:200]}")
            return [{"type": "noise", "error": str(e)}]


class LLMParserWithFallback:
    """带有 fallback 的解析器"""
    
    def __init__(self, primary: LLMParser, fallback: LLMParser = None):
        self.primary = primary
        self.fallback = fallback
    
    async def parse_message(self, sender: str, timestamp: str, content: str) -> List[Dict[str, Any]]:
        """使用主解析器，失败时使用备用解析器"""
        try:
            return await self.primary.parse_message(sender, timestamp, content)
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}, falling back")
            if self.fallback:
                try:
                    return await self.fallback.parse_message(sender, timestamp, content)
                except Exception as e2:
                    logger.error(f"Fallback LLM also failed: {e2}")
                    raise
            else:
                raise


def create_llm_parser(system_prompt: Optional[str] = None) -> LLMParserWithFallback:
    """
    创建 LLM 解析器实例
    
    Args:
        system_prompt: 系统提示词，如果为 None 则从 business_config 获取
    """
    # 如果没有提供，从业务配置获取
    if system_prompt is None:
        system_prompt = get_system_prompt()
    
    primary = None
    fallback = None
    
    if settings.primary_llm == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when PRIMARY_LLM=openai")
        primary = OpenAIParser(api_key=settings.openai_api_key, model=settings.openai_model, system_prompt=system_prompt)
    elif settings.primary_llm == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when PRIMARY_LLM=anthropic")
        primary = ClaudeParser(api_key=settings.anthropic_api_key, model=settings.anthropic_model, system_prompt=system_prompt)
    else:
        raise ValueError(f"Unknown PRIMARY_LLM: {settings.primary_llm}")
    
    if settings.fallback_llm and settings.fallback_llm != settings.primary_llm:
        if settings.fallback_llm == "openai":
            if not settings.openai_api_key:
                logger.warning("Fallback LLM set to openai but OPENAI_API_KEY not set, skipping fallback")
            else:
                fallback = OpenAIParser(api_key=settings.openai_api_key, model=settings.openai_model, system_prompt=system_prompt)
        elif settings.fallback_llm == "anthropic":
            if not settings.anthropic_api_key:
                logger.warning("Fallback LLM set to anthropic but ANTHROPIC_API_KEY not set, skipping fallback")
            else:
                fallback = ClaudeParser(api_key=settings.anthropic_api_key, model=settings.anthropic_model, system_prompt=system_prompt)
    
    if primary is None:
        raise ValueError("Failed to create primary LLM parser")
    
    return LLMParserWithFallback(primary=primary, fallback=fallback)

