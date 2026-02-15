"""LLM 解析引擎 - 使用新的 Agent 架构"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from loguru import logger
from config.settings import settings
from config.prompts import get_system_prompt

# 导入新的 Agent 架构
from agent import Agent, create_provider
from agent.functions.registry import FunctionRegistry
from agent.functions.discovery import register_instance_methods, auto_discover_and_register


class LLMParser(ABC):
    """LLM 解析器抽象基类（向后兼容接口）"""
    
    @abstractmethod
    async def parse_message(self, sender: str, timestamp: str, content: str) -> List[Dict[str, Any]]:
        """解析消息，返回结构化数据列表"""
        pass


class AgentBasedParser(LLMParser):
    """基于 Agent 架构的解析器（统一实现）"""
    
    def __init__(self, agent: Agent):
        """初始化基于 Agent 的解析器
        
        Args:
            agent: Agent 实例
        """
        self.agent = agent
    
    async def parse_message(self, sender: str, timestamp: str, content: str) -> List[Dict[str, Any]]:
        """使用 Agent 解析消息"""
        return await self.agent.parse_message(sender, timestamp, content)


# 向后兼容的别名
class OpenAIParser(AgentBasedParser):
    """OpenAI GPT 解析器（向后兼容）"""
    pass


class ClaudeParser(AgentBasedParser):
    """Anthropic Claude 解析器（向后兼容）"""
    pass


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


def create_llm_parser(
    system_prompt: Optional[str] = None,
    db_repo=None,
    enable_function_calling: bool = False,
    custom_function_targets: Optional[List[Any]] = None
) -> LLMParserWithFallback:
    """
    创建 LLM 解析器实例（使用新的 Agent 架构）
    
    Args:
        system_prompt: 系统提示词，如果为 None 则从 business_config 获取
        db_repo: 数据库仓库实例（如果启用函数调用）
        enable_function_calling: 是否启用函数调用功能
        custom_function_targets: 自定义函数目标列表，用于注册其他对象的方法
            可以是: [obj1, (obj2, "prefix_"), module1, ...]
    
    Examples:
        # 只注册数据库仓库
        llm_parser = create_llm_parser(db_repo=db_repo, enable_function_calling=True)
        
        # 注册数据库仓库和其他服务
        llm_parser = create_llm_parser(
            db_repo=db_repo,
            enable_function_calling=True,
            custom_function_targets=[
                (membership_svc, "membership_"),
                (inventory_svc, "inventory_"),
            ]
        )
    """
    # 如果没有提供，从业务配置获取
    if system_prompt is None:
        system_prompt = get_system_prompt()
    
    primary = None
    fallback = None
    
    # 创建函数注册表（如果启用函数调用）
    function_registry = None
    if enable_function_calling:
        function_registry = FunctionRegistry()
        
        # 注册数据库仓库（使用 db_ 前缀）
        if db_repo:
            register_instance_methods(
                function_registry,
                db_repo,
                class_name="DatabaseRepository",
                prefix="db_"
            )
            logger.info("Function calling enabled with database repository")
        
        # 注册自定义目标
        if custom_function_targets:
            auto_discover_and_register(function_registry, custom_function_targets)
            logger.info(f"Registered {len(custom_function_targets)} custom function targets")
    
    # 创建主解析器
    if settings.primary_llm == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when PRIMARY_LLM=openai")
        provider = create_provider(
            "openai",
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
        agent = Agent(provider, function_registry, system_prompt)
        primary = AgentBasedParser(agent)
    elif settings.primary_llm == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when PRIMARY_LLM=anthropic")
        provider = create_provider(
            "claude",
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model
        )
        agent = Agent(provider, function_registry, system_prompt)
        primary = AgentBasedParser(agent)
    else:
        raise ValueError(f"Unknown PRIMARY_LLM: {settings.primary_llm}")
    
    # 创建备用解析器
    if settings.fallback_llm and settings.fallback_llm != settings.primary_llm:
        if settings.fallback_llm == "openai":
            if not settings.openai_api_key:
                logger.warning("Fallback LLM set to openai but OPENAI_API_KEY not set, skipping fallback")
            else:
                provider = create_provider(
                    "openai",
                    api_key=settings.openai_api_key,
                    model=settings.openai_model
                )
                agent = Agent(provider, function_registry, system_prompt)
                fallback = AgentBasedParser(agent)
        elif settings.fallback_llm == "anthropic":
            if not settings.anthropic_api_key:
                logger.warning("Fallback LLM set to anthropic but ANTHROPIC_API_KEY not set, skipping fallback")
            else:
                provider = create_provider(
                    "claude",
                    api_key=settings.anthropic_api_key,
                    model=settings.anthropic_model
                )
                agent = Agent(provider, function_registry, system_prompt)
                fallback = AgentBasedParser(agent)
    
    if primary is None:
        raise ValueError("Failed to create primary LLM parser")
    
    return LLMParserWithFallback(primary=primary, fallback=fallback)

