"""Pytest 配置和共享 fixtures"""
import pytest
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock
from database import DatabaseManager
from database.models import Base

try:
    from core.business_adapter import BusinessLogicAdapter
    from business.therapy_store_adapter import TherapyStoreAdapter
    _HAS_BUSINESS = True
except (ImportError, ModuleNotFoundError):
    _HAS_BUSINESS = False


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    db_url = f"sqlite:///{db_path}"
    
    # 创建数据库
    repo = DatabaseManager(database_url=db_url)
    repo.create_tables()
    
    yield repo
    
    # 清理
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_business_adapter(temp_db):
    """创建 Mock 业务逻辑适配器"""
    if not _HAS_BUSINESS:
        pytest.skip("business module not available")
    # 使用真实的 TherapyStoreAdapter 进行测试
    return TherapyStoreAdapter(temp_db)


@pytest.fixture
def sample_message():
    """示例消息数据"""
    return {
        'wechat_msg_id': 'test_msg_001',
        'sender_nickname': '测试用户',
        'sender_wechat_id': 'test_user_001',
        'content': '1.28段老师头疗30',
        'msg_type': 'text',
        'group_id': 'test_group_001',
        'timestamp': datetime(2024, 1, 28, 10, 0, 0),
        'is_at_bot': False,
        'is_business': None,
        'parse_status': 'pending'
    }


@pytest.fixture
def sample_datetime():
    """示例日期时间"""
    return datetime(2024, 1, 28, 10, 0, 0)
