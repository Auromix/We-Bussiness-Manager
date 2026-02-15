"""测试消息处理流水线"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from parsing.preprocessor import MessagePreProcessor
from parsing.pipeline import MessagePipeline, ProcessResult
from db.repository import DatabaseRepository


class MockLLMParser:
    """Mock LLM 解析器"""
    
    def __init__(self, return_value=None):
        self.return_value = return_value or []
    
    async def parse_message(self, sender: str, timestamp: str, content: str):
        return self.return_value


class TestMessagePipeline:
    """消息处理流水线测试"""
    
    @pytest.fixture
    def pipeline(self, temp_db, mock_business_adapter):
        """创建流水线实例"""
        preprocessor = MessagePreProcessor()
        # 创建默认的 mock parser，返回空列表
        llm_parser = MockLLMParser(return_value=[])
        pipeline = MessagePipeline(preprocessor, llm_parser, temp_db, mock_business_adapter)
        # 保存 llm_parser 引用以便测试中修改
        pipeline.llm_parser = llm_parser
        return pipeline
    
    @pytest.mark.asyncio
    async def test_process_noise_message(self, pipeline, sample_message):
        """测试处理噪声消息"""
        sample_message['content'] = "接"
        
        result = await pipeline.process(sample_message)
        
        assert result.status == 'ignored'
        assert len(result.records) == 0
    
    @pytest.mark.asyncio
    async def test_process_service_message(self, pipeline, sample_message, temp_db):
        """测试处理服务消息"""
        # 设置 LLM 返回结果
        mock_return = [{
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
        # 直接修改 return_value
        pipeline.llm_parser.return_value = mock_return
        
        result = await pipeline.process(sample_message)
        
        assert result.status == 'parsed'
        assert len(result.records) == 1
        assert result.records[0]['type'] == 'service'
        assert result.records[0]['confidence'] == 0.95
        assert not result.records[0]['needs_confirmation']  # 置信度高，不需要确认
    
    @pytest.mark.asyncio
    async def test_process_low_confidence(self, pipeline, sample_message):
        """测试低置信度消息"""
        # 设置低置信度返回
        pipeline.llm_parser.return_value = [{
            "type": "service",
            "date": "2024-01-28",
            "customer_name": "段老师",
            "service_or_product": "头疗",
            "amount": 30,
            "confidence": 0.5  # 低置信度
        }]
        
        result = await pipeline.process(sample_message)
        
        assert result.status == 'parsed'
        assert len(result.records) == 1
        assert result.records[0]['needs_confirmation']  # 需要确认
    
    @pytest.mark.asyncio
    async def test_process_multiple_records(self, pipeline, sample_message):
        """测试处理多条记录"""
        pipeline.llm_parser.return_value = [
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
        
        sample_message['content'] = "2.3段老师490\n姚老师490理疗合计980"
        
        result = await pipeline.process(sample_message)
        
        assert result.status == 'parsed'
        assert len(result.records) == 2
    
    @pytest.mark.asyncio
    async def test_process_llm_failure(self, pipeline, sample_message):
        """测试 LLM 解析失败"""
        # 模拟 LLM 抛出异常
        pipeline.llm_parser.parse_message = AsyncMock(side_effect=Exception("LLM API Error"))
        
        result = await pipeline.process(sample_message)
        
        assert result.status == 'failed'
        assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_process_membership_message(self, pipeline, sample_message):
        """测试处理会员消息"""
        pipeline.llm_parser.return_value = [{
            "type": "membership",
            "date": "2024-01-28",
            "customer_name": "姚老师",
            "card_type": "理疗卡",
            "amount": 1000,
            "confidence": 0.95
        }]
        
        sample_message['content'] = "理疗开卡1000姚老师"
        
        result = await pipeline.process(sample_message)
        
        assert result.status == 'parsed'
        assert len(result.records) == 1
        assert result.records[0]['type'] == 'membership'
    
    @pytest.mark.asyncio
    async def test_process_product_sale(self, pipeline, sample_message):
        """测试处理商品销售"""
        pipeline.llm_parser.return_value = [{
            "type": "product_sale",
            "date": "2024-01-28",
            "customer_name": "段老师",
            "service_or_product": "泡脚液",
            "amount": 100,
            "quantity": 1,
            "confidence": 0.9
        }]
        
        sample_message['content'] = "泡脚液100段老师"
        
        result = await pipeline.process(sample_message)
        
        assert result.status == 'parsed'
        assert len(result.records) == 1
        assert result.records[0]['type'] == 'product_sale'
    
    @pytest.mark.asyncio
    async def test_process_invalid_record(self, pipeline, sample_message):
        """测试处理无效记录"""
        # LLM 返回无效格式
        pipeline.llm_parser.return_value = [
            {"type": "noise"},  # 噪声，应被忽略
            {"invalid": "record"},  # 缺少 type 字段
            {"type": "service", "date": "2024-01-28", "customer_name": "段老师", "amount": 30, "confidence": 0.9}  # 有效记录
        ]
        
        result = await pipeline.process(sample_message)
        
        # 应该只处理有效记录
        assert result.status == 'parsed'
        # 噪声和无效记录被过滤，只保留有效记录


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

