"""全局配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # LLM API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///data/store.db"
    
    # Redis
    redis_url: Optional[str] = "redis://localhost:6379/0"
    
    # Bot Configuration
    bot_name: str = "小助手"
    target_group_name: str = "门店经营群"
    primary_llm: str = "openai"  # openai / anthropic
    fallback_llm: Optional[str] = "anthropic"
    
    # LLM Model Settings
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-sonnet-4-20250514"
    
    # Processing Settings
    confidence_threshold: float = 0.7
    daily_summary_time: str = "21:00"
    
    # WeChat Configuration
    wechat_group_ids: Optional[str] = None  # 逗号分隔的群ID列表
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()

