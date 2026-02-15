"""初始化数据库"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.repository import DatabaseRepository
from db.models import Base
from config.known_entities import SERVICE_TYPES
from loguru import logger


def init_database():
    """初始化数据库和种子数据"""
    logger.info("Initializing database...")
    
    # 创建数据库仓库
    db_repo = DatabaseRepository()
    
    # 创建所有表
    logger.info("Creating tables...")
    db_repo.create_tables()
    
    # 插入种子数据
    logger.info("Inserting seed data...")
    
    # 插入服务类型
    for service_type in SERVICE_TYPES:
        db_repo.get_or_create_service_type(
            name=service_type['name'],
            default_price=service_type.get('default_price'),
            category=service_type.get('category')
        )
        logger.info(f"Created service type: {service_type['name']}")
    
    logger.info("Database initialization completed!")


if __name__ == "__main__":
    init_database()

