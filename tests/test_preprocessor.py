"""测试消息预处理器"""
import pytest
from datetime import datetime
from parsing.preprocessor import MessagePreProcessor


class TestMessagePreProcessor:
    """消息预处理器测试类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.preprocessor = MessagePreProcessor()
        self.timestamp = datetime(2024, 1, 28, 10, 0, 0)
    
    def test_is_noise(self):
        """测试噪声过滤"""
        # 单字闲聊
        assert self.preprocessor.is_noise("接") == True
        assert self.preprocessor.is_noise("好") == True
        assert self.preprocessor.is_noise("运") == True
        
        # 简短回复
        assert self.preprocessor.is_noise("好的") == True
        assert self.preprocessor.is_noise("收到") == True
        assert self.preprocessor.is_noise("谢谢") == True
        
        # 业务消息（不应被过滤）
        assert self.preprocessor.is_noise("1.28段老师头疗30") == False
        assert self.preprocessor.is_noise("理疗开卡1000") == False
        
        # 停车相关
        assert self.preprocessor.is_noise("停在门口") == True
        assert self.preprocessor.is_noise("掉头") == True
    
    def test_extract_date(self):
        """测试日期提取"""
        # 点分隔
        result = self.preprocessor.extract_date("1.28段老师头疗30", self.timestamp)
        assert result == datetime(2024, 1, 28).date()
        
        # 斜杠分隔
        result = self.preprocessor.extract_date("1/28段老师头疗", self.timestamp)
        assert result == datetime(2024, 1, 28).date()
        
        # 竖线分隔
        result = self.preprocessor.extract_date("2|1段老师头疗", self.timestamp)
        assert result == datetime(2024, 2, 1).date()
        
        # 中文格式
        result = self.preprocessor.extract_date("1月26日段老师头疗", self.timestamp)
        assert result == datetime(2024, 1, 26).date()
        
        result = self.preprocessor.extract_date("1月26号段老师头疗", self.timestamp)
        assert result == datetime(2024, 1, 26).date()
        
        # 无日期
        result = self.preprocessor.extract_date("段老师头疗30", self.timestamp)
        assert result is None
    
    def test_classify_intent(self):
        """测试意图分类"""
        # 服务类型
        assert self.preprocessor.classify_intent("1.28段老师头疗30") == "service"
        assert self.preprocessor.classify_intent("段老师理疗198") == "service"
        assert self.preprocessor.classify_intent("泡脚50") == "service"
        
        # 会员类型
        assert self.preprocessor.classify_intent("理疗开卡1000姚老师") == "membership"
        assert self.preprocessor.classify_intent("充值500") == "membership"
        
        # 商品类型
        assert self.preprocessor.classify_intent("泡脚液100") == "product"
        assert self.preprocessor.classify_intent("保健品200") == "product"
        
        # 修正类型
        assert self.preprocessor.classify_intent("26-27号错误，改25-26") == "correction"
        assert self.preprocessor.classify_intent("更正日期") == "correction"
        
        # 未知类型
        assert self.preprocessor.classify_intent("闲聊内容") == "unknown"
    
    def test_extract_amount(self):
        """测试金额提取"""
        # 标准格式
        assert self.preprocessor.extract_amount("头疗30") == 30.0
        assert self.preprocessor.extract_amount("理疗198") == 198.0
        
        # 金额在服务前
        assert self.preprocessor.extract_amount("30头疗") == 30.0
        
        # 带元
        assert self.preprocessor.extract_amount("头疗30元") == 30.0
        
        # 无金额
        assert self.preprocessor.extract_amount("头疗") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
