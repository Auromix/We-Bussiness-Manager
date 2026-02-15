"""测试 LLM 解析器（使用 Mock）"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from parsing.llm_parser import OpenAIParser, ClaudeParser, LLMParserWithFallback
import json


class MockOpenAIClient:
    """Mock OpenAI 客户端"""
    
    def __init__(self):
        self.chat = Mock()
        self.completions = Mock()
        self.chat.completions = self.completions
    
    def create_response(self, content):
        """创建模拟响应"""
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = content
        return response


class MockAnthropicClient:
    """Mock Anthropic 客户端"""
    
    def __init__(self):
        self.messages = Mock()
    
    def create_response(self, content):
        """创建模拟响应"""
        response = Mock()
        response.content = [Mock()]
        response.content[0].text = content
        return response


class TestOpenAIParser:
    """OpenAI 解析器测试"""
    
    @pytest.mark.asyncio
    async def test_parse_service_message(self):
        """测试解析服务消息"""
        mock_client = MockOpenAIClient()
        
        # 模拟响应
        response_data = {
            "records": [{
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
        }
        mock_client.completions.create.return_value = mock_client.create_response(
            json.dumps(response_data)
        )
        
        parser = OpenAIParser(api_key="test_key", model="gpt-4o-mini")
        parser.client = mock_client
        
        result = await parser.parse_message(
            sender="测试用户",
            timestamp="2024-01-28T10:00:00",
            content="1.28段老师头疗30"
        )
        
        assert len(result) == 1
        assert result[0]["type"] == "service"
        assert result[0]["customer_name"] == "段老师"
        assert result[0]["amount"] == 30
    
    @pytest.mark.asyncio
    async def test_parse_multiple_records(self):
        """测试解析多条记录"""
        mock_client = MockOpenAIClient()
        
        response_data = {
            "records": [
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
        }
        mock_client.completions.create.return_value = mock_client.create_response(
            json.dumps(response_data)
        )
        
        parser = OpenAIParser(api_key="test_key", model="gpt-4o-mini")
        parser.client = mock_client
        
        result = await parser.parse_message(
            sender="测试用户",
            timestamp="2024-02-03T10:00:00",
            content="2.3段老师490\n姚老师490理疗合计980"
        )
        
        assert len(result) == 2
        assert result[0]["customer_name"] == "段老师"
        assert result[1]["customer_name"] == "姚老师"
    
    @pytest.mark.asyncio
    async def test_parse_noise(self):
        """测试解析噪声消息"""
        mock_client = MockOpenAIClient()
        
        response_data = {"records": [{"type": "noise"}]}
        mock_client.completions.create.return_value = mock_client.create_response(
            json.dumps(response_data)
        )
        
        parser = OpenAIParser(api_key="test_key", model="gpt-4o-mini")
        parser.client = mock_client
        
        result = await parser.parse_message(
            sender="测试用户",
            timestamp="2024-01-28T10:00:00",
            content="接"
        )
        
        assert len(result) == 1
        assert result[0]["type"] == "noise"


class TestClaudeParser:
    """Claude 解析器测试"""
    
    @pytest.mark.asyncio
    async def test_parse_service_message(self):
        """测试解析服务消息"""
        mock_client = MockAnthropicClient()
        
        response_data = {
            "records": [{
                "type": "service",
                "date": "2024-01-28",
                "customer_name": "段老师",
                "service_or_product": "头疗",
                "amount": 30,
                "confidence": 0.95
            }]
        }
        mock_client.messages.create.return_value = mock_client.create_response(
            json.dumps(response_data)
        )
        
        parser = ClaudeParser(api_key="test_key", model="claude-sonnet-4-20250514")
        parser.client = mock_client
        
        result = await parser.parse_message(
            sender="测试用户",
            timestamp="2024-01-28T10:00:00",
            content="1.28段老师头疗30"
        )
        
        assert len(result) == 1
        assert result[0]["type"] == "service"


class TestLLMParserWithFallback:
    """带 Fallback 的解析器测试"""
    
    @pytest.mark.asyncio
    async def test_primary_success(self):
        """测试主解析器成功"""
        primary = Mock()
        primary.parse_message = AsyncMock(return_value=[{"type": "service"}])
        
        fallback = Mock()
        fallback.parse_message = AsyncMock()
        
        parser = LLMParserWithFallback(primary=primary, fallback=fallback)
        result = await parser.parse_message("test", "2024-01-28", "test content")
        
        assert result == [{"type": "service"}]
        primary.parse_message.assert_called_once()
        fallback.parse_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_primary_fail_fallback_success(self):
        """测试主解析器失败，fallback 成功"""
        primary = Mock()
        primary.parse_message = AsyncMock(side_effect=Exception("Primary failed"))
        
        fallback = Mock()
        fallback.parse_message = AsyncMock(return_value=[{"type": "service"}])
        
        parser = LLMParserWithFallback(primary=primary, fallback=fallback)
        result = await parser.parse_message("test", "2024-01-28", "test content")
        
        assert result == [{"type": "service"}]
        fallback.parse_message.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

