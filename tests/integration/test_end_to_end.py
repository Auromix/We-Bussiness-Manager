"""端到端集成测试"""
import pytest
from datetime import datetime, date
from parsing.preprocessor import MessagePreProcessor
from parsing.pipeline import MessagePipeline
from db.repository import DatabaseRepository
from business.therapy_store_adapter import TherapyStoreAdapter


class MockLLMParser:
    """Mock LLM 解析器用于集成测试"""
    def __init__(self):
        self.return_value = []
    
    async def parse_message(self, sender, timestamp, content):
        return self.return_value


class TestEndToEnd:
    """端到端集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_service_message(self, temp_db):
        """测试服务消息的完整处理流程"""
        # 1. 初始化组件
        preprocessor = MessagePreProcessor()
        llm_parser = MockLLMParser()
        business_adapter = TherapyStoreAdapter(temp_db)
        pipeline = MessagePipeline(preprocessor, llm_parser, temp_db, business_adapter)
        
        # 2. 设置 LLM 返回结果
        llm_parser.return_value = [{
            "type": "service",
            "date": "2024-01-28",
            "customer_name": "段老师",
            "service_or_product": "头疗",
            "amount": 30,
            "commission": None,
            "commission_to": None,
            "net_amount": 30,
            "notes": "",
            "confidence": 0.95
        }]
        
        # 3. 构造测试消息
        raw_msg = {
            'wechat_msg_id': 'integration_test_001',
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
        
        # 4. 处理消息
        result = await pipeline.process(raw_msg)
        
        # 5. 验证处理结果
        assert result.status == 'parsed'
        assert len(result.records) == 1
        assert result.records[0]['type'] == 'service'
        assert result.records[0]['confidence'] == 0.95
        
        # 6. 验证数据库
        records = temp_db.get_records_by_date(date(2024, 1, 28))
        assert len(records) == 1
        assert records[0]['customer_name'] == '段老师'
        assert records[0]['service_type'] == '头疗'
        assert records[0]['amount'] == 30.0
    
    @pytest.mark.asyncio
    async def test_end_to_end_noise_message(self, temp_db):
        """测试噪声消息的完整处理流程"""
        preprocessor = MessagePreProcessor()
        llm_parser = MockLLMParser()
        business_adapter = TherapyStoreAdapter(temp_db)
        pipeline = MessagePipeline(preprocessor, llm_parser, temp_db, business_adapter)
        
        raw_msg = {
            'wechat_msg_id': 'integration_test_002',
            'sender_nickname': '测试用户',
            'content': '接',
            'timestamp': datetime(2024, 1, 28, 10, 1, 0),
            'is_at_bot': False
        }
        
        result = await pipeline.process(raw_msg)
        
        # 噪声消息应该被忽略
        assert result.status == 'ignored'
        assert len(result.records) == 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_multiple_records(self, temp_db):
        """测试多条记录的完整处理流程"""
        preprocessor = MessagePreProcessor()
        llm_parser = MockLLMParser()
        business_adapter = TherapyStoreAdapter(temp_db)
        pipeline = MessagePipeline(preprocessor, llm_parser, temp_db, business_adapter)
        
        # 设置返回多条记录
        llm_parser.return_value = [
            {
                "type": "service",
                "date": "2024-02-03",
                "customer_name": "段老师",
                "service_or_product": "理疗",
                "amount": 490,
                "confidence": 0.9
            },
            {
                "type": "service",
                "date": "2024-02-03",
                "customer_name": "姚老师",
                "service_or_product": "理疗",
                "amount": 490,
                "confidence": 0.9
            }
        ]
        
        raw_msg = {
            'wechat_msg_id': 'integration_test_003',
            'sender_nickname': '测试用户',
            'content': '2.3段老师490\n姚老师490理疗合计980',
            'timestamp': datetime(2024, 2, 3, 10, 0, 0),
            'is_at_bot': False
        }
        
        result = await pipeline.process(raw_msg)
        
        # 应该处理两条记录
        assert result.status == 'parsed'
        assert len(result.records) == 2
        
        # 验证数据库
        records = temp_db.get_records_by_date(date(2024, 2, 3))
        assert len(records) == 2
        assert any(r['customer_name'] == '段老师' for r in records)
        assert any(r['customer_name'] == '姚老师' for r in records)

