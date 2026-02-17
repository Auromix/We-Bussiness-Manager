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
    
    # WeChat Work (企业微信) Configuration
    wechat_work_corp_id: Optional[str] = None  # 企业 ID
    wechat_work_secret: Optional[str] = None  # 应用密钥
    wechat_work_agent_id: Optional[str] = None  # 应用 ID
    wechat_work_token: Optional[str] = None  # 回调 Token
    wechat_work_encoding_aes_key: Optional[str] = None  # 回调消息加密密钥
    
    # HTTP API Configuration
    wechat_http_host: str = "0.0.0.0"  # HTTP API 监听地址
    wechat_http_port: int = 8000  # HTTP API 监听端口
    wechat_callback_path: str = "/callback"  # 回调路径
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()

