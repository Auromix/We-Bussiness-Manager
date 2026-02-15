"""基础数据库访问层 - 提供通用的数据库操作，不包含业务逻辑"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import Optional
from db.models import Base
from config.settings import settings
from loguru import logger


class BaseRepository:
    """
    基础数据库访问层
    
    只提供通用的数据库操作，不包含业务逻辑。
    业务逻辑应该通过 BusinessLogicAdapter 实现。
    """
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        
        # 判断是否为异步数据库URL
        if self.database_url.startswith("sqlite"):
            # SQLite 使用同步引擎
            self.engine = create_engine(
                self.database_url.replace("sqlite:///", "sqlite:///"),
                echo=False,
                connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
            )
            self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
            self.is_async = False
        else:
            # PostgreSQL 等使用异步引擎
            async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            self.engine = create_async_engine(async_url, echo=False)
            self.SessionLocal = async_sessionmaker(self.engine, class_=AsyncSession)
            self.is_async = True
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def execute_raw_sql(self, sql: str, params: Optional[dict] = None):
        """执行原始 SQL（用于复杂查询）"""
        with self.get_session() as session:
            result = session.execute(sql, params or {})
            session.commit()
            return result

